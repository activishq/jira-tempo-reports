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

    def fetch_closed_issues(
        self, account_id: str, start_date: str, end_exclusive: str
    ) -> List[dict]:
        """Récupère les tâches **fermées** (statusCategory = Done) assignées à
        un employé et **entrées dans la catégorie « Terminé »** dans
        [start_date, end_exclusive[.

        Le workflow Jira d'Activis passe les tâches en « Terminé »/« Résolu »
        sans remplir resolution/resolutiondate. On bucketise donc sur
        `statusCategoryChangedDate` (date d'entrée en catégorie Done).

        Retourne une liste de dicts bruts : {issue_key, estimated (h),
        timespent (h), closed_date (str ISO ou None), status (nom ou None)}.
        La pagination du nouvel endpoint /search/jql (token-based) est suivie
        jusqu'au bout.
        """
        jql = (
            f'assignee = "{account_id}" '
            f'AND statusCategory = Done '
            f'AND statusCategoryChangedDate >= "{start_date}" '
            f'AND statusCategoryChangedDate < "{end_exclusive}"'
        )

        issues: List[dict] = []
        next_token = None
        while True:
            params = {
                'jql': jql,
                # NB : id de champ = statuscategorychangedate (un seul « d »),
                # alors que la clause JQL s'écrit statusCategoryChangedDate.
                'fields': 'timeoriginalestimate,timespent,statuscategorychangedate,status,summary',
                'maxResults': 100,
            }
            if next_token:
                params['nextPageToken'] = next_token

            response = JiraApi.search(params)
            response.raise_for_status()
            data = response.json()

            for issue in data.get('issues', []):
                fields = issue.get('fields', {}) or {}
                status = fields.get('status') or {}
                issues.append(
                    {
                        'issue_key': issue.get('key'),
                        'estimated': (fields.get('timeoriginalestimate') or 0) / 3600,
                        'timespent': (fields.get('timespent') or 0) / 3600,
                        'closed_date': fields.get('statuscategorychangedate'),
                        'status': status.get('name') if isinstance(status, dict) else None,
                    }
                )

            next_token = data.get('nextPageToken')
            if data.get('isLast', True) or not next_token:
                break

        return issues

    def probe_jql(self, jql: str, fields: str = "status,resolution,resolutiondate", max_results: int = 100) -> dict:
        """DEBUG : exécute un JQL brut (première page) et renvoie le nombre de
        billets + un échantillon. Sert à diagnostiquer un filtre trop strict."""
        response = JiraApi.search({'jql': jql, 'fields': fields, 'maxResults': max_results})
        status_code = response.status_code
        try:
            data = response.json()
        except Exception:
            data = {}
        issues = data.get('issues', []) if isinstance(data, dict) else []
        sample = []
        for issue in issues[:8]:
            f = issue.get('fields', {}) or {}
            st = (f.get('status') or {})
            sample.append({
                'key': issue.get('key'),
                'status': st.get('name') if isinstance(st, dict) else None,
                'closed_date': f.get('statuscategorychangeddate'),
                'est_h': round((f.get('timeoriginalestimate') or 0) / 3600, 2),
                'reel_h': round((f.get('timespent') or 0) / 3600, 2),
            })
        return {
            'jql': jql,
            'http_status': status_code,
            'count_first_page': len(issues),
            'is_last': data.get('isLast', True) if isinstance(data, dict) else True,
            'error': None if status_code == 200 else str(data)[:300],
            'sample': sample,
        }

    def probe_all_fields(self, jql: str, limit: int = 3) -> list:
        """DEBUG : renvoie, pour les premiers billets, toutes les paires
        champ→valeur dont la clé évoque une date/un statut ou dont la valeur
        ressemble à une date ISO. Sert à trouver le vrai id du champ
        « statusCategoryChangedDate »."""
        response = JiraApi.search({'jql': jql, 'fields': '*all', 'maxResults': limit})
        data = response.json() if response.status_code == 200 else {}
        out = []
        for issue in (data.get('issues', []) if isinstance(data, dict) else [])[:limit]:
            f = issue.get('fields', {}) or {}
            hits = {}
            for k, v in f.items():
                key_match = any(t in k.lower() for t in ('date', 'change', 'status', 'resol', 'created', 'updated'))
                val_match = isinstance(v, str) and len(v) >= 10 and v[4] == '-' and v[7] == '-'
                if key_match or val_match:
                    hits[k] = v if not isinstance(v, dict) else v.get('name', v)
            out.append({'key': issue.get('key'), 'fields': hits})
        return out
