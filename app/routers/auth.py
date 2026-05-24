from fastapi import APIRouter
from typing import Any, Union
import app.services.db_service as db_service

router = APIRouter()

# ================= 1. 登录校验（融合大前端导航守卫双重保险） =================
@router.post("/user/login")
async def login(data: Union[dict, Any]):
    """
    用户/管理员登录接口
    已经通过主入口 main.py 统一挂载了 /api 前缀，实际请求路径为: /api/user/login
    """
    # 自动兼容 Pydantic 模型对象或原生 dict 字典传参
    username = data.username if hasattr(data, "username") else data.get("username")
    password = data.password if hasattr(data, "password") else data.get("password")
    
    # 调用底层 SQLAlchemy 查真数据库 lingxi.db
    result = db_service.check_user_login(username, password)
    
    if result["success"]:
        user_info = result["data"]
        
        return {
            "code": 200,
            "message": "登录成功，鉴权令牌刻录完成",
            "token": f"lingxi_{user_info['username']}",
            
            # 层级一：标准 Axios 响应结构 (res.data.data.xxx)
            "data": user_info,
            
            # 层级二：降维直出扁平结构，无缝兼容老的前端 Mock 依赖 (res.role / res.username)
            "username": user_info["username"],
            "role": user_info["role"],
            "avatar": user_info["avatar"],
            "bio": user_info["bio"],
            "hours": user_info["hours"],
            "tags": user_info["tags"]
        }
        
    # 登录失败，返回 400 状态码及错误话术
    return {"code": 400, "message": result["message"]}


# ================= 1.5 新用户注册 =================
@router.post("/user/register")
async def register(data: Union[dict, Any]):
    """
    普通学生注册接口
    实际请求路径为: /api/user/register
    """
    username = data.username if hasattr(data, "username") else data.get("username")
    password = data.password if hasattr(data, "password") else data.get("password")

    if not username or not password:
        return {"code": 400, "message": "账号和密码不能为空"}

    result = db_service.create_user(username, password)
    if result["success"]:
        return {"code": 200, "message": "注册成功", "data": result["data"]}
    return {"code": 400, "message": result["message"]}


# ================= 2. 问题反馈中心提交（SQL 物理刻录） =================
@router.post("/user/feedback/submit")
async def submit_feedback(data: Union[dict, Any]):
    """
    学生前台：提交反馈意见
    实际请求路径为: /api/user/feedback/submit
    """
    username = data.username if hasattr(data, "username") else data.get("username")
    content = data.content if hasattr(data, "content") else data.get("content")
    
    # 安全调用中台写入真数据库表
    success = db_service.insert_feedback(username, content)
    if success:
        return {"code": 200, "message": "反馈提交成功，已物理实时送达超级管理员中枢"}
    return {"code": 500, "message": "反馈物理写入失败，请检查 sqlite 链路"}


# ================= 3. 用户个性资料修改（实时同步更新） =================
@router.put("/user/profile/update")
async def update_profile(data: Union[dict, Any]):
    """
    学生/管理员：修改个性签名（bio）或更换头像（avatar）
    实际请求路径为: /api/user/profile/update
    """
    username = data.username if hasattr(data, "username") else data.get("username")
    bio = data.bio if hasattr(data, "bio") else data.get("bio")
    avatar = data.avatar if hasattr(data, "avatar") else data.get("avatar", "")
    password = data.password if hasattr(data, "password") else data.get("password", "")

    # 执行真数据库物理字段修改
    success = db_service.update_user_profile(username, bio, avatar, password)
    if success:
        # 修改成功后，立刻重新从数据库中捞取最新全量数据，反哺前端 Pinia，实现无缝无刷新变动
        updated_user = db_service.get_user_by_username(username)
        return {
            "code": 200, 
            "message": "个人资料全真刻录同步成功",
            "data": {
                "username": updated_user.username,
                "role": updated_user.role,
                "bio": updated_user.bio,
                "avatar": updated_user.avatar,
                "hours": updated_user.hours,
                "tags": [t for t in updated_user.tags.split(",") if t] if updated_user.tags else []
            }
        }
    return {"code": 500, "message": "资料更新物理保存失败"}
