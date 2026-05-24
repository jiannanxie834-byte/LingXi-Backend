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
    {"id": "FB002", "username": "student", "content": "错题诊断报告里的复习建议希望能更具体一些。", "status": "已处理", "date": "2026-05-16"}
]

# 3.  知识资源储备库
RESOURCES_DB = [
    {"id": "RES001", "title": "Vue3 组合式 API 核心进阶演练", "type": "代码类实操案例", "status": "已通过"},
    {"id": "RES002", "title": "讯飞星火大模型 Agent 开发实战手册.pdf", "type": "文档", "status": "待审核"},
    {"id": "RES003", "title": "PyTorch 神经网络结构可视化工具", "type": "工具", "status": "待审核"}
]

# 4. 智能学习规划路线库
PLANS_DB = {
    "student": [
        {
            "id": "route_vue3_001",
            "title": "Vue3 高级实战路线 (AI 专属定制)",
            "isCollapsed": False,
            "isAiGenerated": True,
            "tasks": [
                { "id": 101, "title": "Vue3 组合式 API 入门", "desc": "掌握 setup, ref, reactive 等核心响应式函数。", "status": "completed", "isCustom": False, "resources": ["Vue3 官方文档"] },
                { "id": 102, "title": "深度理解生命周期与 Watcher", "desc": "分析 Hook 调用时机及侦听器高级用法。", "status": "active", "isCustom": False, "resources": ["生命周期流程图"] },
                { "id": 103, "title": "Vue-Router 与 Pinia 进阶", "desc": "单页面应用的路由管理及全局状态管理。", "status": "pending", "isCustom": False, "resources": [] }
            ]
        },
        {
            "id": "route_net_002",
            "title": "计算机网络体系复习冲刺",
            "isCollapsed": True,
            "isAiGenerated": False,
            "tasks": [
                { "id": 201, "title": "TCP/IP 五层模型概述", "desc": "理清物理层到应用层的基本职责。", "status": "completed", "isCustom": False, "resources": [] },
                { "id": 202, "title": "三次握手与四次挥手详解", "desc": "核心常考点，理解状态转移图。", "status": "pending", "isCustom": False, "resources": ["抓包实操案例"] }
            ]
        }
    ]
}

# 5.  动态知识库分类标签库（支持学生申请、管理员审核、全站动态增加）
RESOURCE_TYPES_DB = [
    {"name": "专业课程讲解文档", "status": "已通过"},
    {"name": "知识点思维导图", "status": "已通过"},
    {"name": "不同类型练习题目", "status": "已通过"},
    {"name": "拓展阅读材料", "status": "已通过"},
    {"name": "错题诊断与学习反馈报告", "status": "已通过"},
    {"name": "代码类实操案例", "status": "已通过"}
]
