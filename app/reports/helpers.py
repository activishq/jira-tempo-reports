import requests
from requests.auth import HTTPBasicAuth
from constants import (
    JIRA_USERNAME,
    JIRA_API_KEY,
    TEMPO_ACCESS_TOKEN,
)


class JiraApi:
    base_url = "https://activis.atlassian.net"
    headers = {
        "Accept": "application/json"
    }
    auth = HTTPBasicAuth(JIRA_USERNAME, JIRA_API_KEY)
    
    @classmethod
    def search(cls, params):
        url = f"{cls.base_url}/rest/api/3/search/jql"
        return requests.request(
            "GET",
            url,
            headers=cls.headers,
            params=params,
            auth=cls.auth
        )
    
    @classmethod
    def user_search(cls, params):
        url = f"{cls.base_url}/rest/api/3/user/search"
        return requests.get(url, params=params, auth=cls.auth)
    
    @classmethod
    def get_issue(cls, issue_id):
        url = f"{cls.base_url}/rest/api/3/issue/{issue_id}"
        return requests.get(url, auth=cls.auth)
    
class Employees:
    data = {
        'Sonia Marquette': '557058:32b276cf-1a9f-4fd5-9dc9-067ddca36ed4',
        'Claire Conrardy': '557058:74a3c4c3-38aa-4201-b5d9-478462777444',
        'Benoit Leboucher': '557058:e1f0069a-5123-4cfa-98c2-de32588aed26',
        'Eric Ferole': '557058:f29b0c56-f018-47c6-af4f-f6f44ba03bb4',
        'Laurence Cauchon': '557058:eba24c3e-0273-4c27-bf2b-661215620795',
        'Julien Le Mée': '557058:eddec97e-7457-47dc-91c7-06907ee8ef9f',
        'David Chabot': '557058:x29b0c56-x018-47c6-af4f-f6f44ba03bb4',
        'Thierry Tanguay': '557058:y29b0c56-y018-47c6-af4f-f6f44ba03bb4',
        # 'Simon Bouchard': '712020:32ea8dc5-c696-4365-be1b-2ac476c34039',
        'Nancy L. Rodriguez': '712020:b0bfc929-6691-4ce9-8152-32cb07b51b27',
        'Jeff Trempe': '712020:dc3a2115-d8ee-4d15-a38b-c1978136c148',
        # 'Evan Buckiewicz': '712020:d951992c-717d-4485-bc35-a459cef088db',
        'David Cazal': '712020:6d7bad8f-2de8-4ca0-bd29-5d3ba83dec44'
    }

    @classmethod
    def get_user_account_id(cls, user: str) -> str:
        return cls.data.get(user)
