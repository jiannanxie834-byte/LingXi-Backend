# LingXi-Backend 后端

灵析学伴后端项目，定位为面向高校《深度学习》课程的个性化多模态资源生成与学习多智能体系统。项目基于 FastAPI、SQLAlchemy、MySQL 构建，负责用户、Artifact 资源工厂、学习规划、学习评价、聊天历史、多智能体编排、课程图谱和初始知识库同步。

## 当前主线

- 课程主线：`《深度学习》`
- 核心知识图谱：12 个章节、12 个知识单元，覆盖神经网络基础、反向传播、优化、正则化、CNN、RNN/LSTM/GRU、Transformer、生成模型、PyTorch 实践和课程项目
- 资源体系：不再把“总包型多模态资源”作为平级资源生成，而是生成多个具体 Artifact，再由主题学习包聚合展示
- 范围门禁：只有命中《深度学习》课程图谱的主题才允许生成路径和资源；其他学科或泛化计算机主题会进入课程外提示，不套用资源模板

## 主要目录

```text
app/
  agents/                  意图识别、画像、规划、资源生成等轻量 Agent
  models/                  SQLAlchemy 模型和数据库基础配置
  routers/                 FastAPI 路由
  services/
    data_services/         业务服务层
    llm_provider.py        DeepSeek / 讯飞星火调用封装，开发占位输出不用于正式演示
data/
  knowledge_base/deep_learning/
                            《深度学习》初始课程知识库、章节文档、公开视频目录和实验代码
scripts/
  seed_demo_data.py        演示基准数据重置脚本
  seed_deep_learning_course.py
                            同步《深度学习》课程知识库
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

## 深度学习课程知识库

```bash
source .venv/bin/activate
python scripts/seed_deep_learning_course.py
```

课程资料位于：

```text
data/knowledge_base/deep_learning/
  manifest.json
  knowledge_units.jsonl
  video_catalog.json
  references.json
  chapters/
  labs/
```

## 资源 Artifact 类型

新生成资源只允许使用以下 Artifact 类型：

- 课程讲解文档
- 知识点思维导图
- 练习题集
- 拓展阅读包
- PyTorch 实操案例
- PPT 大纲
- 外部公开视频推荐卡
- 个性化视频观看指南
- 交互动画规格
- 动画分镜
- 课程实践项目任务书
- 诊断与补弱报告

主题学习包是展示层聚合结构，不作为平级资源正文入库。
