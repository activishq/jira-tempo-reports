import unittest
from unittest.mock import patch, MagicMock, call
from datetime import datetime, timedelta
from reports.jira_reports import JiraReports
from reports.combined_reports import JiraTempoReport
import random
import pandas as pd

class TestJiraReports(unittest.TestCase):

    def setUp(self):
        self.jira_reports = JiraReports()

    def test_get_current_users(self):
        users = self.jira_reports.get_current_users()
        self.assertIsInstance(users, list)
        self.assertTrue(len(users) > 0)
        self.assertIn('Sonia Marquette', users)

    def test_get_department_availability(self):
        availability = self.jira_reports.get_department_availability()
        self.assertIsInstance(availability, float)
        self.assertTrue(availability > 0)

    @patch('reports.jira_reports.requests.get')
    def test_get_estimated_time(self, mock_get):
        # Mock the API response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'issues': [
                {
                    'key': 'TEST-1',
                    'fields': {
                        'timespent': 3600,
                        'timeoriginalestimate': 7200
                    }
                }
            ]
        }
        mock_get.return_value = mock_response

        df = self.jira_reports.get_estimated_time('2023-01-01', '2023-01-31', 'Test User')

        self.assertIsInstance(df, pd.DataFrame)
        self.assertEqual(len(df), 1)
        self.assertEqual(df.iloc[0]['issue_key'], 'TEST-1')
        self.assertEqual(df.iloc[0]['timespent'], 1.0)  # 3600 seconds = 1 hour
        self.assertEqual(df.iloc[0]['estimated_time'], 2.0)  # 7200 seconds = 2 hours

    @patch('reports.jira_reports.JiraReports.get_current_users')
    @patch('reports.jira_reports.JiraReports.get_estimated_time')
    def test_get_department_total_time_spent(self, mock_get_estimated_time, mock_get_current_users):
        # Mock the get_current_users method to return a fixed list of users
        mock_get_current_users.return_value = ['User1', 'User2']

        # Mock the get_estimated_time method to return different DataFrames for each user
        mock_get_estimated_time.side_effect = [
            pd.DataFrame({
                'user': ['User1', 'User1'],
                'issue_key': ['TEST-1', 'TEST-2'],
                'timespent': [5.0, 3.0],
                'estimated_time': [4.0, 2.0]
            }),
            pd.DataFrame({
                'user': ['User2', 'User2'],
                'issue_key': ['TEST-3', 'TEST-4'],
                'timespent': [2.0, 1.0],
                'estimated_time': [3.0, 1.0]
            })
        ]

        jira_reports = JiraReports()
        total_time = jira_reports.get_department_total_time_spent('2023-01-01', '2023-01-31')

        self.assertEqual(total_time, 11.0)  # 5.0 + 3.0 + 2.0 + 1.0

    @patch('reports.jira_reports.JiraReports.get_current_users')
    @patch('reports.jira_reports.JiraReports.get_estimated_time')
    def test_get_department_estimated_time(self, mock_get_estimated_time, mock_get_current_users):
        # Mock the get_current_users method to return a fixed list of users
        mock_get_current_users.return_value = ['User1', 'User2']

        # Mock the get_estimated_time method to return different DataFrames for each user
        mock_get_estimated_time.side_effect = [
            pd.DataFrame({
                'user': ['User1', 'User1'],
                'issue_key': ['TEST-1', 'TEST-2'],
                'timespent': [5.0, 3.0],
                'estimated_time': [4.0, 2.0]
            }),
            pd.DataFrame({
                'user': ['User2', 'User2'],
                'issue_key': ['TEST-3', 'TEST-4'],
                'timespent': [2.0, 1.0],
                'estimated_time': [3.0, 1.0]
            })
        ]

        jira_reports = JiraReports()
        estimated_time = jira_reports.get_department_estimated_time('2023-01-01', '2023-01-31')

        self.assertEqual(estimated_time, 10.0)  # 4.0 + 2.0 + 3.0 + 1.0

    @patch('reports.tempo_reports.TempoReport')
    def test_calculate_weekly_billable_hours(self, mock_tempo_report):
        jira_tempo_report = JiraTempoReport()

        # Utiliser la vraie méthode get_current_users
        real_users = JiraReports().get_current_users()

        # Mock de la méthode get_billable_time
        jira_tempo_report.get_billable_time = MagicMock(return_value=40.0)

        # Définir la période de test
        start_date = '2023-01-01'
        end_date = '2023-01-14'  # 2 semaines

        # Appeler la méthode à tester
        result = jira_tempo_report.calculate_weekly_billable_hours(start_date, end_date)

        # Vérifications
        self.assertIsInstance(result, pd.DataFrame)

        # Vérifier que tous les utilisateurs réels sont dans le résultat
        self.assertEqual(set(real_users), set(result['user'].unique()),
                         "Les utilisateurs dans le résultat devraient correspondre exactement aux utilisateurs réels")

        # Vérifier que le nombre de lignes est correct (nombre d'utilisateurs * 2 semaines)
        expected_rows = len(real_users) * 2
        self.assertEqual(len(result), expected_rows,
                         f"Expected {expected_rows} rows, but got {len(result)}")

        # Vérifier les dates de début de semaine
        expected_week_starts = [datetime(2023, 1, 1), datetime(2023, 1, 8)]
        self.assertEqual(set(result['week_start'].unique()), set(expected_week_starts))

        # Vérifier que get_billable_time a été appelé correctement pour chaque utilisateur et chaque semaine
        expected_calls = [
            call(start_date, '2023-01-07', user) for user in real_users
        ] + [
            call('2023-01-08', end_date, user) for user in real_users
        ]
        jira_tempo_report.get_billable_time.assert_has_calls(expected_calls, any_order=True)


if __name__ == '__main__':
    unittest.main()
