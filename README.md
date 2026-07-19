# LingXi-Backend 后端

灵析学伴后端项目，当前唯一课程主线是面向高校《数据结构与算法：可视化理解与代码实践》的个性化多模态学习系统。项目基于 FastAPI、SQLAlchemy 和 MySQL/SQLite，负责对话画像、多智能体编排、五类资源生成、AI 动态路线、学生自主路线与任务清单、练习评价和内容审核。

## 当前主线

- 课程主线：`《数据结构与算法》`
- 核心框架：12 个章节、123 个知识点，包含章节讲义、小节正文、练习题、代码任务、思维导图、视频指南与来源证据
- 学习主流程：学生自然语言输入 → 10 维动态画像 → 课程知识检索 → 5 步学习路径 → 5 类个性化资源 → 教师审核 → 练习评价与画像更新
- 双轨规划：AI 路线负责系统推荐；学生可新建自主路线、在路线中插入个人任务，并维护独立自主任务清单，两者共同进入规划执行画像和学习评价。
- 默认资源：课程讲解文档、知识点思维导图、练习题集、代码实验、个性化视频观看指南
- 资源体系：每类资源独立保存为 Artifact，学习路径通过 Artifact ID 绑定可点击资源
- 范围门禁：只有命中《数据结构与算法》课程图谱的主题才允许生成路径和资源；数据库、操作系统、计算机网络、外语、高数等其他课程主题默认进入课程外提示
- 质量闭环：内容安全分、教学质量分、证据完整性分开保存和展示，安全无风险不等于教学质量合格

## 主要目录

```text
app/
  agents/                  意图识别、画像、规划、资源生成等轻量 Agent
  models/                  SQLAlchemy 模型和数据库基础配置
  routers/                 FastAPI 路由
  services/
    data_services/         业务服务层
    llm_provider.py        讯飞星火调用封装
data/
  knowledge_base/data_structures_algorithms/
                            《数据结构与算法》12 章完整初始知识库
scripts/
  create_admin.py          从本地环境变量幂等创建/更新管理员
  seed_demo_data.py        演示基准数据脚本
  seed_dsa_course.py       同步《数据结构与算法》课程知识库
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

比赛正式主线统一使用讯飞星火：

```env
LINGXI_LLM_PROVIDER=spark
SPARK_API_URL=https://spark-api-open.xf-yun.com/x2/chat/completions
SPARK_MODEL=spark-x
SPARK_THINKING=disabled
SPARK_STREAM=true
SPARK_KEEP_ALIVE=true
SPARK_API_PASSWORD=APIKey:APISecret
LINGXI_TOKEN_SECRET=至少32字节的随机签名密钥
LINGXI_DEMO_ADMIN_PASSWORD=本地演示管理员密码
LINGXI_DEMO_STUDENT_PASSWORD=本地演示学生密码
```

如需查看模型调用摘要日志，可在 `.env` 中添加：

```env
LINGXI_DEBUG_LLM=1
```

## 演示数据

```bash
source .venv/bin/activate
python scripts/seed_dsa_course.py
python scripts/create_admin.py
```

脚本效果：

- `seed_dsa_course.py`：同步《数据结构与算法》课程、章节、知识点和初始学习资源。
- `create_admin.py`：从 `LINGXI_DEMO_ADMIN_PASSWORD` 读取本地密码，幂等创建或更新 `admin / role=admin`，不清空课程数据。真实口令不得写入页面、源码或提交文档。

## 数据结构与算法课程知识库

```bash
source .venv/bin/activate
python scripts/seed_dsa_course.py
```

课程资料位于：

```text
data/knowledge_base/data_structures_algorithms/
  course_manifest.json
  chapter_resource_index.json
  knowledge_units.jsonl
  source_references.json
  video_catalog.json
  courseware/
  labs/
  evidence/
```

## 默认生成的 5 类 Artifact

- 课程讲解文档
- 知识点思维导图
- 练习题集
- 代码实验
- 个性化视频观看指南

练习评价后可额外生成诊断与补弱报告；它不是普通对话的默认资源。

## 稳定演示用例

主演示只使用下面这条输入：

`我是计算机专业大二学生，学过数组和链表，但不理解动态规划的状态定义与转移方程，偏好图解和代码实践。请为我制定学习路径并生成配套资源。`

预期结果：定位到第 10 章动态规划，更新 10 维学生画像，生成 5 步路径和上述 5 类资源，并进入审核队列。

边界测试保留两条：

1. `比较 BFS 和 DFS`
   - 预期：`scope_level=comparison`，主题为 `BFS 与 DFS 对比学习`。
2. `我想学习数据库索引`
   - 预期：返回课程外提示：本系统聚焦《数据结构与算法》课程。

## 检查命令

```bash
PYTHONPYCACHEPREFIX=/private/tmp/lingxi_pycache .venv/bin/python -m unittest discover -s tests -p 'test_*.py' -v

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
- 大模型：比赛主线仅接入讯飞星火；真实访问凭证只放在本地 `.env`，不得提交到仓库。
