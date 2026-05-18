# app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
# 1. 引入拆分好的三个模块
from app.routers import auth, admin, plan

app = FastAPI(title="灵析学伴全栈全真内核系统")

# 解决跨域
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

#  2. 统一挂载到 /api 前缀下
app.include_router(auth.router, prefix="/api")
app.include_router(admin.router, prefix="/api")
app.include_router(plan.router, prefix="/api")

@app.get("/")
async def root():
    return {"status": "online", "message": "灵析学伴大楼运行良好，各模块通电正常！"}