import sys
import os
import time
import json
from fastapi import APIRouter, BackgroundTasks, Request, HTTPException
from fastapi.responses import StreamingResponse
from azure.search.documents import SearchClient
from azure.search.documents.models import QueryType, QueryCaptionType, QueryAnswerType
from azure.search.documents.models import VectorizableTextQuery
from azure.core.credentials import AzureKeyCredential


def get_search_docs(user_question: str):
    search_endpoint = os.getenv('AZURE_AI_SEARCH_ENDPOINT')
    search_key = os.getenv('AZURE_AI_SEARCH_API_KEY')
    index_name = 'adventureworks'

    search_client = SearchClient(
        endpoint=search_endpoint, 
        credential=AzureKeyCredential(search_key), 
        index_name=index_name
    )

    vector_query = VectorizableTextQuery(text=user_question, k_nearest_neighbors=50, fields="embedding")

    results = search_client.search(  
        search_text=user_question,  
        vector_queries=[vector_query],
        query_type=QueryType.SEMANTIC,
        semantic_configuration_name='my-semantic-config',
        query_caption=QueryCaptionType.EXTRACTIVE,
        query_answer=QueryAnswerType.EXTRACTIVE,
        top=3
    )
    
    candidate_tables = []
    for result in results:
        candidate_tables.append(
            json.dumps({key: result[key] for key in ['name',
                                                    'business_readable_name',
                                                    'description',
                                                    'columns'] if key in result}, indent=4))

    return candidate_tables


def sql_query_from_llm(openai_client, tables_prompt, user_question):

    system_prompt = f"""
    You are a helpful AI data analyst assistant, 
        You can execute SQL queries to retrieve information from a sql database,
        The database is SQL server, use the right syntax to generate queries


        ### These are the available tables in the database alongside their descriptions:
        {tables_prompt}

        When asked a question that could be answered with a SQL query: 
        - Break down the question into smaller parts that can be answered with SQL queries
        - Identify the tables that contains the information needed to answer the question
        - Only once this is done, create a sql query to retrieve the information based on your understanding of the table
    
        Think step by step, before doing anything, share the different steps you'll execute to get the answer
        
        Your response should be in JSON format with the following structure:
        "chain_of_thought": "Your reasoning",
        "sql_query": "The generated sql query"

        Example:    
        question: "Show me the first 5 rows of the sales_data table"
        output: "chain_of_thought": "Your reasoning",
        "sql_query": "SELECT TOP 5 * FROM sales_data"

    """

    messages =[
        {
            "role": "system",
            "content": system_prompt
        },
        {
            "role": "user",
            "content": user_question
        }
    ]

    response = openai_client.chat.completions.create(
                    model="gpt-4o-global",
                    messages=messages,
                    response_format={"type": "json_object"}
                )

    response_message = response.choices[0].message.content
    response_json = json.loads(response_message)

    return response_json

  
router = APIRouter(
    prefix="/aoai",
    tags=["aoai"],
)

@router.get("/")
def main():
    return {"message": "running get"}


@router.post("/sql-query")
def get_sql_query(obj: dict, request: Request):

    # checking if obj has user_prompt key and it is not empty, throw error if not
    if "user_question" not in obj or obj["user_question"] == "":
        raise HTTPException(status_code=400, detail="User question cannot be empty")
    
    # user_question = obj["user_question"]
    # overriding for test
    user_question = "What is the first name of the customer that put in the most orders?"

    search_docs = get_search_docs(user_question)
    # print(search_docs)

    # loading client from state
    aoai_client = request.app.state.aoai_client
    openai_client = aoai_client.client
    result = sql_query_from_llm(openai_client=openai_client, tables_prompt=search_docs, user_question=user_question)
    return result
    

