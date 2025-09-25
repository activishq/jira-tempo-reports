import requests
from requests.auth import HTTPBasicAuth
import pandas as pd
from typing import List
import os
from constants import (
    JIRA_USERNAME,
    JIRA_API_KEY,
)


env = os.getenv('ENVIRONMENT')
if env not in ['test', 'development', 'production']:
    raise ValueError("ENVIRONMENT must be one of 'test', 'development', 'production'")


JIRA_URL = "https://activis.atlassian.net"
class JiraReports:
    # called by main
    def __init__(self):
        self.auth = HTTPBasicAuth(JIRA_USERNAME, JIRA_API_KEY)

    def get_current_users(self) -> List[str]:
        """Return a list of current users."""
        return ['Sonia Marquette', 'Claire Conrardy', 'Benoit Leboucher',
                'Eric Ferole', 'Laurence Cauchon', 'Julien Le Mée',
                'David Chabot', 'Thierry Tanguay', 'Jeff Trempe', 'David Cazal']

    def get_department_availability(self) -> float:
        """Calculate and return the total department availability."""
        user_availabilities = {
            'Sonia Marquette': 30,
            'Claire Conrardy': 14,
            'Benoit Leboucher': 37.5,
            'Eric Ferole': 37.5,
            'Laurence Cauchon': 37.5,
            'Julien Le Mée': 37.5,
            'David Cazal': 37.5
        }
        return sum(user_availabilities.values())

    def get_users_mapping(self) -> dict:
        """Returns a dictionary mapping displayName to accountId for current users."""
        return {
            'Sonia Marquette': '557058:32b276cf-1a9f-4fd5-9dc9-067ddca36ed4',
            'Claire Conrardy': '557058:74a3c4c3-38aa-4201-b5d9-478462777444',
            'Benoit Leboucher': '557058:e1f0069a-5123-4cfa-98c2-de32588aed26',
            'Eric Ferole': '557058:f29b0c56-f018-47c6-af4f-f6f44ba03bb4',
            'Laurence Cauchon': '557058:eba24c3e-0273-4c27-bf2b-661215620795',
            'Julien Le Mée': '557058:eddec97e-7457-47dc-91c7-06907ee8ef9f',
            'David Chabot': '557058:x29b0c56-x018-47c6-af4f-f6f44ba03bb4',
            'Thierry Tanguay': '557058:y29b0c56-y018-47c6-af4f-f6f44ba03bb4',
            'Jeff Trempe': '712020:dc3a2115-d8ee-4d15-a38b-c1978136c148',
            'David Cazal': '712020:6d7bad8f-2de8-4ca0-bd29-5d3ba83dec44'
        }

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

    def get_user_account_id(self, display_name: str) -> str:
        """
        Récupère l'accountId d'un utilisateur à partir de son nom d'affichage.
        """
        url = f"{JIRA_URL}/rest/api/3/user/search"
        params = {
            'query': display_name
        }
        try:
            response = requests.get(url, params=params, auth=self.auth)
            response.raise_for_status()
            users = response.json()

            # Chercher une correspondance exacte
            for user in users:
                if user.get('displayName') == display_name:
                    return user.get('accountId')

            return None
        except requests.RequestException as e:
            print(f"Erreur lors de la récupération de l'accountId: {e}")
            return None

    def get_issue_key_from_id(self, issue_id: str) -> str:
        """
        Récupère la clé du ticket à partir de son ID.
        """
        url = f"{JIRA_URL}/rest/api/3/issue/{issue_id}"
        try:
            response = requests.get(url, auth=self.auth)
            response.raise_for_status()
            issue_data = response.json()
            return issue_data.get('key')
        except requests.RequestException as e:
            print(f"Erreur lors de la récupération de la clé du ticket: {e}")
            return None
