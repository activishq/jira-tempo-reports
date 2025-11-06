import json
import requests
from requests.auth import HTTPBasicAuth
import webbrowser
from urllib.parse import urlencode, urlparse, parse_qs
from constants import (
    JIRA_USERNAME,
    JIRA_API_KEY,
    TEMPO_ACCESS_TOKEN,
    TEMPO_CLIENT_ID,
    TEMPO_SECRET_ID,
    TEMPO_REFRESH_TOKEN,
    EnvUpdater,
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


class JsonFileBackup:
    def __init__(self, file_name: str):
        self.file_name = file_name

    def dump(self, data: dict) -> None:
        with open(f'{self.file_name}.json', 'w') as f:
            json.dump(data, f, indent=4)

    def read(self) -> dict:
        try:
            with open(f'{self.file_name}.json', 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            with open(f'{self.file_name}.json', 'w') as f:
                json.dump({}, f, indent=4)
            return {}



class TokenManager:
    redirect_uri = 'https://www.google.com/callback/'
    token_url = "https://api.tempo.io/oauth/token/"

    def __init__(self):
        self.client_id = TEMPO_CLIENT_ID
        self.secret_id = TEMPO_SECRET_ID
        self.refresh_token = TEMPO_REFRESH_TOKEN

    def __get_authorization_code(self):
        """Prompt user to authorize the app and get the authorization code."""
        authorization_url = f"https://activis.atlassian.net/plugins/servlet/ac/io.tempo.jira/oauth-authorize/?client_id={self.client_id}&redirect_uri={self.redirect_uri}"
        webbrowser.open(authorization_url)
        redirect_response = input("Enter the full redirect URL (after granting permission): ")
        parsed = urlparse(redirect_response)
        code = parse_qs(parsed.query)['code'][0]
        return code

    def get_access_token(self):
        """Obtain an access token using the authorization code."""

        code = self.__get_authorization_code()
        data = {
            'grant_type': 'authorization_code',
            'client_id': self.client_id,
            'client_secret': self.secret_id,
            'redirect_uri': self.redirect_uri,
            'code': code
        }
        response = requests.post(self.token_url, data=data)
        data = response.json()

        EnvUpdater.update_tokens(data['access_token'], data['refresh_token'])
        
        return data

    def refresh_access_token(self):
        """Refresh the access token using the refresh token."""
        data = {
            'grant_type': 'refresh_token',
            'client_id': self.client_id,
            'client_secret': self.secret_id,
            'redirect_uri': self.redirect_uri,
            'refresh_token': self.refresh_token
        }
        response = requests.post(self.token_url, data=data)
        data = response.json()

        EnvUpdater.update_tokens(
            access_token=data['access_token'],
            refresh_token=data['refresh_token'],
        )
        
        return data
