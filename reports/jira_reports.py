
import requests
from requests.auth import HTTPBasicAuth
from decouple import config
import pandas as pd
from typing import List, Dict
from dotenv import load_dotenv
import os

load_dotenv()


JIRA_URL = "https://activis.atlassian.net"

class JiraReports:
    def __init__(self):
        self.auth = HTTPBasicAuth(config('JIRA_USERNAME'), config('JIRA_API_KEY'))

    def get_current_users(self) -> List[str]:
        """Return a list of current users."""
        return ['Sonia Marquette', 'Claire Conrardy', 'Benoit Leboucher',
                'Eric Ferole', 'Laurence Cauchon', 'Julien Le Mée',
                'David Chabot', 'Thierry Tanguay']

    def get_department_availability(self) -> float:
        """Calculate and return the total department availability."""
        user_availabilities = {
            'Sonia Marquette': 30,
            'Claire Conrardy': 14,
            'Benoit Leboucher': 37.5,
            'Eric Ferole': 37.5,
            'Laurence Cauchon': 37.5,
            'Julien Le Mée': 37.5
        }
        return sum(user_availabilities.values())

    def get_estimated_time(self, start_date: str, end_date: str, user_name: str) -> pd.DataFrame:
        """
        Retrieve estimated time data from Jira for a specific user and date range.
        """
        url = f"{JIRA_URL}/rest/api/3/search"
        jql = f"assignee in (\"{user_name}\") AND worklogDate >= '{start_date}' AND worklogDate <= '{end_date}'"

        params = {
            'jql': jql,
            'fields': 'timeoriginalestimate,summary,timespent'
        }

        try:
            response = requests.get(url, params=params, auth=self.auth)
            response.raise_for_status()
            issues = response.json()['issues']

            data = [
                {
                    'user': user_name,
                    'issue_key': issue['key'],
                    'timespent': (issue['fields']['timespent'] or 0) / 3600,
                    'estimated_time': (issue['fields']['timeoriginalestimate'] or 0) / 3600
                }
                for issue in issues
            ]

            return pd.DataFrame(data, columns=['user', 'issue_key', 'timespent', 'estimated_time'])

        except requests.RequestException as e:
            print(f"Error fetching data from Jira: {e}")
            return pd.DataFrame()

    def get_department_total_time_spent(self, start_date: str, end_date: str) -> float:
        """
        Calculate the total time spent by the department for a given date range.
        """
        department_users = self.get_current_users()
        department_estimates = pd.DataFrame()

        for user_name in department_users:
            user_estimated_time = self.get_estimated_time(start_date, end_date, user_name)
            department_estimates = pd.concat([department_estimates, user_estimated_time], ignore_index=True)

        return department_estimates['timespent'].sum()

    def get_department_estimated_time(self, start_date: str, end_date: str) -> float:
        """
        Calculate the total estimated time for the department for a given date range.
        """
        department_users = self.get_current_users()
        department_estimates = pd.DataFrame()

        for user_name in department_users:
            user_estimated_time = self.get_estimated_time(start_date, end_date, user_name)
            department_estimates = pd.concat([department_estimates, user_estimated_time], ignore_index=True)

        return department_estimates['estimated_time'].sum()
