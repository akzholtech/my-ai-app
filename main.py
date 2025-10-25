from fastapi import FastAPI
from starlette.staticfiles import StaticFiles

from routers import login_page, auth, dashboard

app = FastAPI(title="Portfolio")
app.mount("/static", StaticFiles(directory="static"), name="static")

app.include_router(login_page.router)
app.include_router(auth.router)
app.include_router(dashboard.router)

