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
    