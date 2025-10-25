from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.templating import Jinja2Templates
from starlette import status
from starlette.responses import HTMLResponse, RedirectResponse

from routers.auth import get_current_user

router = APIRouter()
templates = Jinja2Templates(directory="templates")
user_dependency = Annotated[dict, Depends(get_current_user)]

### Pages ###
@router.get('/dashboard', response_class=HTMLResponse)
async def root(request: Request):

    return templates.TemplateResponse('dashboard.html', context={'request': request})