from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter()

#  模拟后端不可更改的“核心数据库”
# 预置了初始的管理员和测试学生，并且预留了他们后续要同步给 AI 的画像数据空间
USERS_DB = {
    "admin": {
        "password": "123456", 
        "role": "admin", 
        "profile": {"direction": "全栈管理", "hours": 0}
    },
    "student": {
        "password": "123456", 
        "role": "student", 
        "profile": {"direction": "Vue3前端攻坚", "hours": 42}
    }
}

# --- Pydantic 数据模型定义 ---
class LoginRequest(BaseModel):
    username: str
    password: str

class RegisterRequest(BaseModel):
    username: str
    password: str

# =================  1. 登录接口 (带真实账密比对) =================
@router.post("/user/login")
async def login(data: LoginRequest):
    username = data.username
    password = data.password

    # 检查用户是否存在
    if username not in USERS_DB:
        return {"code": 400, "message": "用户不存在，请先注册！", "data": None}
    
    # 校验密码是否正确
    if USERS_DB[username]["password"] != password:
        return {"code": 400, "message": "密码错误，请重新输入", "data": None}

    # 登录成功，颁发 Token 并返回角色
    role = USERS_DB[username]["role"]
    return {
        "code": 200,
        "message": "登录成功",
        "data": {
            "token": f"Bearer token-for-{username}", # 护照里夹带了用户名
            "role": role,
            "username": username
        }
    }

# =================  2. 注册接口 (新用户入库) =================
@router.post("/user/register")
async def register(data: RegisterRequest):
    username = data.username
    password = data.password

    if username in USERS_DB:
        return {"code": 400, "message": "该账号已被占用，请换一个吧", "data": None}

    # 注册新用户，默认身份是学生(student)，并初始化他独立的空画像数据
    USERS_DB[username] = {
        "password": password,
        "role": "student",
        "profile": {"direction": "未设置", "hours": 0} # 不同用户间的数据在这里天然隔离
    }
    
    print(f"🎉 新用户注册成功并安全入库！当前总用户数: {len(USERS_DB)}")
    return {"code": 200, "message": "注册成功，快去登录吧！", "data": None}