import pandas as pd
from typing import List
from datetime import datetime, timedelta
from .jira_reports import JiraReports
from .tempo_reports import TempoReport

class JiraTempoReport:
    def __init__(self):
        self.jira_report = JiraReports()
        self.tempo_report = TempoReport()

    def get_merged_report(self, start_date: str, end_date: str, user_id: str) -> pd.DataFrame:
        df_jira_report = self.jira_report.get_estimated_time(start_date, end_date, user_id)
        df_tempo_report = self.tempo_report.get_logged_time(start_date, end_date, user_id)

        if df_jira_report.empty or df_tempo_report.empty:
            print(f"Warning: Empty data for user {user_id} in the specified date range.")
            return pd.DataFrame(columns=['Issue Key', 'Total Time Spent', 'Estimated Time', 'Period\'s Logged Time', 'Period\'s Leaked Time', 'Total Leaked Time'])

        # Fusionner les DataFrames en utilisant 'issue_key' comme clé et en spécifiant comment gérer les colonnes en double
        df_merged = pd.merge(df_jira_report, df_tempo_report, on='issue_key', how='outer', suffixes=('_jira', '_tempo'))

        # Nettoyer les colonnes dupliquées
        if 'user_jira' in df_merged.columns and 'user_tempo' in df_merged.columns:
            df_merged['user'] = df_merged['user_jira'].fillna(df_merged['user_tempo'])
            df_merged.drop(['user_jira', 'user_tempo'], axis=1, inplace=True)

        df_merged = df_merged.fillna(0)

        df_merged['Period\'s Leaked Time'] = self._calculate_period_leak_time(df_merged)
        df_merged['Total Leaked Time'] = self._calculate_total_leaked_time(df_merged)

        df_merged = df_merged.rename(columns={
            'estimated_time': 'Estimated Time',
            'issue_key': 'Issue Key',
            'timespent': 'Total Time Spent',
            'logged_time': 'Period\'s Logged Time'
        })

        return df_merged

    def _calculate_period_leak_time(self, df: pd.DataFrame) -> pd.Series:
        """Calculate the period's leaked time."""
        return df.apply(lambda row: min(max(row['timespent'] - row['estimated_time'], 0), row['logged_time']), axis=1)

    def _calculate_total_leaked_time(self, df: pd.DataFrame) -> pd.Series:
        """Calculate the total leaked time."""
        return df.apply(lambda row: max(row['timespent'] - row['estimated_time'], 0), axis=1)

    def get_logged_time(self, start_date: str, end_date: str, user_id: str) -> float:
        """Get total logged time for a user in the specified date range."""
        df_merged = self.get_merged_report(start_date, end_date, user_id)
        return df_merged['Period\'s Logged Time'].sum()

    def get_leaked_time(self, start_date: str, end_date: str, user_id: str) -> float:
        """Calculate leaked time for a user in the specified date range."""
        df_merged = self.get_merged_report(start_date, end_date, user_id)

        if df_merged.empty:
            return 0

        soutien = df_merged[df_merged['Issue Key'].str.contains('SOUTIEN', na=False)]['Period\'s Leaked Time'].sum()
        leaked_time = df_merged['Period\'s Leaked Time'].sum()
        total_leaked_time = leaked_time - soutien

        return round(total_leaked_time, 2)

    def get_billable_time(self, start_date: str, end_date: str, user_id: str) -> float:
        """Calculate billable time for a user in the specified date range."""
        logged_time_sum = self.get_logged_time(start_date, end_date, user_id)
        leaked_time_sum = self.get_leaked_time(start_date, end_date, user_id)
        billable_hours = abs(logged_time_sum - leaked_time_sum)

        return billable_hours

    def get_billable_ratio(self, start_date: str, end_date: str, user_id: str) -> float:
        """Calculate billable ratio for a user in the specified date range."""
        billable_hours = self.get_billable_time(start_date, end_date, user_id)
        logged_time = self.get_logged_time(start_date, end_date, user_id)

        if logged_time == 0:
            print(f"Warning: No logged time for user {user_id} in the specified date range.")
            return 0

        billable_ratio = round((billable_hours / logged_time) * 100, 2)

        return billable_ratio

    def get_department_leaked_time(self, start_date: str, end_date: str) -> float:
        """Calculate total leaked time for the department in the specified date range."""
        department_users = self.jira_report.get_current_users()
        department_leaked_time = sum(self.get_leaked_time(start_date, end_date, user_name) for user_name in department_users)

        return department_leaked_time

    def calculate_weekly_billable_hours(self, start_date: str, end_date: str) -> pd.DataFrame:
        start = datetime.strptime(start_date, "%Y-%m-%d")
        end = datetime.strptime(end_date, "%Y-%m-%d")

        current_users = self.jira_report.get_current_users()
        weekly_data = []

        while start <= end:
            week_end = start + timedelta(days=6)
            week_end = min(week_end, end)

            for user in current_users:
                billable_time = self.get_billable_time(start.strftime("%Y-%m-%d"), week_end.strftime("%Y-%m-%d"), user)

                weekly_data.append({
                    'user': user,
                    'week_start': start,
                    'billable_hours': billable_time
                })

            start = week_end + timedelta(days=1)

        return pd.DataFrame(weekly_data)
