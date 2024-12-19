import sys
import os
import time
import json
from fastapi import APIRouter, BackgroundTasks, Request, HTTPException
from fastapi.responses import StreamingResponse
from openai import AzureOpenAI, AsyncAzureOpenAI
from azure.search.documents import SearchClient
from azure.search.documents.models import QueryType, QueryCaptionType, QueryAnswerType
from azure.search.documents.models import VectorizableTextQuery
from azure.core.credentials import AzureKeyCredential

search_client = None
aoai_client = None

def prompt_rewriting(aoai_info, user_question: str):

    global aoai_client
    model_deployment = aoai_info.get("model_deployment")
    if aoai_client is None:
        print("creating aoai client")
        aoai_client = AzureOpenAI(
            azure_endpoint=aoai_info.get("endpoint"),
            api_key=aoai_info.get("api_key"),
            api_version="2024-06-01"
        )


    rewriter_prompt = f"""
    You are a helpful AI SQL Agent. Your role is to help people translate their questions 
    into better questions that can be translated into SQL queries.
    You should disimbiguate the question and provide a more specific version of the question to the best of your ability
    You should rewrite the question in a way that is more likely to be answered by the database.

    You must only return a single sentence that is a better version of the user's question.

    """

    messages =[
        {
            "role": "system",
            "content": rewriter_prompt
        },
        {
            "role": "user",
            "content": user_question
        }
    ]

    rewriter_response = aoai_client.chat.completions.create(
                    model=model_deployment,
                    messages=messages,
                )

    rewriter_response = rewriter_response.choices[0].message.content
    return rewriter_response

def get_search_docs(aisearch_info, user_question: str):

    global search_client

    if search_client is None:
        print("creating search client")
        search_endpoint = aisearch_info.get("endpoint")
        search_key = aisearch_info.get("api_key")
        index_name = aisearch_info.get("index_name")

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

def sql_query_from_llm(aoai_info, tables_prompt, user_question):

    global aoai_client
    model_deployment = aoai_info.get("model_deployment")
    if aoai_client is None:
        print("creating aoai client")
        aoai_client = AzureOpenAI(
            azure_endpoint=aoai_info.get("endpoint"),
            api_key=aoai_info.get("api_key"),
            api_version="2024-06-01"
        )

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

    response = aoai_client.chat.completions.create(
                    model=model_deployment,
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
    return {"message": "running get aoai"}


@router.post("/sql-query")
def get_sql_query(obj: dict, request: Request):

    # checking if obj has user_prompt key and it is not empty, throw error if not
    if "user_question" not in obj or obj["user_question"] == "":
        raise HTTPException(status_code=400, detail="User question cannot be empty")
    user_question = obj.get("user_question")

    # checking if obj has aoai_info
    if not obj.get("aoai_info"):
        raise HTTPException(status_code=400, detail="Missing required body parameters")
    aoai_info = obj.get("aoai_info")

    # checking if obj has search_info
    if not obj.get("aisearch_info"):
        raise HTTPException(status_code=400, detail="Missing required body parameters")
    aisearch_info = obj.get("aisearch_info")
    
    # rewriting user question
    updated_user_question = prompt_rewriting(aoai_info=aoai_info, user_question=user_question)
    print(updated_user_question)

    search_docs = get_search_docs(aisearch_info=aisearch_info, user_question=updated_user_question)
    print(len(search_docs))

    result = sql_query_from_llm(aoai_info=aoai_info, tables_prompt=search_docs, user_question=updated_user_question)
    print(result)

    # adding search information as well as rewritten prompt to the result
    # result["search_docs"] = search_docs
    result["rewritten_prompt"] = updated_user_question

    return result
    

