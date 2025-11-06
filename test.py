import sys


sys.path.append('app')
from reports.helpers import TokenManager


tokens = TokenManager.get_access_token()
print(tokens)
