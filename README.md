# LingXi-Backend 后端

灵析学伴后端项目，定位为面向高校《深度学习》课程的个性化多模态资源生成与学习多智能体系统。项目基于 FastAPI、SQLAlchemy、MySQL 构建，负责用户、Artifact 资源工厂、学习规划、学习评价、聊天历史、多智能体编排、课程图谱和初始知识库同步。

## 当前主线

- 课程主线：`《深度学习》`
- 核心知识图谱：12 个章节、70+ 细粒度知识单元，覆盖数学前置、神经网络基础、反向传播、优化、正则化、CNN、RNN/LSTM/GRU、Attention/Transformer、生成模型、PyTorch 实践和课程项目
- 资源体系：不再把“总包型多模态资源”作为平级资源生成，而是生成多个具体 Artifact，再由主题学习包聚合展示
- 范围门禁：只有命中《深度学习》课程图谱的主题才允许生成路径和资源；其他学科或泛化计算机主题会进入课程外提示，不套用资源模板
- 质量闭环：内容安全分、教学质量分、证据完整性分开保存和展示，安全无风险不等于教学质量合格

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
  create_admin.py          幂等创建/更新管理员 admin / 123456
  seed_demo_data.py        兼容旧入口的演示基准数据重置脚本
  seed_deep_learning_demo_data.py
                            深度学习演示数据初始化脚本
  seed_deep_learning_course.py
                            同步《深度学习》课程知识库
```

## 分支

```bash
git checkout feature/deep-learning-agent
```

## 安装与运行

macOS 上如果 `python` 不存在，使用 `python3`：

```bash
python3 -m venv .venv
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
python scripts/seed_deep_learning_course.py
python scripts/create_admin.py
python scripts/seed_deep_learning_demo_data.py
```

脚本效果：

- `seed_deep_learning_course.py`：同步《深度学习》课程知识库、章节、知识单元和实验资源。
- `create_admin.py`：幂等创建或更新 `admin / 123456 / role=admin`，不清空课程数据。
- `seed_deep_learning_demo_data.py`：写入演示学生、画像、路线、评价、反馈、资源和聊天历史；只重置演示范围数据。

## 深度学习课程知识库

```bash
source .venv/bin/activate
python scripts/seed_deep_learning_course.py
```

课程资料位于：

```text
data/knowledge_base/deep_learning/
  course_manifest.json
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

## 稳定演示用例

建议按以下三条学生端输入演示：

1. `我是大二学生，学过一点机器学习，但是反向传播和 CNN 不太懂，想两周内做一个图像分类项目，比较喜欢图解和代码。`
   - 预期：识别 CNN、反向传播、PyTorch 项目；更新画像；生成两周路线；进入 Artifact 生成任务。
2. `我想学习 LSTM`
   - 预期：`scope_level=unit`，主题保持为 `LSTM 长短期记忆网络`；RNN 作为前置，GRU 作为对比拓展；生成讲义、导图、题集、代码实验和 LSTM 门控动画规格。
3. `我做 CNN 练习题时总是算错输出特征图尺寸。`
   - 预期：命中 `dl_cnn_output_size`；更新薄弱点；路线插入补弱节点；生成输出尺寸讲解、题集、卷积滑窗动画和错因建议。

## 检查命令

```bash
PYTHONPYCACHEPREFIX=/private/tmp/lingxi_pycache .venv/bin/python -m unittest \
  tests.test_topic_scope_resolver \
  tests.test_deep_learning_course_map \
  tests.test_teaching_quality_gate \
  tests.test_plan_resource_binding \
  tests.test_resource_artifact_generation

PYTHONPYCACHEPREFIX=/private/tmp/lingxi_pycache .venv/bin/python -m compileall app tests
```

前端在 `../LingXi-Agent` 中执行：

```bash
npm install
npm run build
npm run dev
```

## AI Coding 与开源工具说明

- AI Coding：开发过程中使用 Codex 辅助代码阅读、重构、测试和文档整理；关键实现仍需人工确认、运行测试并审核提交。
- 后端：FastAPI、SQLAlchemy、Uvicorn、PyMySQL，遵循各自开源协议。
- 前端：Vue、Vite、Element Plus、Mermaid/Markdown 渲染相关依赖，遵循各自开源协议。
- 大模型：通过配置接入 DeepSeek 或讯飞星火；真实 API Key 只放在本地 `.env`，不得提交到仓库。
