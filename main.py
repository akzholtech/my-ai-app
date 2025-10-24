from fastapi import FastAPI
from routers import login_page, auth
app = FastAPI(title="Portfolio")
app.include_router(login_page.router)
app.include_router(auth.router)

