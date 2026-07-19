from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from app.database import init_db
from app.services.security_service import verify_access_token

from app.routers import (
    auth,
    admin,
    plan,
    resource,
    chat,
    evaluation,
    todo,
    notification,
    course,
    profile,
    generation,
    video,
    exercise,
)

app = FastAPI(title="LingXi AI Learning Platform")
init_db()
STATIC_DIR = Path(__file__).resolve().parents[1] / "static"
app.mount("/media", StaticFiles(directory=str(STATIC_DIR)), name="media")

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


PUBLIC_API_PATHS = {
    "/api/user/login",
    "/api/user/register",
}


@app.middleware("http")
async def authenticate_api_request(request: Request, call_next):
    path = request.url.path
    if request.method == "OPTIONS" or not path.startswith("/api/") or path in PUBLIC_API_PATHS:
        return await call_next(request)

    authorization = request.headers.get("Authorization", "")
    scheme, _, token = authorization.partition(" ")
    claims = verify_access_token(token) if scheme.lower() == "bearer" else {}
    if not claims:
        return JSONResponse(status_code=401, content={"code": 401, "message": "登录状态已失效，请重新登录"})
    if path.startswith("/api/admin/") and claims.get("role") != "admin":
        return JSONResponse(status_code=403, content={"code": 403, "message": "需要管理员权限"})

    request.state.auth = claims
    return await call_next(request)

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
app.include_router(course.router, prefix="/api")
app.include_router(profile.router, prefix="/api")
app.include_router(generation.router, prefix="/api")
app.include_router(video.router, prefix="/api")
app.include_router(exercise.router, prefix="/api")


@app.get("/")
async def root():
    return {
        "message": "LingXi Backend Running"
    }


@app.get("/health")
async def health():
    return {"status": "ok"}
