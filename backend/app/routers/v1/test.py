from fastapi import APIRouter, Request

router = APIRouter(
    prefix="/test",
    tags=["test"],
)

@router.get("/")
def get_test():
    return {"message": "Get call for test"}

@router.get("/{id}")
def get_test_with_id(id: int):
    return {"message": f"Get test with id {id}"}

@router.post("/")
def post_test(obj: dict):
    return {"message": f"POST test with data {obj}"}

@router.post("/aoai")
async def post_test_aoai(request: Request):
    print(request)
    # testing
    req = await request.json()
    user_prompt = req.get("user_prompt")
    aoai_client = request.app.state.aoai_client
    resp = aoai_client.aoai_completion_simple(user_prompt)
    return {"message": resp}