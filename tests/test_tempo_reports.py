import unittest
from unittest.mock import patch, MagicMock
import pandas as pd
import requests
from reports.tempo_reports import TempoReport

class TestTempoReport(unittest.TestCase):
    def setUp(self):
        patcher = patch('reports.tempo_reports.config')
        self.mock_config = patcher.start()
        self.mock_config.return_value = 'fake_token'
        self.addCleanup(patcher.stop)

        # Créer un mock pour requests.Session
        session_patcher = patch('reports.tempo_reports.requests.Session')
        self.mock_session_class = session_patcher.start()
        self.mock_session = MagicMock()
        self.mock_response = MagicMock()
        self.mock_session_class.return_value = self.mock_session
        self.addCleanup(session_patcher.stop)

        # Configure session mock
        self.mock_response.raise_for_status.return_value = None
        self.mock_session.get.return_value = self.mock_response

        # Données de test
        self.mock_worklogs = {
            'results': [
                {
                    'timeSpentSeconds': 3600,
                    'issue': {'key': 'TEST-1'},
                    'author': {'displayName': 'Test User'},
                },
                {
                    'timeSpentSeconds': 7200,
                    'issue': {'key': 'TEST-1'},
                    'author': {'displayName': 'Test User'},
                }
            ],
            'metadata': {}
        }

        # Configure response mock
        self.mock_response.json.return_value = self.mock_worklogs

        # Create TempoReport instance
        self.tempo_report = TempoReport()

    def test_get_worklogs(self):
        """Test la récupération des worklogs"""
        start_date = '2023-01-01'
        end_date = '2023-01-31'
        user_name = 'Test User'

        # Test sans user_name
        worklogs = self.tempo_report.get_worklogs(start_date, end_date)
        self.assertEqual(len(worklogs), 2)
        self.assertEqual(worklogs[0]['issue']['key'], 'TEST-1')

        # Test avec user_name
        worklogs = self.tempo_report.get_worklogs(start_date, end_date, user_name)
        self.assertEqual(len(worklogs), 2)

        # Vérifier les paramètres de l'appel API
        self.mock_session.get.assert_called_with(
            'https://api.tempo.io/core/3/worklogs',
            params={
                'from': start_date,
                'to': end_date,
                'limit': 50,
                'offset': 0,
                'workerId': user_name
            }
        )

    def test_get_logged_time(self):
        """Test le calcul du temps loggé pour un utilisateur"""
        print("\nDebug - Starting test_get_logged_time")
        print(f"\nDebug - Mock response data: {self.mock_worklogs}")

        test_user = "Test User"
        start_date = '2023-01-01'
        end_date = '2023-01-31'

        df = self.tempo_report.get_logged_time(start_date, end_date, test_user)

        self.assertIsInstance(df, pd.DataFrame)
        self.assertGreater(len(df), 0)

        expected_columns = ['issue_key', 'logged_time', 'user']
        self.assertTrue(all(col in df.columns for col in expected_columns))

        test1_data = df[df['issue_key'] == 'TEST-1']
        expected_hours = 3.0
        self.assertEqual(test1_data['logged_time'].iloc[0], expected_hours)

    def test_get_department_logged_time(self):
        """Test le calcul du temps total pour un département"""
        start_date = '2023-01-01'
        end_date = '2023-01-31'
        department_users = ['Test User', 'Another User']

        # Configuration du mock pour retourner différentes données pour différents utilisateurs
        worklogs_user1 = {
            'results': [
                {
                    'timeSpentSeconds': 3600,
                    'issue': {'key': 'TEST-1'},
                    'author': {'displayName': 'Test User'},
                }
            ]
        }
        worklogs_user2 = {
            'results': [
                {
                    'timeSpentSeconds': 7200,
                    'issue': {'key': 'TEST-2'},
                    'author': {'displayName': 'Another User'},
                }
            ]
        }

        # Configure le mock pour retourner différentes réponses
        self.mock_response.json.side_effect = [worklogs_user1, worklogs_user2]

        total_time = self.tempo_report.get_department_logged_time(
            start_date, end_date, department_users
        )

        self.assertEqual(total_time, 3.0)  # (3600 + 7200) / 3600 = 3.0 hours

    def test_error_handling(self):
        """Test la gestion des erreurs"""
        # Simuler une erreur d'API
        self.mock_response.raise_for_status.side_effect = requests.RequestException("API Error")

        start_date = '2023-01-01'
        end_date = '2023-01-31'

        # Vérifier que get_worklogs gère l'erreur gracieusement
        worklogs = self.tempo_report.get_worklogs(start_date, end_date)
        self.assertEqual(len(worklogs), 0)

        # Vérifier que get_logged_time gère l'erreur gracieusement
        df = self.tempo_report.get_logged_time(start_date, end_date, "Test User")
        self.assertTrue(df.empty)

    def test_pagination(self):
        """Test la gestion de la pagination"""
        # Configurer le mock pour simuler plusieurs pages
        page1 = {
            'results': [{'timeSpentSeconds': 3600, 'issue': {'key': 'TEST-1'}, 'author': {'displayName': 'Test User'}}],
            'metadata': {'next': True}
        }
        page2 = {
            'results': [{'timeSpentSeconds': 7200, 'issue': {'key': 'TEST-2'}, 'author': {'displayName': 'Test User'}}],
            'metadata': {}
        }

        self.mock_response.json.side_effect = [page1, page2]

        worklogs = self.tempo_report.get_worklogs('2023-01-01', '2023-01-31')

        self.assertEqual(len(worklogs), 2)
        self.assertEqual(self.mock_session.get.call_count, 2)

if __name__ == '__main__':
    unittest.main()
