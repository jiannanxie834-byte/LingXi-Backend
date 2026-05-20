from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
# 1. 引入拆分好的模块
from app.routers import auth, admin, plan, resource

# 把 base 里的三个宝贝合在一行引入，绝不重复
from app.models.base import engine, Base, init_seeding_data 
import app.models.schemas as schemas  

app = FastAPI()

# 1. 自动在真数据库（SQLite）里把所有的表创建出来
Base.metadata.create_all(bind=engine)

# 2.  紧接着触发自动注入默认学生与管理员的种子数据
init_seeding_data()
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
app.include_router(resource.router, prefix="/api")

@app.get("/")
async def root():
    return {"status": "online", "message": "运行正常"}
