import requests
from decouple import config
import pandas as pd
from typing import List, Dict, Optional

class TempoReport:
    def __init__(self):
        self.base_url = "https://api.tempo.io/core/3/worklogs"
        self.access_token = config('TEMPO_ACCESS_TOKEN')
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {self.access_token}"
        })

    def get_worklogs(self, start_date: str, end_date: str, user_name: Optional[str] = None) -> List[Dict]:
        """
        Retrieve worklogs from Tempo for a given date range and user.
        """
        all_worklogs = []
        page_index = 0
        page_size = 50

        while True:
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
                all_worklogs.extend(worklogs)

                if 'metadata' in data and 'next' in data['metadata']:
                    page_index += 1
                else:
                    break

            except requests.RequestException as e:
                print(f"Error fetching data from Tempo: {e}")
                break

        return all_worklogs

    def get_logged_time(self, start_date: str, end_date: str, user_name: str) -> pd.DataFrame:
        """
        Calculate logged time for a specific user and date range.
        """
        worklogs = self.get_worklogs(start_date, end_date)

        time_by_issue_list = []

        for log in worklogs:
            try:
                if log['author']['displayName'] == user_name:
                    issue_key = log['issue']['key']
                    time_spent = round(log['timeSpentSeconds'] / 3600, 2)

                    entry = next((item for item in time_by_issue_list if item['issue_key'] == issue_key), None)
                    if entry:
                        entry['logged_time'] += time_spent
                    else:
                        time_by_issue_list.append({
                            'issue_key': issue_key,
                            'logged_time': time_spent,
                            'user': user_name
                        })
            except Exception as e:
                continue

        return pd.DataFrame(time_by_issue_list)

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
