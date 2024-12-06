from fastapi import APIRouter
from routers.v1 import test

router = APIRouter(
    prefix="/api/v1"
)

router.include_router(test.router)

