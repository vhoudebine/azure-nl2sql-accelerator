import os 
import requests

# variable
api_endpoint = "http://localhost:8000/api/v1"

def checking_ai_search_index(search_info):

    # check if the database is indexed
    response = requests.post(
        f"{api_endpoint}/db/index-status",
        json=search_info
    )
    if response.status_code == 200:
        return "ready"
    elif response.status_code == 423:
        return "index_already_running"
    elif response.status_code == 404:
        return "index_not_found"
    else:
        return "error"