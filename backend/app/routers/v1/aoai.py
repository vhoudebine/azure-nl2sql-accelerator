import sys
import os
import time
from fastapi import APIRouter, BackgroundTasks, Request
from fastapi.responses import StreamingResponse

  
router = APIRouter(
    prefix="/aoai",
    tags=["aoai"],
)

@router.get("/")
def main():
    return {"message": "running get"}
