import sys
import os
import re
import time
from threading import Lock
from azure.core.credentials import AzureKeyCredential
from azure.core.exceptions import ResourceNotFoundError
from openai import AzureOpenAI, AsyncAzureOpenAI
from azure.search.documents.indexes import SearchIndexClient
# from azure.search.documents.models import QueryType, QueryCaptionType, QueryAnswerType
# from azure.search.documents.models import VectorizableTextQuery
from fastapi import APIRouter, BackgroundTasks, Request, HTTPException
from fastapi.responses import StreamingResponse

# check if sys.path has sqltoolkit path
sqltoolkit_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..'))
if sqltoolkit_path not in sys.path:
    sys.path.append(sqltoolkit_path)

from sqltoolkit import connectors, client, indexer

task_lock = Lock()
internal_indexer = None
status_text = ""

def get_status_of_index_database():
    # this may change to pull status text from internal_indexer
    log_message = ""
    return log_message

def background_index_database(aoai_info, search_info, db_info):

    print("Running background task")
    print(aoai_info)
    print(search_info)
    print(db_info)

    global internal_indexer
    global status_text

    aoai_client = None
    db_client = None

    if internal_indexer is None:
        # if indexer is empty, means db client and aoai clients are not initialized
    
        #init aoai client
        aoai_client = AzureOpenAI(
            azure_endpoint=aoai_info.get("endpoint"),
            api_key=aoai_info.get("api_key"),
            api_version="2024-06-01"
        )

        # init db client
        db_type = re.sub(r'[^a-zA-Z]', '', db_info.get("type")).lower()
        # checking if database is azure sql server while ignoring case
        if db_type.lower() == "azuresql":
            sql_db = connectors.AzureSQLConnector(
                server=db_info.get("server"),
                database=db_info.get("database"),
                username=db_info.get("username"),
                password=db_info.get("password"),
                use_entra_id=False
            )
            db_client = client.DatabaseClient(sql_db)
        else:
            raise ValueError("Database type not supported")

        internal_indexer = indexer.DatabaseIndexer(
            client=db_client,
            openai_client=aoai_client,
            aoai_deployment=aoai_info.get("model_deployment"),
            embedding=aoai_info.get("embedding_deployment")
        )

    manifest = internal_indexer.fetch_and_describe_tables()
    internal_indexer.generate_table_embeddings()

    tables_dict = internal_indexer.export_json_manifest()
    with open('tables_manifest.json', 'w') as f:
        f.write(tables_dict)

    search_endpoint = search_info.get("endpoint")
    search_key = search_info.get("api_key")
    embedding_deployment = aoai_info.get("embedding_deployment")
    aoai_endpoint = aoai_info.get("endpoint")
    aoai_key = aoai_info.get("api_key")

    aisearch_index = search_info.get("index_name")

    internal_indexer.create_azure_ai_search_index(
        search_endpoint=search_endpoint,
        search_credential=search_key,
        index_name=aisearch_index,
        embedding_deployment=embedding_deployment,
        openai_endpoint=aoai_endpoint,
        openai_key=aoai_key,
    )
    # write to AI Search
    internal_indexer.push_to_ai_search()

    # may close db connection and the aoai connection here.
    
    # release the lock
    task_lock.release()

def background_index_database_test(aoai_info, search_info, db_info):
    print("Running background task")
    print(aoai_info)
    print(search_info)
    print(db_info)
    time.sleep(30)
    task_lock.release()

def check_ai_search_index(search_endpoint, search_key, search_index):
    search_index_client = SearchIndexClient(
        endpoint=search_endpoint, 
        credential=AzureKeyCredential(search_key)
    )

    try:   
        # Check if the index has data
        index_client = search_index_client.get_search_client(search_index)
        results = index_client.search(search_text="*", top=1)
        if not any(results):
            print("Index exists but has no data.")
            return "missing_index_data"
        
        return "ready"
    
    except ResourceNotFoundError as e:
        print(f"Index does not exist: {str(e)}")
        return "index_not_found"

    except Exception as e:
        print(f"An error occurred: {str(e)}")
        
    return "error"

# ROUTER
router = APIRouter(
    prefix="/db",
    tags=["db"],
)


# GET

@router.get("/")
def main():
    return {"message": "running main"}

@router.get("/test")
async def test_aoai(request: Request):
    db_client = request.app.state.db_client
    return db_client.list_database_tables()

@router.get("/index-database-status")
async def get_task_status():
    if task_lock.locked():
        raise HTTPException(status_code=423, detail="Task is already running")
    return {"message": "Task is not running"}


# POST

@router.post("/index-status")
async def post_index_status(obj: dict):
    # checking thread lock first
    if task_lock.locked():
        raise HTTPException(status_code=423, detail="Indexing is already running")

    # checking if obj has search_endpoint, search_key, search_index
    if not obj.get("endpoint") or not obj.get("api_key") or not obj.get("index_name"):
        raise HTTPException(status_code=400, detail="Missing required body parameters")

    index_status = check_ai_search_index(
        search_endpoint=obj.get("endpoint"),
        search_key=obj.get("api_key"),
        search_index=obj.get("index_name")
    )

    if index_status == "ready":
        return {"message": "Index exist and is ready"}
    
    if index_status == "index_not_found":
        raise HTTPException(status_code=404, detail="Index does not exist or has no data")
    
    if index_status == "missing_index_data":
        raise HTTPException(status_code=404, detail="Index exists but has no data")
    
    raise HTTPException(status_code=400, detail="Error checking index status, check credentials")
    
@router.post("/index-database-test", status_code=202)
async def index_database(obj: dict, request: Request, background_tasks: BackgroundTasks):
    # checking if task_lock is locked
    if task_lock.locked():
        raise HTTPException(status_code=423, detail="Indexing is already running")
    
    # checking if obj has aoai_info
    if not obj.get("aoai_info"):
        raise HTTPException(status_code=400, detail="Missing required body parameters")
    aoai_info = obj.get("aoai_info")

    # checking if obj has search_info
    if not obj.get("aisearch_info"):
        raise HTTPException(status_code=400, detail="Missing required body parameters")
    search_info = obj.get("aisearch_info")

    # checking if obj has db_info
    if not obj.get("db_info"):
        raise HTTPException(status_code=400, detail="Missing required body parameters")
    db_info = obj.get("db_info")

    try:
        task_lock.acquire(blocking=False)
        background_tasks.add_task(background_index_database_test, aoai_info, search_info, db_info)
    except:
        if task_lock.locked():
            task_lock.release()
        raise HTTPException(status_code=500, detail="Error starting task")

@router.post("/index-database", status_code=202)
async def index_database(obj: dict, request: Request, background_tasks: BackgroundTasks):
    # checking if task_lock is locked
    if task_lock.locked():
        raise HTTPException(status_code=423, detail="Indexing is already running")
    
    # checking if obj has aoai_info
    if not obj.get("aoai_info"):
        raise HTTPException(status_code=400, detail="Missing required body parameters")
    aoai_info = obj.get("aoai_info")

    # checking if obj has search_info
    if not obj.get("aisearch_info"):
        raise HTTPException(status_code=400, detail="Missing required body parameters")
    search_info = obj.get("aisearch_info")

    # checking if obj has db_info
    if not obj.get("db_info"):
        raise HTTPException(status_code=400, detail="Missing required body parameters")
    db_info = obj.get("db_info")

    try:
        task_lock.acquire(blocking=False)
        background_tasks.add_task(background_index_database, aoai_info, search_info, db_info)
    except:
        if task_lock.locked():
            task_lock.release()
        raise HTTPException(status_code=500, detail="Error starting task")
