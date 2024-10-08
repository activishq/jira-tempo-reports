import unittest
from unittest.mock import patch, MagicMock
from reports.jira_reports import JiraReports
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

if __name__ == '__main__':
    unittest.main()
