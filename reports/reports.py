# Obsolete code, kept for reference
# This code is not used in the project

import requests
from requests.auth import HTTPBasicAuth
from decouple import config
import pandas as pd
import unittest

class JiraReports:
    def __init__(self):
        self.jira_url = "https://activis.atlassian.net"
        self.auth = HTTPBasicAuth(config('JIRA_USERNAME'), config('JIRA_API_KEY'))

    def get_current_users(self):
        users = ['Sonia Marquette', 'Claire Conrardy', 'Benoit Leboucher', 'Eric Ferole', 'Laurence Cauchon',
                 'Julien Le Mée', 'David Chabot', 'Thierry Tanguay', 'Jeff Trempe', 'Nancy L. Rodriguez',
                 'Simon Bouchard', 'Evan Buckiewicz',
                 ]
        return users

    def get_users_mapping(self) -> dict:
        """Returns a dictionary mapping displayName to accountId for current users."""
        return {
            'Sonia Marquette': '557058:32b276cf-1a9f-4fd5-9dc9-067ddca36ed4',
            'Claire Conrardy': '557058:74a3c4c3-38aa-4201-b5d9-478462777444',
            'Benoit Leboucher': '557058:e1f0069a-5123-4cfa-98c2-de32588aed26',
            'Eric Ferole': '61957639b43d5b006aa771c8',
            'Laurence Cauchon': '557058:eba24c3e-0273-4c27-bf2b-661215620795',
            'Julien Le Mée': '557058:eddec97e-7457-47dc-91c7-06907ee8ef9f',
            'David Chabot': '557058:x29b0c56-x018-47c6-af4f-f6f44ba03bb4',
            'Thierry Tanguay': '557058:y29b0c56-y018-47c6-af4f-f6f44ba03bb4',
            'Simon Bouchard': '712020:32ea8dc5-c696-4365-be1b-2ac476c34039',
            'Nancy L. Rodriguez': '712020:b0bfc929-6691-4ce9-8152-32cb07b51b27',
            'Jeff Trempe': '712020:dc3a2115-d8ee-4d15-a38b-c1978136c148',
            'Evan Buckiewicz': '712020:d951992c-717d-4485-bc35-a459cef088db'
        }

    def get_department_availability(self):
        user_availabilities = {
            'Sonia Marquette': 30,
            'Claire Conrardy': 14,
            'Benoit Leboucher': 37.5,
            'Eric Ferole': 37.5,
            'Laurence Cauchon': 37.5,
            'Julien Le Mée': 37.5,
            'David Chabot': 37.5,
            'Thierry Tanguay': 37.5,
            'Nancy L. Rodriguez': 37.5,
            'Simon Bouchard': 37.5,
            'Jeff Trempe': 37.5
        }
        total_availabilities = sum(user_availabilities.values())
        return total_availabilities

    def get_estimated_time(self, start_date, end_date, user_name):
        url = f"{self.jira_url}/rest/api/3/search"
        # jql = f"assignee in (\"{display_name}\") AND updated >= '{start_date}' AND updated <= '{end_date}'"
        jql = f"assignee in (\"{user_name}\") AND worklogDate >= '{start_date}' AND worklogDate <= '{end_date}'"

        params = {
            'jql': jql,
            'fields': 'timeoriginalestimate,summary,timespent'
        }
        response = requests.get(url, params=params, auth=self.auth)
        if response.status_code == 200:
            issues = response.json()['issues']
            # print(issues)
            data = [
                {
                    'user': user_name,
                    'issue_key': issue['key'],
                    'timespent': (issue['fields']['timespent'] or 0) / 3600,
                    'estimated_time': (issue['fields']['timeoriginalestimate'] or 0) / 3600
                }
                for issue in issues
            ]
            # Créer un DataFrame à partir de la liste des données
            df = pd.DataFrame(data, columns=['user', 'issue_key', 'timespent', 'estimated_time'])
            return df
        else:
            response.raise_for_status()

    def get_department_total_time_spent(self, start_date, end_date):
        jira_reports = self
        department_users = jira_reports.get_current_users()

        # Initialiser un DataFrame vide pour les estimations de tout le département
        department_estimates = pd.DataFrame()

        for user_name in department_users:
            user_estimated_time = self.get_estimated_time(start_date, end_date, user_name)

            # Concaténer les DataFrames au lieu d'ajouter des dictionnaires à une liste
            department_estimates = pd.concat([department_estimates, user_estimated_time], ignore_index=True)

        estimated_time_total = department_estimates['timespent'].sum()

        return estimated_time_total

    def get_department_estimated_time(self, start_date, end_date):
        jira_reports = self
        department_users = jira_reports.get_current_users()

        # Initialiser un DataFrame vide pour les estimations de tout le département
        department_estimates = pd.DataFrame()

        for user_name in department_users:
            user_estimated_time = self.get_estimated_time(start_date, end_date, user_name)

            # Concaténer les DataFrames au lieu d'ajouter des dictionnaires à une liste
            department_estimates = pd.concat([department_estimates, user_estimated_time], ignore_index=True)

        estimated_time_total = department_estimates['estimated_time'].sum()

        return estimated_time_total


class TempoReport:
    def __init__(self):
        self.base_url = f"https://api.tempo.io/4/worklogs"
        self.access_token = config('TEMPO_ACCESS_TOKEN')
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {self.access_token}"
        })
        print("1ere étape",self.session.headers)

    def get_worklogs(self, start_date, end_date, user_name=None):
        url = self.base_url
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
                response = self.session.get(url, params=params)
                response.raise_for_status()
            except requests.exceptions.HTTPError as e:
                print(f"Erreur HTTP : {e}")
                print(f"Statut : {response.status_code}")
                print(f"Réponse : {response.text}")
                break  # Sortir de la boucle en cas d'erreur

            data = response.json()
            worklogs = data.get('results', [])
            all_worklogs.extend(worklogs)

            if 'metadata' in data and 'next' in data['metadata']:
                page_index += 1
            else:
                break

        return all_worklogs

    def get_logged_time(self, start_date, end_date, user_name):
        worklogs = self.get_worklogs(start_date, end_date)
        time_by_issue_list = []

        for log in worklogs:
            if log['author']['displayName'] == user_name:
                issue_key = log['issue']['key']

                entry = next((item for item in time_by_issue_list if item['issue_key'] == issue_key), None)
                if entry:
                    entry['logged_time'] += round(log['timeSpentSeconds'] / 3600, 2)
                else:
                    time_by_issue_list.append({
                        'issue_key': issue_key,
                        'logged_time': round(log['timeSpentSeconds'] / 3600, 2),
                        'user': user_name
                    })

        df = pd.DataFrame(time_by_issue_list)
        return df

    def get_department_logged_time(self, start_date, end_date):
        department_worklogs = []
        jira_reports = JiraReports()
        department_users = jira_reports.get_current_users()

        for user_name in department_users:
            user_worklogs = self.get_logged_time(start_date, end_date, user_name)
            department_worklogs.append(user_worklogs)

        all_department_worklogs = pd.concat(department_worklogs, ignore_index=True)

        department_summary = all_department_worklogs.groupby(['issue_key', 'user'])['logged_time'].sum().reset_index()
        logged_time_total = department_summary['logged_time'].sum()

        return logged_time_total

class JiraTempoReport:
    def __init__(self):
        self.jira_report = JiraReports()
        self.tempo_report = TempoReport()

    def get_merged_report(self, start_date, end_date, user_id, output_csv=None):
        """
        Cette fonction retourne un DataFrame contenant les données de Jira et Tempo pour un utilisateur donné
        pour une période donnée. Les colonnes du DataFrame sont les suivantes: 'Issue Key', 'Estimated Time',
        'Total Time Spent', 'Period's Logged Time', 'Period's Leaked Time'
        :param start_date: date de début de la période au format YYYY-MM-DD
        :param end_date: date de fin de la période au format YYYY-MM-DD
        :param user_id: nom de l'utilisateur ex : 'Sonia Marquette'
        """

        df_jira_report = self.jira_report.get_estimated_time(start_date, end_date, user_id)
        df_tempo_report = self.tempo_report.get_logged_time(start_date, end_date, user_id)

        print(f"Utilisateur : {user_id}")
        print("df_jira_report:")
        print(df_jira_report.head())

        print("df_tempo_report:")
        print(df_tempo_report.head())

        if df_jira_report.empty or df_tempo_report.empty:
            print("Un des DataFrames est vide pour cet utilisateur. Retour d'un DataFrame vide.")
            return pd.DataFrame(columns=['Issue Key', 'Total Time Spent', 'Estimated Time', 'Period\'s Logged Time', 'Period\'s Leaked Time', 'Total Leaked Time'])

        df_merged = pd.merge(df_jira_report, df_tempo_report, on='issue_key', how='outer').drop(columns=['user_x', 'user_y'])

        print("Colonnes après la fusion :", df_merged.columns)

        df_merged['logged_time'] = df_merged['logged_time'].fillna(0) if 'logged_time' in df_merged.columns else 0
        df_merged['timespent'] = df_merged['timespent'].fillna(0) if 'timespent' in df_merged.columns else 0
        df_merged['estimated_time'] = df_merged['estimated_time'].fillna(0) if 'estimated_time' in df_merged.columns else 0

        print("df_merged après gestion des NaN et des colonnes manquantes:")
        print(df_merged.head())

        def calculate_period_leak_time(row):
            w, y, z = row['timespent'], row['logged_time'], row['estimated_time']

            if z == 0:
                x = y
            # elif w > z and y >= z:
            #     x = w - y
            elif w > z:
                x = w - z
            elif z < w and y < z and y < abs(w - z):
                x = y
            else:
                x = w - z

            x = min(x, y)
            x = max(x, 0)

            return x

        df_merged['Period\'s Leaked Time'] = df_merged.apply(calculate_period_leak_time, axis=1)

        df_merged['total_leaked_time'] = round(df_merged.apply(
            lambda row: abs(row['estimated_time'] - row['timespent']) if row['timespent'] > row['estimated_time'] else 0, axis=1), 2)

        df_merged = df_merged.rename(columns={
            'estimated_time': 'Estimated Time',
            'issue_key': 'Issue Key',
            'timespent': 'Total Time Spent',
            'logged_time': 'Period\'s Logged Time',
            'total_leaked_time': 'Total Leaked Time'
        })

        if output_csv:
            df_merged.to_csv(output_csv, index=False)
            print(f"Le fichier CSV a été créé avec succès à l'emplacement : {output_csv}")

        return df_merged

    def get_logged_time(self, start_date, end_date, user_id):
        df_merged = self.get_merged_report(start_date, end_date, user_id)

        logged_time = df_merged['Period\'s Logged Time'].sum()

        return logged_time

    def get_leaked_time(self, start_date, end_date, user_id):
        df_merged = self.get_merged_report(start_date, end_date, user_id)

        if df_merged.empty:
            return 0

        soutien = df_merged[df_merged['Issue Key'].str.contains('SOUTIEN')]['Period\'s Leaked Time'].sum()

        print("temps de soutient:", soutien)

        leaked_time = round(df_merged['Period\'s Leaked Time'].sum(), 2)

        total_leaked_time = leaked_time - soutien

        return total_leaked_time

    def get_billable_time(self, start_date, end_date, user_id):
        logged_time_sum = self.get_logged_time(start_date, end_date, user_id)
        leaked_time_sum = self.get_leaked_time(start_date, end_date, user_id)
        billed_hours = abs(logged_time_sum - leaked_time_sum)

        return billed_hours

    def get_billable_ratio(self, start_date, end_date, user_id):
        billable_hours = self.get_billable_time(start_date, end_date, user_id)
        logged_time = self.get_logged_time(start_date, end_date, user_id)

        if logged_time == 0:
            print(f"Attention : logged_time est 0 pour l'utilisateur {user_id}. Impossible de calculer le ratio.")
            return 0  # Ou une autre valeur par défaut pour indiquer qu'il n'y a pas de données disponibles

        billable_ratio = round(billable_hours / logged_time, 3) * 100

        return billable_ratio

    def get_department_leaked_time(self, start_date, end_date):
        department_users = self.jira_report.get_current_users()
        department_leaked_time = 0

        for user_name in department_users:
            user_leaked_time = self.get_leaked_time(start_date, end_date, user_name)
            department_leaked_time += user_leaked_time

        return department_leaked_time

def calculate_leaked_time(df):
    df['Period\'s Leaked Time'] = round(df.apply(
        lambda row: abs(row['estimated_time'] - row['timespent']) if row['timespent'] > row['estimated_time'] else 0,
        axis=1), 2)
    print(df)
    return df

if __name__ == '__main__':
    df = pd.DataFrame({
        'timespent': [29],
        'estimated_time': [28.25],
        'logged_time': [26.67]
    })

    calculate_leaked_time(df)
