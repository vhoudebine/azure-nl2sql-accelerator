import os
import sys
from contextlib import asynccontextmanager
from fastapi import FastAPI
from routers.api import router
from internal.azure_openai import AzureOpenAIService
from dotenv import load_dotenv

# adding sqltookit path for import
current_dir = os.path.dirname(__file__)
sqltoolkit_path = os.path.abspath(os.path.join(current_dir, '..', '..'))
print(f"sqltoolkit_path: {sqltoolkit_path}")
sys.path.append(sqltoolkit_path)

from sqltoolkit.connectors import AzureSQLConnector
from sqltoolkit.dbutils import DatabaseUtils

# load environment variables
load_dotenv(override=True)

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Starting up...")
    try:
        # initialize azure openai client here.
        app.state.aoai_client = AzureOpenAIService(
            endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
            api_key=os.getenv("AZURE_OPENAI_API_KEY"),
            deployment_name=os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME")
        )
        # adding database connection here
        # may require more logic to determind which database to connect to
        sql_db = AzureSQLConnector(
            server=os.getenv("AZURE_SQL_SERVER"),
            database=os.getenv("AZURE_SQL_DATABASE"),
            username=os.getenv("AZURE_SQL_USER"),
            password=os.getenv("AZURE_SQL_PASSWORD"),
            use_entra_id=False
        )
        db_util = DatabaseUtils(sql_db)
        app.state.db_util = db_util
        yield
    finally:
        print("Shutting down...")
        app.state.aoai_client.close()

# app start
app = FastAPI(
    debug=True,
    lifespan=lifespan
)

# routers
app.include_router(router)
