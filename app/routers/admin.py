# app/routers/admin.py
from fastapi import APIRouter
from app.database import USERS_DB, FEEDBACK_DB, RESOURCES_DB

router = APIRouter(prefix="/admin", tags=["管理后台业务中心"])

# 1. 获取大盘 100% 动态计算的卡片数值
@router.get("/stats")
async def get_admin_stats():
    total_users = len(USERS_DB)
    total_resources = len(RESOURCES_DB)
    pending_resources = len([r for r in RESOURCES_DB if r["status"] == "待审核"])
    pending_feedback = len([f for f in FEEDBACK_DB if f["status"] == "待处理"])
    
    # 待办事件总数 = 待审核资源 + 待处理反馈
    todo_count = pending_resources + pending_feedback

    return {
        "code": 200,
        "message": "获取实时大盘成功",
        "data": [
            {"title": "全站注册总数", "value": f"{total_users} 人", "tag": "注册用户", "bgColor": "#e6f7ff", "color": "#1890ff"},
            {"title": "资源总储备", "value": f"{total_resources} 份", "tag": "多模态", "bgColor": "#f6ffed", "color": "#52c41a"},
            {"title": "待审核资源", "value": f"{pending_resources} 件", "tag": "安全合规", "bgColor": "#fff7e8", "color": "#fa8c16"},
            {"title": "待处理问题反馈", "value": f"{pending_feedback} 件", "tag": "待办", "bgColor": "#fff1f0", "color": "#f5222d"}
        ],
        "todoCount": todo_count
    }

# 2. 获取学生提交的反馈中心全量列表
@router.get("/feedback/list")
async def get_feedback_list():
    return {
        "code": 200,
        "message": "反馈数据加载成功",
        "data": FEEDBACK_DB
    }


# 3.  标记反馈为已处理接口 (将数据状态真正固化)
@router.post("/feedback/process")
async def process_feedback(feedback_id: str):
    for feedback in FEEDBACK_DB:
        if feedback["id"] == feedback_id:
            feedback["status"] = "已处理" # 状态翻转，大盘待办数会自动实时扣减 1
            print(f" 【系统流转】反馈单 [{feedback_id}] 已被管理员成功处理！")
            return {"code": 200, "message": "该用户反馈已成功标记为处理完成！"}
            
    return {"code": 400, "message": "未找到对应的反馈单号"}