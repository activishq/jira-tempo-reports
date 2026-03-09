import streamlit as st
import pandas as pd
from reports.jira_reports import JiraReports
from datetime import datetime, timedelta
from reports.tempo_reports import TempoReport
import logging
import sys

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

def get_default_dates():
    today = datetime.now().date()
    start = today - timedelta(days=today.weekday() + 1)
    end = start + timedelta(days=6)
    return start, end

def format_hours(hours):                                                                                       
      return f"{hours:.1f}h"

def tempo_account_page():
    st.title("Rapport par Compte Tempo")

    try:
        tempo = TempoReport()
        accounts = tempo.fetch_accounts()
        account_options = sorted(
            [f"{a['key']} ({a.get('status', 'OPEN')})" for a in accounts]
        )
        account_key_map = {
            f"{a['key']} ({a.get('status', 'OPEN')})": a['key'] for a in accounts
        }

        if not account_options:
            st.warning("Aucun compte Tempo trouvé.")
            return

        selected_option = st.selectbox("Sélectionnez un compte Tempo", account_options)

        default_start, default_end = get_default_dates()
        start_date = st.date_input("Date de début", value=default_start)
        end_date = st.date_input("Date de fin", value=default_end)

        if start_date > end_date:
            st.error("La date de fin doit être postérieure à la date de début.")
            return

        account_key = account_key_map[selected_option]
        worklogs = tempo.fetch_worklogs_by_account(
            account_key,
            start_date.strftime("%Y-%m-%d"),
            end_date.strftime("%Y-%m-%d")
        )

        if not worklogs:
            st.warning("Aucune donnée trouvée pour la période sélectionnée.")
            return

        # Calcul des métriques
        total_logged = sum(log['timeSpentSeconds'] for log in worklogs) / 3600
        total_billable = sum(log.get('billableSeconds', log['timeSpentSeconds']) for log in worklogs) / 3600
        total_non_billable = total_logged - total_billable
        billable_ratio = (total_billable / total_logged * 100) if total_logged > 0 else 0

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Heures enregistrées", format_hours(total_logged))
        col2.metric("Heures facturables", format_hours(total_billable))
        col3.metric("Heures non-facturables", format_hours(total_non_billable))
        col4.metric("Ratio de facturation", f"{billable_ratio:.1f}%")

        # Agrégation par issue
        jira = JiraReports()
        time_by_issue = {}
        for log in worklogs:
            issue_id = str(log['issue']['id'])
            if issue_id not in tempo._issue_key_cache:
                tempo._issue_key_cache[issue_id] = jira.get_issue_key_from_id(issue_id)
            issue_key = tempo._issue_key_cache[issue_id]
            if issue_key:
                if issue_key not in time_by_issue:
                    time_by_issue[issue_key] = {'logged': 0, 'billable': 0}
                time_by_issue[issue_key]['logged'] += log['timeSpentSeconds'] / 3600
                time_by_issue[issue_key]['billable'] += log.get('billableSeconds', log['timeSpentSeconds']) / 3600

        df = pd.DataFrame([
            {
                'Issue Key': k,
                'Temps enregistré': round(v['logged'], 2),
                'Temps facturable': round(v['billable'], 2),
                'Temps non-facturable': round(v['logged'] - v['billable'], 2)
            }
            for k, v in time_by_issue.items()
        ])

        if not df.empty:
            df = df.sort_values(by="Temps enregistré", ascending=False)
            base_url = "https://activis.atlassian.net/browse/"
            df['URL'] = base_url + df['Issue Key']

            st.subheader("Détails des Issues Jira")
            st.dataframe(
                df,
                column_config={
                    "Issue Key": "Issue",
                    "Temps enregistré": st.column_config.NumberColumn(format="%.1f h"),
                    "Temps facturable": st.column_config.NumberColumn(format="%.1f h"),
                    "Temps non-facturable": st.column_config.NumberColumn(format="%.1f h"),
                    "URL": st.column_config.LinkColumn("Lien Jira")
                },
                hide_index=True,
                use_container_width=True
            )

    except Exception as e:
        logger.error(f"Erreur: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        st.error(f"Une erreur s'est produite: {str(e)}")

if __name__ == "__main__":
    tempo_account_page()