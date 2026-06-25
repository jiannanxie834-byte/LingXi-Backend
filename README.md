# LingXi-Backend 后端

灵析学伴后端项目，基于 FastAPI、SQLAlchemy、MySQL 构建，负责用户、资源、学习规划、学习评价、聊天历史、多智能体编排和课程知识库同步。

## 主要目录

```text
app/
  agents/                  意图识别、画像、规划、资源生成等轻量 Agent
  models/                  SQLAlchemy 模型和数据库基础配置
  routers/                 FastAPI 路由
  services/
    data_services/         业务服务层
    llm_provider.py        DeepSeek / 讯飞星火 / 本地兜底调用封装
data/
  knowledge_base/          人工智能初始课程知识库
scripts/
  seed_demo_data.py        演示基准数据重置脚本
```

## 运行

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

也可以使用：

```bash
python run.py
```

## 数据库

`.env` 中配置：

```env
DATABASE_URL=mysql+pymysql://root@127.0.0.1:3306/lingxi?charset=utf8mb4
```

`lingxi.db` 是早期 SQLite 本地测试文件，不作为当前演示数据源，不建议提交。

## 大模型配置

DeepSeek：

```env
LINGXI_LLM_PROVIDER=deepseek
DEEPSEEK_API_URL=https://api.deepseek.com/chat/completions
DEEPSEEK_MODEL=deepseek-v4-pro
DEEPSEEK_API_KEY=你的Key
```

讯飞星火：

```env
LINGXI_LLM_PROVIDER=spark
SPARK_API_URL=https://spark-api-open.xf-yun.com/v1/chat/completions
SPARK_MODEL=lite
SPARK_API_PASSWORD=APIKey:APISecret
```

如需查看模型调用摘要日志，可在 `.env` 中添加：

```env
LINGXI_DEBUG_LLM=1
```

## 演示数据

```bash
source .venv/bin/activate
python scripts/seed_demo_data.py
```

该脚本会恢复适合演示的用户、资源、反馈、评价和聊天历史。
