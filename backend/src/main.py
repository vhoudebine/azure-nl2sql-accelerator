from fastapi import FastAPI, HTTPException
from .routers import test

app = FastAPI()

app.include_router(test.router)

@app.get("/")
async def root():
    raise HTTPException(status_code=400, detail="Invalid API use")
    # return {400: {"description": "non API use"}}
    