from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import auth

app = FastAPI(title="灵析学伴 API Hub", version="1.0.0")

# 核心安全配置：允许进行跨域访问
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"], # 允许前端的源
    allow_credentials=True,
    allow_methods=["*"], # 允许所有 HTTP 方法 (GET, POST 等)
    allow_headers=["*"], # 允许所有请求头
)

# 🌐 注册业务模块路由，统一加 /api 前缀，完美对接前端 utils/request.js
app.include_router(auth.router, prefix="/api")

@app.get("/")
async def root():
    return {"message": "灵析学伴 Python 后端服务已成功启动！🚀"}