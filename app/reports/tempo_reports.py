import requests
from constants import TEMPO_ACCESS_TOKEN
import pandas as pd
from typing import List, Dict
import logging
from .jira_reports import JiraReports

logger = logging.getLogger(__name__)
class TempoReport:
    # used by main
    def __init__(self):
        self.base_url = "https://api.tempo.io/4/worklogs"
        self.access_token = TEMPO_ACCESS_TOKEN
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {self.access_token}"
        })
        self._worklog_cache = {}
        self._issue_key_cache = {}

    def _get_cached_worklogs(self, start_date: str, end_date: str) -> List[Dict]:
        cache_key = f"{start_date}_{end_date}"
        if cache_key not in self._worklog_cache:
            self._worklog_cache[cache_key] = self._fetch_all_worklogs(start_date, end_date)
        return self._worklog_cache[cache_key]

    def _fetch_all_worklogs(self, start_date: str, end_date: str) -> List[Dict]:
        all_worklogs = []
        page_index = 0
        page_size = 50
        max_attempts = 20

        while page_index < max_attempts:
            params = {
                'from': start_date,
                'to': end_date,
                'limit': page_size,
                'offset': page_index * page_size
            }

            response = self.session.get(self.base_url, params=params)
            response.raise_for_status()
            data = response.json()
            worklogs = data.get('results', [])

            if not worklogs:
                break

            all_worklogs.extend(worklogs)

            if not data.get('metadata', {}).get('next'):
                break

            page_index += 1

        return all_worklogs

    def _get_issue_keys_batch(self, issue_ids: List[str], jira) -> dict:
        """Récupère les clés de tickets en batch"""
        uncached_ids = [id for id in issue_ids if id not in self.issue_key_cache]
        for issue_id in uncached_ids:
            key = jira.get_issue_key_from_id(str(issue_id))
            if key:
                self.issue_key_cache[issue_id] = key
        return self.issue_key_cache

    def get_worklogs(self, start_date: str, end_date: str, user_name: str = None) -> List[Dict]:
        all_worklogs = []
        page_index = 0
        page_size = 50
        max_results = 1000  # Protection contre les boucles infinies

        while page_index * page_size < max_results:
            params = {
                'from': start_date,
                'to': end_date,
                'limit': page_size,
                'offset': page_index * page_size
            }

            if user_name:
                params['workerId'] = user_name

            try:
                response = self.session.get(self.base_url, params=params)
                response.raise_for_status()
                data = response.json()
                worklogs = data.get('results', [])

                if not worklogs:  # Si pas de résultats, on sort
                    break

                all_worklogs.extend(worklogs)

                # Vérifier s'il y a une page suivante
                if not data.get('metadata', {}).get('next'):
                    break

                page_index += 1

            except Exception as e:
                print(f"Error fetching worklogs: {str(e)}")
                break

        print(f"Total worklogs retrieved: {len(all_worklogs)}")
        return all_worklogs

    def get_logged_time(self, start_date: str, end_date: str, user_name: str) -> pd.DataFrame:
        jira = JiraReports()
        user_account_id = jira.get_user_account_id(user_name)

        if not user_account_id:
            return pd.DataFrame()

        worklogs = self._get_cached_worklogs(start_date, end_date)
        user_worklogs = [log for log in worklogs if log['author']['accountId'] == user_account_id]

        time_by_issue = {}
        for log in user_worklogs:
            issue_id = str(log['issue']['id'])
            if issue_id not in self._issue_key_cache:
                self._issue_key_cache[issue_id] = jira.get_issue_key_from_id(issue_id)

            issue_key = self._issue_key_cache[issue_id]
            if issue_key:
                time_spent = round(log['timeSpentSeconds'] / 3600, 2)
                time_by_issue[issue_key] = time_by_issue.get(issue_key, 0) + time_spent

        return pd.DataFrame([
            {'issue_key': k, 'logged_time': v, 'user': user_name}
            for k, v in time_by_issue.items()
        ])

    def get_department_logged_time(self, start_date: str, end_date: str, department_users: List[str]) -> float:
            """
            Calculate total logged time for the department for a given date range.
            """
            department_worklogs = []

            for user_name in department_users:
                user_worklogs = self.get_logged_time(start_date, end_date, user_name)
                department_worklogs.append(user_worklogs)

            all_department_worklogs = pd.concat(department_worklogs, ignore_index=True)
            department_summary = all_department_worklogs.groupby(['issue_key', 'user'])['logged_time'].sum().reset_index()
            logged_time_total = department_summary['logged_time'].sum()

            return logged_time_total
