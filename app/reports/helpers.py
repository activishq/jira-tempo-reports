import requests
from requests.auth import HTTPBasicAuth
from constants import (
    JIRA_USERNAME,
    JIRA_API_KEY,
    TEMPO_ACCESS_TOKEN,
)


class JiraApi:
    url = "https://activis.atlassian.net"
    headers = {
        "Accept": "application/json"
    }
    auth = HTTPBasicAuth(JIRA_USERNAME, JIRA_API_KEY)

    @classmethod
    def get(cls, params):
        return requests.request(
            'GET',
            cls.url,
            headers=cls.headers

        )
        return requests.get(cls.__url, params=params, auth=cls.__auth)
    
    @classmethod
    def search(cls, params):
        
        return requests.get(cls.__url+'/rest/api/3/search', params=params, auth=cls.__auth)
    
