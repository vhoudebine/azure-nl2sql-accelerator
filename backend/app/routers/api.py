from fastapi import APIRouter
from routers.v1 import aoai, test, db

router = APIRouter(
    prefix="/api/v1"
)

router.include_router(test.router)
router.include_router(aoai.router)
router.include_router(db.router)

