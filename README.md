# LingXi-Backend 后端

灵析学伴后端项目，当前主线定位为面向高校《数据结构与算法：可视化理解与代码实践》课程的个性化多模态学习系统。项目基于 FastAPI、SQLAlchemy、MySQL 构建，负责用户、Artifact 资源工厂、学习规划、学习评价、聊天历史、多智能体编排、课程图谱和初始知识库同步。

## 当前主线

- 课程主线：`《数据结构与算法》`
- 核心框架：12 个章节、80 个知识单元骨架，覆盖复杂度分析、线性结构、递归分治回溯、排序查找、哈希堆、树图、最短路径、贪心、动态规划、字符串算法和综合项目
- 当前阶段：课程框架迁移阶段，只包含章节入口、知识单元 schema 和占位资源，不包含正式课程正文、题库或代码实验
- 资源体系：不再把“总包型多模态资源”作为平级资源生成，而是生成多个具体 Artifact，再由主题学习包聚合展示
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
    llm_provider.py        DeepSeek / 讯飞星火调用封装，开发占位输出不用于正式演示
data/
  knowledge_base/data_structures_algorithms/
                            《数据结构与算法》课程框架、12 章章节入口和知识单元骨架
scripts/
  create_admin.py          幂等创建/更新管理员 admin / 123456
  seed_demo_data.py        兼容旧入口的演示基准数据重置脚本
  seed_dsa_course.py         同步《数据结构与算法》课程框架占位资源
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
python scripts/seed_dsa_course.py
python scripts/create_admin.py
```

脚本效果：

- `seed_dsa_course.py`：同步《数据结构与算法》课程框架、章节、知识单元骨架和占位资源。
- `create_admin.py`：幂等创建或更新 `admin / 123456 / role=admin`，不清空课程数据。

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

## 资源 Artifact 类型

新生成资源只允许使用以下 Artifact 类型：

- 课程讲解文档
- 知识点思维导图
- 练习题集
- 拓展阅读包
- 代码实验
- PPT 大纲
- 外部公开视频推荐卡
- 个性化视频观看指南
- 算法可视化动画规格
- 动画分镜
- 算法项目任务书
- 诊断与补弱报告

主题学习包是展示层聚合结构，不作为平级资源正文入库。

## 稳定演示用例

当前阶段建议按以下输入验证课程边界和框架路由：

1. `我想学习数据结构与算法`
   - 预期：`scope_level=course`，只生成课程导学、诊断和学习路径，不一次性铺开全部章节资源。
2. `比较 BFS 和 DFS`
   - 预期：`scope_level=comparison`，主题为 `BFS 与 DFS 对比学习`。
3. `我想学习数据库索引`
   - 预期：返回课程外提示：本系统聚焦《数据结构与算法》课程。

## 检查命令

```bash
PYTHONPYCACHEPREFIX=/private/tmp/lingxi_pycache .venv/bin/python -m unittest \
  tests.test_dsa_course_map \
  tests.test_dsa_scope_resolver \
  tests.test_dsa_seed_framework

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
