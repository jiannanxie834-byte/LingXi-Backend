from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import init_db

from app.routers import (
    auth,
    admin,
    plan,
    resource,
    chat,
    evaluation,
    todo,
    notification,
)

app = FastAPI(title="LingXi AI Learning Platform")
init_db()

# =========================
# CORS
# =========================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =========================
# routers
# =========================

app.include_router(auth.router, prefix="/api")
app.include_router(admin.router, prefix="/api")
app.include_router(plan.router, prefix="/api")
app.include_router(resource.router, prefix="/api")
app.include_router(chat.router, prefix="/api")
app.include_router(evaluation.router, prefix="/api")
app.include_router(todo.router, prefix="/api")
app.include_router(notification.router, prefix="/api")


@app.get("/")
async def root():
    return {
        "message": "LingXi Backend Running"
    }
