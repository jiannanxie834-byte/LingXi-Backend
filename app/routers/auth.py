# app/routers/auth.py
from fastapi import APIRouter
from pydantic import BaseModel
# 从统一数据层导入全局唯一的数据库实例
from app.database import USERS_DB 

router = APIRouter(prefix="/user", tags=["用户鉴权中心"])

# --- Pydantic 数据模型定义 ---
class LoginRequest(BaseModel):
    username: str
    password: str

class RegisterRequest(BaseModel):
    username: str
    password: str

# ================= 1. 登录接口 (与前端 Pinia + 路由守卫完美对齐) =================
@router.post("/login")
async def login(data: LoginRequest):
    username = data.username
    password = data.password

    # 1. 检查用户是否存在
    if username not in USERS_DB:
        return {"code": 400, "message": "用户不存在，请先注册！", "data": None}
    
    # 2. 校验密码是否正确
    if USERS_DB[username]["password"] != password:
        return {"code": 400, "message": "密码错误，请重新输入", "data": None}

    # 3. 登录成功，打包前端需要的全量画像状态，让 Pinia 一键收纳
    user_info = USERS_DB[username]
    return {
        "code": 200,
        "message": "登录成功",
        "data": {
            "token": f"Bearer token-for-{username}",
            "role": user_info["role"],
            "username": username,
            "avatar": user_info.get("avatar", ""),
            "tags": user_info.get("tags", []),
            #  吐出活的个签数据，支持前端无缝渲染和修改
            "bio": user_info.get("bio", "这个人十分神秘什么都没留下哟") 
        }
    }

# ================= 2. 注册接口 (新用户完美初始化空状态) =================
@router.post("/register")
async def register(data: RegisterRequest):
    username = data.username
    password = data.password

    if username in USERS_DB:
        return {"code": 400, "message": "该账号已被占用，请换一个吧", "data": None}

    # 注册新学生，为其初始化完全标准但空空如也的画像结构
    # 这样新用户登录切到“我的”页面时，骨架完美支撑，但会触发精美的空提示
    USERS_DB[username] = {
        "password": password,
        "role": "student",
        "avatar": "",
        "tags": [], # 初始标签为空，等待 AI 对话生成后填入
        "bio": "这个人十分神秘什么都没留下哟", #  新用户默认个签
        "hours": 0 # 累计学习时间归零
    }
    
    print(f" 新用户 [{username}] 注册成功并安全入库！当前内存总用户数: {len(USERS_DB)}")
    return {"code": 200, "message": "注册成功，快去登录吧！", "data": None}

from app.database import FEEDBACK_DB #  确保文件顶部或者这里导入了 FEEDBACK_DB
from datetime import datetime

# --- 1. 定义反馈提交的数据模型 ---
class FeedbackRequest(BaseModel):
    username: str
    content: str

# --- 2. 接收学生反馈接口 (打通管理员大盘的终极纽带) ---
@router.post("/feedback/submit")
async def submit_feedback(data: FeedbackRequest):
    # 动态生成反馈 ID（例如当前长度加 1 补零）
    new_id = f"FB{len(FEEDBACK_DB) + 1:03d}"
    # 自动获取当前真实的年月日（2026年）
    current_date = datetime.now().strftime("%Y-%m-%d")
    
    # 组装一条标准的全真反馈记录
    new_item = {
        "id": new_id,
        "username": data.username,
        "content": data.content,
        "status": "待处理", # 初始状态为待处理，会立刻让管理员待办数加 1
        "date": current_date
    }
    
    # 追加进全局唯一的内存数据库
    FEEDBACK_DB.append(new_item)
    
    print(f" 【系统流转】收到学生 [{data.username}] 的反馈！当前大盘总反馈数: {len(FEEDBACK_DB)}")
    # 显式加上 "data": None，完美对齐前端解包拦截器
    return {
        "code": 200, 
        "message": "反馈提交成功！系统已实时呈递给最高管理员。",
        "data": None 
    }
