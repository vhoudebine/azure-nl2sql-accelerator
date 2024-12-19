import os 
import requests

# variable
api_endpoint = "http://localhost:8000/api/v1"

def get_sql_query(aisearch_info, aoai_info, user_question):

    body = {
        "user_question": user_question,
        "aisearch_info": aisearch_info,
        "aoai_info": aoai_info
    }

    response = requests.post(
        f"{api_endpoint}/aoai/sql-query",
        json=body
    )
    if response.status_code == 200:
        return response.json()
    elif response.status_code == 423:
        return "index_already_running"
    elif response.status_code == 404:
        return "index_not_found"
    else:
        return response.json().get("detail")
    