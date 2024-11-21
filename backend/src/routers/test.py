from fastapi import APIRouter

router = APIRouter(
    prefix="/api",
    tags=["test"],
)

@router.get("/test")
def get_users():
    return {"message": "Get call for test"}

@router.get("/test/{id}")
def get_user(id: int):
    return {"message": f"Get test with id {id}"}

@router.post("/test")
def create_user(obj: dict):
    return {"message": f"POST test with data {obj}"}