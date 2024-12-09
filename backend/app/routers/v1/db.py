import sys
import os
import time
from fastapi import APIRouter, BackgroundTasks, Request
from fastapi.responses import StreamingResponse

def background_init_metadata():
    # do some test while loops to simulate long running process with waiting time
    # this will be replaced with actual code to connect to database and get metadata
    # for now, just return a dummy response
    for i in range(10):
        print(f"i: {i}")
        time.sleep(1)
  
router = APIRouter(
    prefix="/db",
    tags=["db"],
)

@router.get("/")
def main():
    return {"message": "running main"}

@router.get("/info")
async def post_test_aoai(request: Request):
    # return {"message": "Not implemented yet"}
    db_util = request.app.state.db_util
    return db_util.list_database_tables()

@router.post("/init-metadata")
def init_db_metadata(obj: dict, request: Request, background_tasks: BackgroundTasks):
    background_tasks.add_task(background_init_metadata)
    return {"message": "db metadata initialization started"}
