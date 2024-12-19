import os 
import requests

# variable
api_endpoint = "http://localhost:8000/api/v1"

def checking_ai_search_index(aisearch_info):

    # testing for now
    return "index_not_found"

    # check if the database is indexed
    response = requests.post(
        f"{api_endpoint}/db/index-status",
        json=aisearch_info
    )
    if response.status_code == 200:
        return "ready"
    elif response.status_code == 423:
        return "index_already_running"
    elif response.status_code == 404:
        return "index_not_found"
    else:
        return response.json().get("detail")
    
def check_database_indexing_status():
    response = requests.get(
        f"{api_endpoint}/db/index-database-status"
    )
    if response.status_code == 200:
        return "ready"
    elif response.status_code == 423:
        return "index_already_running"
    else:
        # print error message
        print(response.json())
        return "error"
    
def initialize_index_database(aoai_info, search_info, database_info, sub_table=None):
    response = requests.post(
        # f"{api_endpoint}/db/index-database",
        f"{api_endpoint}/db/index-database-test",
        json={
            "aoai_info": aoai_info,
            "aisearch_info": search_info,
            "db_info": database_info
        }
    )
    if response.status_code == 202:
        return "success"
    elif response.status_code == 423:
        return "index_already_running"
    else:
        return "error"