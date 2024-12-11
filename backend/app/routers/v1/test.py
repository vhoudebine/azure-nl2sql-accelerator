import sys
import os
import time
import threading
from fastapi import APIRouter, BackgroundTasks, Request, HTTPException
from fastapi.responses import StreamingResponse


task_lock = threading.Lock()

def cpu_intensive_task(param):
    for i in range(30):
        print(f"i: {i}")
        time.sleep(1)
    
    task_lock.release()

router = APIRouter(
    prefix="/test",
    tags=["test"],
)

# GET

@router.get("/")
def get_test():
    return {"message": "Get call for test"}

@router.get("/id/{id}")
def get_test_with_id(id: int):
    return {"message": f"Get test with id {id}"}

@router.get("/status")
async def get_task_status():
    print(task_lock.locked())
    if task_lock.locked():
        raise HTTPException(status_code=423, detail="Task is already running")
    return {"message": "Task is not running"}


# POST

@router.post("/")
def post_test(obj: dict):
    return {"message": f"POST test with data {obj}"}

@router.post("/aoai")
async def post_test_aoai(obj: dict, request: Request):
    user_prompt = obj["user_prompt"]
    aoai_client = request.app.state.aoai_client
    resp = aoai_client.aoai_completion_simple(user_prompt)
    return {"message": resp}

@router.post("/aoai-stream")
async def post_test_aoai(obj: dict, request: Request):
    # return {"message": "Not implemented yet"}
    user_prompt = obj["user_prompt"]
    aoai_client = request.app.state.aoai_client
    return StreamingResponse(aoai_client.aoai_completion_simple_stream(user_prompt), media_type="text/event-stream")

@router.post("/long-running-task", status_code=202)
async def long_running_task(background_tasks: BackgroundTasks, param: int):
    print("Endpoint received request")
    
    # checking if task_lock is locked
    if task_lock.locked():
        raise HTTPException(status_code=423, detail="Task is already running")
    
    try:
        task_lock.acquire(blocking=False)
        background_tasks.add_task(cpu_intensive_task, param)
    except:
        if task_lock.locked():
            task_lock.release()
        raise HTTPException(status_code=500, detail="Error starting task")

