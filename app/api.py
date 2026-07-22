import os
from typing import Callable, List, Optional

from fastapi import Depends, FastAPI, Header, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from reports.tempo_reports import TempoReport
from reports.jira_reports import JiraReports
from datetime import datetime, timedelta

app = FastAPI(title="Jira Tempo Reports API")

# ---------------------------------------------------------------------------
# CORS — restreint aux origines autorisées (config via ALLOWED_ORIGINS).
# Par défaut : dev local. En production, définir ALLOWED_ORIGINS avec le
# domaine de l'app (ex. "https://mon-app.vercel.app").
# ---------------------------------------------------------------------------
ALLOWED_ORIGINS = [
    o.strip()
    for o in os.getenv(
        "ALLOWED_ORIGINS", "http://localhost:5173,http://localhost:3000"
    ).split(",")
    if o.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_methods=["GET"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Auth — clé API optionnelle. Si REPORTS_API_KEY est définie côté serveur,
# chaque requête doit fournir l'en-tête "X-API-Key" correspondant.
# ---------------------------------------------------------------------------
API_KEY = os.getenv("REPORTS_API_KEY")


def require_api_key(x_api_key: Optional[str] = Header(default=None)):
    if API_KEY and x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid or missing API key")


def f2(value):
    """Format a number to exactly 2 decimal places."""
    return f"{value:.2f}"


def _compute_billable_from_worklogs(
    worklogs: List[dict],
    fetch_historical: Callable[[str], List[dict]],
    start_date: str,
    tempo: TempoReport,
    jira: JiraReports,
) -> Optional[dict]:
    """Cœur du calcul billable/leaked par ticket, indépendant de la source
    des worklogs (compte Tempo ou utilisateur).

    - worklogs : worklogs de la période à analyser.
    - fetch_historical(day_before) : renvoie les worklogs *avant* la période,
      pour calculer la fuite (leaked) cumulée correctement.

    Retourne None si aucun worklog sur la période (le caller renvoie un
    rapport vide).
    """
    if not worklogs:
        return None

    # Agrège le temps loggé par ticket sur la période.
    time_by_issue = {}
    for log in worklogs:
        issue_id = str(log["issue"]["id"])
        if issue_id not in tempo._issue_key_cache:
            tempo._issue_key_cache[issue_id] = jira.get_issue_key_from_id(issue_id)
        issue_key = tempo._issue_key_cache[issue_id]
        if issue_key:
            if issue_key not in time_by_issue:
                time_by_issue[issue_key] = {"logged": 0}
            time_by_issue[issue_key]["logged"] += log["timeSpentSeconds"] / 3600

    # Worklogs historiques (avant la période) pour la fuite cumulée.
    start_dt = datetime.strptime(start_date, "%Y-%m-%d")
    day_before = (start_dt - timedelta(days=1)).strftime("%Y-%m-%d")
    historical_worklogs = fetch_historical(day_before)
    timespent_before = {}
    for log in historical_worklogs:
        issue_id = str(log["issue"]["id"])
        if issue_id not in tempo._issue_key_cache:
            tempo._issue_key_cache[issue_id] = jira.get_issue_key_from_id(issue_id)
        issue_key = tempo._issue_key_cache[issue_id]
        if issue_key:
            timespent_before[issue_key] = (
                timespent_before.get(issue_key, 0) + log["timeSpentSeconds"] / 3600
            )

    # Estimations Jira + fuite/billable par ticket.
    for issue_key in time_by_issue:
        try:
            response = jira._get_issue_fields(issue_key)
            estimated = (response.get("timeoriginalestimate") or 0) / 3600 if response else 0
        except Exception:
            estimated = 0
        logged = time_by_issue[issue_key]["logged"]
        before = timespent_before.get(issue_key, 0)
        leaked_avant = max(0, before - estimated)
        leaked_fin = max(0, before + logged - estimated)
        leaked = leaked_fin - leaked_avant
        time_by_issue[issue_key]["estimated"] = estimated
        time_by_issue[issue_key]["timespent_total"] = before + logged
        time_by_issue[issue_key]["leaked"] = leaked
        time_by_issue[issue_key]["billable"] = logged - leaked

    total_logged = sum(v["logged"] for v in time_by_issue.values())
    total_leaked = sum(v["leaked"] for v in time_by_issue.values())
    total_billable = total_logged - total_leaked
    billable_ratio = (total_billable / total_logged * 100) if total_logged > 0 else 0

    issues = [
        {
            "issue_key": k,
            "logged": f2(v["logged"]),
            "estimated": f2(v["estimated"]),
            "timespent_total": f2(v["timespent_total"]),
            "leaked": f2(v["leaked"]),
            "billable": f2(v["billable"]),
        }
        for k, v in time_by_issue.items()
    ]

    return {
        "total_logged": f2(total_logged),
        "total_billable": f2(total_billable),
        "total_non_billable": f2(total_leaked),
        "billable_ratio": f2(billable_ratio),
        "issues": issues,
    }


def _empty_report() -> dict:
    return {
        "total_logged": f2(0),
        "total_billable": f2(0),
        "total_non_billable": f2(0),
        "billable_ratio": f2(0),
        "issues": [],
    }


def compute_billable_hours(account_key: str, start_date: str, end_date: str) -> dict:
    """Rapport billable par **compte** Tempo (client/projet)."""
    tempo = TempoReport()
    jira = JiraReports()

    worklogs = tempo.fetch_worklogs_by_account(account_key, start_date, end_date)
    result = _compute_billable_from_worklogs(
        worklogs,
        lambda day_before: tempo.fetch_worklogs_by_account(account_key, "2015-01-01", day_before),
        start_date,
        tempo,
        jira,
    )
    base = {"account_key": account_key, "start_date": start_date, "end_date": end_date}
    return {**base, **(result or _empty_report())}


def compute_employee_billable_hours(account_id: str, start_date: str, end_date: str) -> dict:
    """Rapport billable par **employé** (Jira/Tempo accountId).

    Même calcul que par compte, mais les worklogs sont filtrés sur une seule
    personne via l'endpoint utilisateur de Tempo.
    """
    tempo = TempoReport()
    jira = JiraReports()

    worklogs = tempo.fetch_worklogs_by_user(account_id, start_date, end_date)
    result = _compute_billable_from_worklogs(
        worklogs,
        lambda day_before: tempo.fetch_worklogs_by_user(account_id, "2015-01-01", day_before),
        start_date,
        tempo,
        jira,
    )
    base = {"account_id": account_id, "start_date": start_date, "end_date": end_date}
    return {**base, **(result or _empty_report())}


def _validate_dates(start_date: str, end_date: str):
    try:
        datetime.strptime(start_date, "%Y-%m-%d")
        datetime.strptime(end_date, "%Y-%m-%d")
    except ValueError:
        raise HTTPException(status_code=400, detail="Dates must be in YYYY-MM-DD format")

    if start_date > end_date:
        raise HTTPException(status_code=400, detail="start_date must be before end_date")


@app.get("/api/billable-hours", dependencies=[Depends(require_api_key)])
def get_billable_hours(
    account_key: str = Query(..., description="Tempo account key"),
    start_date: str = Query(..., description="Start date (YYYY-MM-DD)"),
    end_date: str = Query(..., description="End date (YYYY-MM-DD)"),
):
    _validate_dates(start_date, end_date)
    return compute_billable_hours(account_key, start_date, end_date)


@app.get("/api/employee-billable-hours", dependencies=[Depends(require_api_key)])
def get_employee_billable_hours(
    account_id: str = Query(..., description="Jira/Tempo user accountId"),
    start_date: str = Query(..., description="Start date (YYYY-MM-DD)"),
    end_date: str = Query(..., description="End date (YYYY-MM-DD)"),
):
    _validate_dates(start_date, end_date)
    return compute_employee_billable_hours(account_id, start_date, end_date)
