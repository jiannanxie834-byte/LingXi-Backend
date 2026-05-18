# app/database.py

# 1. 用户账密与全息画像库
USERS_DB = {
    "admin": {
        "password": "123456", 
        "role": "admin", 
        "avatar": "", 
        "tags": ["掌控全局"], 
        "bio": "系统最高管理员",
        "hours": 0
    },
    "student": {
        "password": "123456", 
        "role": "student", 
        "avatar": "https://api.dicebear.com/7.x/avataaars/svg?seed=Felix", 
        "tags": ["大二", "前端方向", "深度学习热粉"], 
        "bio": "“路漫漫其修远兮，吾将上下而求索。”",
        "hours": 42
    }
}

# 2.  问题反馈中心模拟库
FEEDBACK_DB = [
    {"id": "FB001", "username": "student", "content": "智能规划的节点数量建议能自由调控，现在有点多。", "status": "待处理", "date": "2026-05-15"},
    {"id": "FB002", "username": "student", "content": "多模态资源库里的视频加载偶尔有点卡顿。", "status": "已处理", "date": "2026-05-16"}
]

# 3.  多模态资源储备库
RESOURCES_DB = [
    {"id": "RES001", "title": "Vue3 组合式 API 核心进阶演练", "type": "视频", "status": "已通过"},
    {"id": "RES002", "title": "讯飞星火大模型 Agent 开发实战手册.pdf", "type": "文档", "status": "待审核"},
    {"id": "RES003", "title": "PyTorch 神经网络结构可视化工具", "type": "工具", "status": "待审核"}
]

# 4.  智能学习规划路线库 (你死守的核心：支持物理整条线删除与单节点剥离)
PLANS_DB = {
    "student": [
        {
            "id": "route_vue3_001",
            "title": "Vue3 前端现代化全栈攻坚路线",
            "nodes": [
                {"id": 101, "name": "Pinia 状态机与 Session 级会话存储安全解耦"},
                {"id": 102, "name": "Vue Router 路由导航死锁与全局守卫防爆机制"},
                {"id": 103, "name": "Axios 拦截器全真数据吞吐网络层搭建"}
            ]
        }
    ]
}