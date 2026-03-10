import requests
import json
from requests.auth import HTTPBasicAuth
import pandas as pd
from typing import List
import os
from constants import (
    JIRA_USERNAME,
    JIRA_API_KEY,
)
from .helpers import JiraApi, JsonFileBackup


env = os.getenv('ENVIRONMENT')
if env not in ['test', 'development', 'production']:
    raise ValueError("ENVIRONMENT must be one of 'test', 'development', 'production'")


class JiraReports:
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

    def get_estimated_time(self, start_date: str, end_date: str, user_name: str) -> pd.DataFrame:
        """
        Retrieve estimated time data from Jira for a specific user and date range.
        """
        params = {
            'jql': f"assignee in (\"{user_name}\") AND worklogDate >= '{start_date}' AND worklogDate <= '{end_date}'",
            'fields': 'timeoriginalestimate,summary,timespent'
        }

        try:
            response = JiraApi.search(params)
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

    def get_user_account_id(self, display_name: str) -> str:
        """
        Récupère l'accountId d'un utilisateur à partir de son nom d'affichage.
        """
        backup = JsonFileBackup(file_name='user_account_id')
        previous_data = backup.read()
        user_account_id = previous_data.get(display_name, None)

        if user_account_id:
            return user_account_id
        
        params = {
            'query': display_name
        }
        try:
            response = JiraApi.user_search(params)
            response.raise_for_status()
            users = response.json()

            for user in users:
                previous_data[user.get('displayName')] = user.get('accountId')
            backup.dump(previous_data)

            return previous_data.get(display_name, None)
        except requests.RequestException as e:
            print(f"Erreur lors de la récupération de l'accountId: {e}")
            return None

    def get_issue_key_from_id(self, issue_id: str) -> str:
        """
        Récupère la clé du ticket à partir de son ID.
        """
        try:
            response = JiraApi.get_issue(issue_id)
            response.raise_for_status()
            issue_data = response.json()
            return issue_data.get('key')
        except requests.RequestException as e:
            print(f"Erreur lors de la récupération de la clé du ticket: {e}")
            return None

    def _get_issue_fields(self, issue_key: str) -> dict:
        """
        Récupère les champs d'un ticket à partir de sa clé.
        """
        try:
            response = JiraApi.get_issue(issue_key)
            response.raise_for_status()
            return response.json().get('fields', {})
        except requests.RequestException as e:
            print(f"Erreur lors de la récupération des champs du ticket {issue_key}: {e}")
            return None
