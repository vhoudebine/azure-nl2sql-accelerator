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

# load environment variables
load_dotenv(override=True)

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Starting up...")
    try:
        yield
    finally:
        print("Shutting down...")

# app start
app = FastAPI(
    debug=True,
    lifespan=lifespan
)

# routers
app.include_router(router)
