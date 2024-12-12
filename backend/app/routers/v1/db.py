
import sys
import os
import time
from threading import Lock
from fastapi import APIRouter, BackgroundTasks, Request, HTTPException
from fastapi.responses import StreamingResponse

# check if sys.path has sqltoolkit path
sqltoolkit_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..'))
if sqltoolkit_path not in sys.path:
    sys.path.append(sqltoolkit_path)

from sqltoolkit.indexer import DatabaseIndexer

task_lock = Lock()

def background_index_database(subset_table, aoai_client, db_client):
    indexer = DatabaseIndexer(client=db_client, openai_client=aoai_client.client)
    table_subset = ['SalesLT.SalesOrderHeader', 
                    'SalesLT.SalesOrderDetail',
                    'SalesLT.Product',
                    'SalesLT.Customer',
                    'SalesLT.ProductCategory']

    manifest = indexer.fetch_and_describe_tables()
    indexer.generate_table_embeddings()

    tables_dict = indexer.export_json_manifest()
    with open('tables_manifest.json', 'w') as f:
        f.write(tables_dict)

    print(indexer.tables[0].description)

    search_endpoint = os.getenv('AZURE_AI_SEARCH_ENDPOINT')
    search_key = os.getenv('AZURE_AI_SEARCH_API_KEY')
    embedding_deployment = os.getenv('AZURE_OPENAI_EMBEDDING_DEPLOYMENT_NAME')
    aoai_endpoint = os.getenv('AZURE_OPENAI_ENDPOINT')
    aoai_key = os.getenv('AZURE_OPENAI_API_KEY')

    index_name = 'adventureworks'

    indexer.create_azure_ai_search_index(
        search_endpoint=search_endpoint,
        search_credential=search_key,
        index_name=index_name,
        embedding_deployment=embedding_deployment,
        openai_endpoint=aoai_endpoint,
        openai_key=aoai_key,
    )

    # write to AI Search
    indexer.push_to_ai_search()

    # release the lock
    task_lock.release()

# ROUTER
router = APIRouter(
    prefix="/db",
    tags=["db"],
)

# GET

@router.get("/")
def main():
    return {"message": "running main"}

@router.get("/info")
async def post_test_aoai(request: Request):
    # return {"message": "Not implemented yet"}
    db_client = request.app.state.db_client
    return db_client.list_database_tables()

@router.get("/status")
async def get_task_status():
    if task_lock.locked():
        raise HTTPException(status_code=423, detail="Task is already running")
    return {"message": "Task is not running"}

# POST

@router.post("/index-database", status_code=202)
async def index_database(obj: dict, request: Request, background_tasks: BackgroundTasks):
    # checking if task_lock is locked
    if task_lock.locked():
        raise HTTPException(status_code=423, detail="Task is already running")
    
     # init subset_table as empty json array
    subset_table = []
    if obj.get("subset_table"):
        subset_table = obj.get("subset_table")

    aoai_client = request.app.state.aoai_client
    db_client = request.app.state.db_client

    try:
        task_lock.acquire(blocking=False)
        background_tasks.add_task(background_index_database, subset_table, aoai_client, db_client)
    except:
        if task_lock.locked():
            task_lock.release()
        raise HTTPException(status_code=500, detail="Error starting task")
