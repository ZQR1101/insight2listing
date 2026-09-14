<p align="center">
  <strong>Insight2Listing</strong>
</p>

<p align="center">
  面向 Amazon 美国站的「有据可查」市场洞察、选品验证与智能 Listing 工作流
</p>

<p align="center">
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-MIT-green.svg?style=flat-square" alt="License: MIT"/></a>
  <a href="https://github.com/ZQR1101/insight2listing/stargazers"><img src="https://img.shields.io/github/stars/ZQR1101/insight2listing?style=flat-square" alt="Stars"/></a>
  <br/>
  <img src="https://img.shields.io/badge/Python-3.12-3776AB?style=flat-square&logo=python&logoColor=white" alt="Python"/>
  <img src="https://img.shields.io/badge/FastAPI-0.14-009688?style=flat-square&logo=fastapi&logoColor=white" alt="FastAPI"/>
  <img src="https://img.shields.io/badge/PostgreSQL-16-4169E1?style=flat-square&logo=postgresql&logoColor=white" alt="PostgreSQL"/>
  <img src="https://img.shields.io/badge/SQLAlchemy-2.0-D71F00?style=flat-square&logo=sqlalchemy&logoColor=white" alt="SQLAlchemy"/>
  <img src="https://img.shields.io/badge/Next.js-15-black?style=flat-square&logo=next.js" alt="Next.js"/>
  <img src="https://img.shields.io/badge/React-19-61DAFB?style=flat-square&logo=react&logoColor=white" alt="React"/>
  <img src="https://img.shields.io/badge/Docker-Compose-2496ED?style=flat-square&logo=docker&logoColor=white" alt="Docker"/>
  <img src="https://img.shields.io/badge/CI-GitHub_Actions-2088FF?style=flat-square&logo=githubactions&logoColor=white" alt="CI"/>
</p>

<p align="center">
  <a href="./README.md">English</a> | <a href="./README.zh-CN.md">简体中文</a>
  <br/>
  <a href="#-overview">概览</a> · <a href="#-quick-start">快速开始</a> · <a href="#-features">功能</a> · <a href="#-project-structure">项目结构</a> · <a href="#-roadmap">路线图</a> · <a href="#-license">许可</a>
</p>

---

## 📋 这是什么？

Insight2Listing 把零散的评论、竞品数据与经过确认的商品事实，转化为面向 **Amazon 美国站**结构化、可审计的 Listing 工作流。它是一套**工作流优先**的系统——聊天只是辅助，绝不取代结构化数据。它的核心承诺只有一句话：

> **Listing 里的每一条洞察和声明都能追溯到来源。系统绝不编造事实。**

候选商品与市场数据会经过一条「有据可查」的管线：

```text
商品与市场数据
      ↓
数据校验与来源记录
      ↓
评论洞察与竞品缺口
      ↓
商品机会卡
      ↓
人工确认商品事实
      ↓
Listing 与视觉素材生成
      ↓
事实、图片与平台规则检查
      ↓
人工审核与导出
```

**当前里程碑：** 后端与数据导入管线已经实现并通过测试；评论洞察、Listing 生成、视觉素材与 Web 界面是后续里程碑（见[路线图](#-roadmap)）。

### 核心亮点

- **证据优先于文案** —— 每条痛点、关键词和卖点都带来源引用
- **事实隔离** —— 系统严格区分 *事实 / 推断 / 建议*，绝不会把未确认的能力写进 Listing
- **三格式导入** —— CSV、JSON、XLSX 统一走「适配器 + 规范化 Schema」
- **幂等且安全** —— 确定性去重 + 电子表格公式注入防护
- **自托管优先、托管就绪** —— Docker Compose、BYOK 模型、工作空间隔离
- **模型无关** —— 文本 / 嵌入 / 图片 Provider 均可替换

---

> [!TIP]
> ### 🔑 自备密钥（BYOK）
>
> Insight2Listing 采用 BYOK：你使用自己的模型 API Key——本里程碑没有云端托管、没有后台运行时，数据只留在你的环境里。API Key 只由后端读取，绝不进入浏览器或日志。
>
> 系统也诚实交代边界：**不**抓取 Amazon 网页、**不**承诺选出爆款、**不**自动发布任何商品；Listing 主图必须基于真实商品照片。

---

## 🚀 快速开始

### 前置要求

- [uv](https://docs.astral.sh/uv/) —— Python 工具链
- Docker —— 本地数据库

### 1. 启动基础设施

```powershell
Copy-Item .env.example .env
docker compose up -d postgres minio redis
```

Postgres 宿主端口默认是 `5050`，避免与本地其他库冲突；`.env.example` 里的 `DATABASE_URL` 已指向它——如想换端口请一并修改。

### 2. 启动后端 API

```bash
cd apps/api
uv sync
uv run alembic upgrade head     # 应用数据库迁移
uv run python run.py            # http://localhost:8000  （OpenAPI 文档在 /docs）
```

> 🪟 **Windows 注意：** `run.py` 会用一个 SelectorEventLoop 启动 uvicorn，因为 psycopg 异步驱动不支持 Windows 默认的 ProactorEventLoop；在 Windows 上建议用它而不是 `uvicorn app.main:app`。

### 3. 运行测试、lint 与类型检查

```bash
cd apps/api
uv run pytest                   # 需要 Postgres 容器在运行
uv run ruff check src tests
uv run mypy src
```

测试套件会根据 `DATABASE_URL` 自动创建独立的 `insight2listing_test` 库，并在每个用例间清空数据表，绝不触碰应用数据。

### 4. 用容器跑整套应用

```bash
docker compose up --build api
```

`api` 服务在启动时自动执行 Alembic 迁移，然后对外提供服务。

---

## ✨ 功能

### 已实现 · 后端与数据导入

| 能力 | 说明 |
| --- | --- |
| **项目** | 工作空间、项目与工作流状态机（`DRAFT → DATA_IMPORTED → … → EXPORTED`） |
| **数据导入** | CSV / JSON / XLSX 适配器、字段自动映射（含同义词与币种后缀兜底）、预览、导入报告 |
| **校验** | 字段转换、必填校验、行级错误定位、按 external id / 标题 / 内容哈希去重 |
| **安全** | 公式注入转义；API Key 只在后端；创建 / 状态变更 / 导入事件审计日志 |
| **可追溯** | `SourceRecord` 记录来源、许可、观察时间与载荷哈希；字段级新鲜度元数据 |
| **模型 Provider** | 可替换的 `文本洞察 / 嵌入 / 图片 / 审核` 接口 + Mock 实现（可离线运行） |
| **质量闸门** | CI 运行 ruff、mypy、测试（Postgres 服务）以及「迁移 vs 模型」一致性检查 |

### 规划中 · 后续里程碑

| 能力 | 方向 |
| --- | --- |
| **评论洞察** | 清洗 → 主题与情感 → 语义聚类 → 跨竞品合并 → 证据绑定 |
| **商品机会卡** | 加权评分、置信度、缺失维度、评分版本化 |
| **Listing 工作台** | 标题 / 五点 / 描述 / 搜索词生成、版本管理、事实与规则检查 |
| **视觉素材** | 真实商品图编辑 + GPT Image 2、确定性文字排版、一致性检查 |
| **Web 界面** | 工作流优先的 Next.js 界面，聊天作为辅助 |
| **Amazon SP-API** | 官方连接器 + 卖家 OAuth（后续 Beta 阶段） |

---

## 💡 使用场景

> *"为什么买家老在吐槽收纳袋的拉链？"*

> *"在把卖点写进 Listing 之前，有哪些评论能支持这条卖点？"*

> *"把这些确认过的商品事实翻译成英文标题、五点和搜索词——不要编造功能。"*

首批测试商品——压缩旅行收纳袋、玻璃喷油壶、车载垃圾桶——用于验证跨品类能力与评测质量，不构成商业投资建议。

---

## 🔧 项目结构

```
insight2listing/
├── apps/
│   ├── api/                     # FastAPI 后端  （当前开发中的仓库主体）
│   │   ├── src/app/
│   │   │   ├── api/             #   REST 端点（health、projects、imports、products、reviews）
│   │   │   ├── core/            #   配置、数据库引擎、枚举、安全防护
│   │   │   ├── models/          #   SQLAlchemy 模型（项目、商品、评论、来源、审计）
│   │   │   ├── schemas/         #   Pydantic API Schema
│   │   │   ├── ingestion/       #   CSV/JSON/XLSX 适配器 → 映射 → 规范化 → 去重 → 导入
│   │   │   ├── providers/       #   可替换的模型 Provider 接口 + Mock
│   │   │   └── audit/           #   审计事件日志
│   │   ├── alembic/             #   数据库迁移
│   │   ├── tests/               #   pytest 测试套件
│   │   └── run.py               #   面向 Windows 的开发服务器启动脚本
│   ├── web/                     # Next.js 前端（尚未实现）
│   └── worker/                  # 后台任务 Worker（尚未实现）
├── packages/
│   ├── schemas/ ui/ i18n/ rules/ prompts/ evals/   # 共享包（规划中）
├── examples/synthetic-data/     # 仅存放明确标注的合成数据
├── docs/                        # 架构、API、数据来源与评测文档
├── .github/workflows/           # CI：lint、typecheck、测试、迁移
├── outputs/                     # 产品与技术基线文档
├── docker-compose.yml
└── LICENSE
```

### 关键架构

- **模块化 FastAPI**（`apps/api`）——模块化单体；导入、项目、商品、评论、来源、Provider 与审计各自独立，统一暴露在版本化的 `/api/v1` 之下
- **统一导入 Schema**——适配器只负责解析格式；业务逻辑只读统一的规范化 Schema（含新鲜度与许可元数据）
- **审计追踪**——生成 / 编辑 / 确认 / 导出动作均被记录，下游声明可归因
- **Provider 接缝**——文本、嵌入、图片、审核模型均可替换，业务逻辑不与任何厂商绑定

### 数据与证据原则

- **事实 / 推断 / 建议**严格区分；未经确认的属性绝不会写成既有能力（§11）
- **公式注入**在导入时被中和——`=`/`+`/`-`/`@`/Tab 开头的单元格在入库前被转义（§18.4）
- **许可纪律**——仓库只提供合成数据；不内置抓取、不收录无授权商品图（§8.7）

---

## 🗺️ 路线图

| 阶段 | 范围 | 状态 |
| --- | --- | --- |
| **A/B** | 工程基础 + 数据导入管线 | ✅ 已完成（本里程碑） |
| **C** | 评论洞察与商品机会卡 | ⏳ 下一步 |
| **D** | Listing 工作台 | 规划中 |
| **E** | 视觉素材（GPT Image 2） | 规划中 |
| **F** | 评测与开源发布 | 规划中 |
| **G** | 实时数据与卖家 Beta（SP-API） | 后续 |

详见 [`outputs/Insight2Listing详细产品与技术方案.md`](outputs/Insight2Listing详细产品与技术方案.md)。

---

## 🤝 参与贡献

欢迎一切贡献——bug 反馈、功能建议、Pull Request 都很重要。

1. Fork 本仓库
2. 创建功能分支（`git checkout -b feature/amazing-feature`）
3. 提交改动
4. 推送分支并提交 Pull Request

请参阅 [`CONTRIBUTING.md`](CONTRIBUTING.md) 与 [`SECURITY.md`](SECURITY.md)。

---

## 📄 许可

源代码以 [MIT License](LICENSE) 发布。第三方数据集、商品图片、商标、字体与用户上传内容**不**自动受此许可保护；仓库仅提供合成数据。详见 [`DATA_LICENSE.md`](DATA_LICENSE.md) 与 [`DISCLAIMER.md`](DISCLAIMER.md)。

---

## ⭐ 支持

如果 Insight2Listing 对你有帮助，欢迎点一个 ⭐，帮助项目成长。