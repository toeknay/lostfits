from fastapi import APIRouter

router = APIRouter()


@router.get("/api/hello")
def hello() -> dict[str, str]:
    return {"message": "Welcome to LostFits API"}
