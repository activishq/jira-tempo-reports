import requests
import webbrowser
from decouple import config
from urllib.parse import urlencode, urlparse, parse_qs


# Constants
CLIENT_ID = config('TEMPO_CLIENT_ID')
SECRET_ID = config('TEMPO_SECRET_ID')
REDIRECT_URI = 'https://www.google.com/callback/'
JIRA_CLOUD_INSTANCE_NAME = 'activis'

# URLs
AUTHORIZATION_URL = f"https://{JIRA_CLOUD_INSTANCE_NAME}.atlassian.net/plugins/servlet/ac/io.tempo.jira/oauth-authorize/?client_id={CLIENT_ID}&redirect_uri={REDIRECT_URI}"
TOKEN_URL = "https://api.tempo.io/oauth/token/"


def get_authorization_code():
    """Prompt user to authorize the app and get the authorization code."""
    webbrowser.open(AUTHORIZATION_URL)
    redirect_response = input("Enter the full redirect URL (after granting permission): ")
    parsed = urlparse(redirect_response)
    code = parse_qs(parsed.query)['code'][0]
    return code


def get_access_token(code):
    """Obtain an access token using the authorization code."""
    data = {
        'grant_type': 'authorization_code',
        'client_id': CLIENT_ID,
        'client_secret': SECRET_ID,
        'redirect_uri': REDIRECT_URI,
        'code': code
    }
    response = requests.post(TOKEN_URL, data=data)
    return response.json()


def refresh_access_token(refresh_token):
    """Refresh the access token using the refresh token."""
    data = {
        'grant_type': 'refresh_token',
        'client_id': CLIENT_ID,
        'client_secret': SECRET_ID,
        'redirect_uri': REDIRECT_URI,
        'refresh_token': refresh_token
    }
    response = requests.post(TOKEN_URL, data=data)
    return response.json()

if __name__ == '__main__':
    code = get_authorization_code()
    tokens = get_access_token(code)

    print("Access Token:", tokens['access_token'])
    print("Refresh Token:", tokens['refresh_token'])
    print("Expires in:", tokens['expires_in'])

    # Uncomment the line below to refresh the access token using the refresh token.
    # new_tokens = refresh_access_token(tokens['refresh_token'])
    # print("New Access Token:", new_tokens['access_token'])