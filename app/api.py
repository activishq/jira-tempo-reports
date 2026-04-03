from fastapi import FastAPI, Query, HTTPException
from fastapi.responses import JSONResponse
from app.reports.tempo_reports import TempoReport
from app.reports.jira_reports import JiraReports
from datetime import datetime, timedelta

app = FastAPI(title="Jira Tempo Reports API")


def f2(value):
    """Format a number to exactly 2 decimal places."""
    return f"{value:.2f}"


def compute_billable_hours(account_key: str, start_date: str, end_date: str) -> dict:
    tempo = TempoReport()
    jira = JiraReports()

    worklogs = tempo.fetch_worklogs_by_account(account_key, start_date, end_date)
    if not worklogs:
        return {
            "account_key": account_key,
            "start_date": start_date,
            "end_date": end_date,
            "total_logged": f2(0),
            "total_billable": f2(0),
            "total_non_billable": f2(0),
            "billable_ratio": f2(0),
            "issues": [],
        }

    # Aggregate logged time per issue for the period
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

    # Fetch historical worklogs before the period
    start_dt = datetime.strptime(start_date, "%Y-%m-%d")
    day_before = (start_dt - timedelta(days=1)).strftime("%Y-%m-%d")
    historical_worklogs = tempo.fetch_worklogs_by_account(account_key, "2015-01-01", day_before)
    timespent_before = {}
    for log in historical_worklogs:
        issue_id = str(log["issue"]["id"])
        if issue_id not in tempo._issue_key_cache:
            tempo._issue_key_cache[issue_id] = jira.get_issue_key_from_id(issue_id)
        issue_key = tempo._issue_key_cache[issue_id]
        if issue_key:
            timespent_before[issue_key] = timespent_before.get(issue_key, 0) + log["timeSpentSeconds"] / 3600

    # Fetch Jira estimates and compute leaked/billable per issue
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
        "account_key": account_key,
        "start_date": start_date,
        "end_date": end_date,
        "total_logged": f2(total_logged),
        "total_billable": f2(total_billable),
        "total_non_billable": f2(total_leaked),
        "billable_ratio": f2(billable_ratio),
        "issues": issues,
    }


@app.get("/api/billable-hours")
def get_billable_hours(
    account_key: str = Query(..., description="Tempo account key"),
    start_date: str = Query(..., description="Start date (YYYY-MM-DD)"),
    end_date: str = Query(..., description="End date (YYYY-MM-DD)"),
):
    try:
        datetime.strptime(start_date, "%Y-%m-%d")
        datetime.strptime(end_date, "%Y-%m-%d")
    except ValueError:
        raise HTTPException(status_code=400, detail="Dates must be in YYYY-MM-DD format")

    if start_date > end_date:
        raise HTTPException(status_code=400, detail="start_date must be before end_date")

    return compute_billable_hours(account_key, start_date, end_date)
