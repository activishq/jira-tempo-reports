import json
import logging
import requests
from requests.auth import HTTPBasicAuth
import webbrowser
from urllib.parse import urlencode, urlparse, parse_qs
from dotenv import find_dotenv, dotenv_values
from constants import (
    JIRA_USERNAME,
    JIRA_API_KEY,
    TEMPO_ACCESS_TOKEN,
    TEMPO_CLIENT_ID,
    TEMPO_SECRET_ID,
    TEMPO_REFRESH_TOKEN,
    EnvUpdater,
)

logger = logging.getLogger(__name__)


class TempoTokenRefreshError(Exception):
    """Raised when the Tempo OAuth token could not be refreshed.

    This typically means both the access token and the refresh token have
    expired (Tempo tokens live ~30 days), and a full manual OAuth
    authorization is required to obtain a new pair of tokens.
    """


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
    __instance = None
    redirect_uri = 'https://www.google.com/callback/'
    token_url = 'https://api.tempo.io/oauth/token/'
    
    def __new__(cls):
        if cls.__instance is None:
            cls.__instance = super(TokenManager, cls).__new__(cls)
            cls.__instance.client_id = TEMPO_CLIENT_ID
            cls.__instance.secret_id = TEMPO_SECRET_ID
            cls.__instance.access_token = TEMPO_ACCESS_TOKEN
            cls.__instance.refresh_token = TEMPO_REFRESH_TOKEN

        return cls.__instance
    

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

        self.access_token = data['access_token']
        self.refresh_token = data['refresh_token']

        EnvUpdater.update_tokens(data['access_token'], data['refresh_token'])
        
        return data

    def _reload_from_env(self):
        """Reload the tokens from the .env file.

        Tempo uses rotating refresh tokens, and several processes (API,
        Streamlit, the background refresher) share the same .env file. Whenever
        one process refreshes, the others hold stale in-memory tokens. Reloading
        from disk lets a process pick up tokens refreshed elsewhere before
        attempting a refresh of its own (which would fail with a rotated token).
        """
        dotenv_path = find_dotenv()
        if not dotenv_path:
            return
        values = dotenv_values(dotenv_path)
        access_token = values.get("TEMPO_ACCESS_TOKEN")
        refresh_token = values.get("TEMPO_REFRESH_TOKEN")
        if access_token:
            self.access_token = access_token
        if refresh_token:
            self.refresh_token = refresh_token

    def refresh_access_token(self):
        """Refresh the access token using the refresh token.

        Always reads the freshest refresh token from disk first (to cope with
        token rotation across processes) and validates the response so a failed
        refresh raises a clear error instead of a cryptic KeyError.
        """
        # Use the most recent refresh token available on disk.
        self._reload_from_env()

        data = {
            'grant_type': 'refresh_token',
            'client_id': self.client_id,
            'client_secret': self.secret_id,
            'redirect_uri': self.redirect_uri,
            'refresh_token': self.refresh_token
        }
        response = requests.post(self.token_url, data=data)

        try:
            payload = response.json()
        except ValueError:
            payload = {}

        if (
            response.status_code != 200
            or "access_token" not in payload
            or "refresh_token" not in payload
        ):
            # Maybe another process already rotated the tokens; re-read disk so
            # the caller can retry with whatever is currently valid.
            self._reload_from_env()
            raise TempoTokenRefreshError(
                "Tempo token refresh failed "
                f"(status={response.status_code}): {payload or response.text}"
            )

        self.access_token = payload['access_token']
        self.refresh_token = payload['refresh_token']

        EnvUpdater.update_tokens(payload['access_token'], payload['refresh_token'])

        return payload


def tempo_request(method, url, *, params=None, json=None, extra_headers=None):
    """Perform an authenticated request against the Tempo API.

    Handles 401 responses gracefully:
      1. Reload tokens from .env and retry (another process / the background
         refresher may have already rotated the tokens).
      2. If still unauthorized, refresh the token ourselves and retry once.

    Raises TempoTokenRefreshError (via refresh_access_token) when the tokens
    can no longer be refreshed and a manual re-authorization is required.
    """
    token_manager = TokenManager()

    def _send(token):
        headers = {"Authorization": f"Bearer {token}"}
        if extra_headers:
            headers.update(extra_headers)
        return requests.request(method, url, headers=headers, params=params, json=json)

    response = _send(token_manager.access_token)

    if response.status_code == 401:
        token_manager._reload_from_env()
        response = _send(token_manager.access_token)

    if response.status_code == 401:
        token_manager.refresh_access_token()
        response = _send(token_manager.access_token)

    return response
