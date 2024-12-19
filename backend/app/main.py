import os
import sys
from contextlib import asynccontextmanager
from fastapi import FastAPI
from routers.api import router
from internal.azure_openai import AzureOpenAIService
from dotenv import load_dotenv

# adding sqltookit path for import
# check if sys.path has sqltoolkit path
sqltoolkit_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if sqltoolkit_path not in sys.path:
    sys.path.append(sqltoolkit_path)

# import sqltoolkit
from sqltoolkit import connectors, client, indexer

# from sqltoolkit.connectors import AzureSQLConnector
# from sqltoolkit.client import DatabaseClient
# from sqltoolkit.indexer import DatabaseIndexer

# load environment variables
load_dotenv(override=True)

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Starting up...")
    try:
        # # initialize azure openai client here.
        # app.state.aoai_client = AzureOpenAIService(
        #     endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
        #     api_key=os.getenv("AZURE_OPENAI_API_KEY"),
        #     deployment_name=os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME")
        # )
        # # adding database connection here
        # db_type = os.getenv("DATABASE_TYPE")
        # db_client = None
        # # checking if database is azure sql server while ignoring case
        # if db_type.lower() == "azuresql":
        #     sql_db = connectors.AzureSQLConnector(
        #         server=os.getenv("AZURE_SQL_SERVER"),
        #         database=os.getenv("AZURE_SQL_DATABASE"),
        #         username=os.getenv("AZURE_SQL_USER"),
        #         password=os.getenv("AZURE_SQL_PASSWORD"),
        #         use_entra_id=False
        #     )
        #     db_client = client.DatabaseClient(sql_db)
        # # elif db_type.lower() == "sqlite":
        # #     raise ValueError("Database type not supported YET")
        # else:
        #     raise ValueError("Database type not supported")

        # app.state.db_client = db_client
        yield
    finally:
        print("Shutting down...")
        # app.state.aoai_client.close()

# app start
app = FastAPI(
    debug=True,
    lifespan=lifespan
)

# routers
app.include_router(router)
