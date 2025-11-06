import sys


sys.path.append('app')
from reports.helpers import TokenManager


tokens = TokenManager.refresh_access_token()
print(tokens)
