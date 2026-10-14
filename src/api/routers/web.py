from fastapi import APIRouter
from fastapi.responses import HTMLResponse

router = APIRouter()


@router.get("/")
def web_ui():
    return HTMLResponse(open("templates/index.html").read())
