import streamlit as st

# Importez vos pages ici
from pages import billable_hours_dashboard, availability

def main():
    st.sidebar.title("Navigation")
    page = st.sidebar.radio("Aller à", ["Dashboard des heures facturables", "Gestion du budget de production"])

    if page == "Dashboard des heures facturables":
        billable_hours_dashboard.main()
    elif page == "Gestion du budget de production":
        availability.availability_management()

if __name__ == "__main__":
    main()


# /rest/api/3/search/jql
# https://activis.atlassian.net/rest/api/3/search?jql=assigne



# new format
# url = "https://activis.atlassian.net/rest/api/3/search/jql"
# auth = HTTPBasicAuth("email@example.com", "<api_token>")

# headers = {
#   "Accept": "application/json"
# }


# query = {
#   'jql': 'project = HSP',
#   'nextPageToken': '<string>',
#   'maxResults': '{maxResults}',
#   'fields': '{fields}',
#   'expand': '<string>',
#   'reconcileIssues': '{reconcileIssues}'
# }

# response = requests.request(
#    "GET",
#    url,
#    headers=headers,
#    params=query,
#    auth=auth
# )
