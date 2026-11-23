from fastapi import APIRouter

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/{user_id}")
def read_user(user_id: int):
    return {"id": user_id}


@router.delete("/{user_id}", operation_id="remove_user")
async def delete_user(user_id: int):
    return {"deleted": user_id}
