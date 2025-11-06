import sys


sys.path.append('app')
from reports.helpers import TokenManager


token_manager = TokenManager()
tokens = token_manager.get_access_token()
print(tokens)