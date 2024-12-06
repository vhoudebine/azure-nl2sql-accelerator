
from contextlib import asynccontextmanager
from fastapi import FastAPI
from routers.api import router
from internal.azure_openai import AzureOpenAIService
from dotenv import load_dotenv
from os import getenv

load_dotenv(override=True)


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Starting up...")
    try:
        # initialize azure openai client here.
        app.state.aoai_client = AzureOpenAIService(
            endpoint=getenv("AZURE_OPENAI_ENDPOINT"),
            api_key=getenv("AZURE_OPENAI_API_KEY"),
            deployment_name=getenv("AZURE_OPENAI_DEPLOYMENT_NAME")
        )
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
