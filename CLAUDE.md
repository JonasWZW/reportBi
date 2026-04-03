# 智能报表 BI 系统 (smart-report-bi)

## 项目概述

基于 LangChain + LangGraph + FastAPI 实现的智能报表生成平台，用于安全运营场景的自然语言数据查询、图表生成和报表分析。

### 核心功能

1. **自然语言查询** - 用户输入 prompt，系统自动解析并查询数据
2. **数据可视化** - 支持表格、柱状图、折线图、饼图等图表
3. **智能分析** - 对数据进行归纳、总结、趋势分析
4. **报表模板** - 内置 JSON 格式模板，支持多章节和 Data Part
5. **调试模式** - 单独调试某个 Data Part，预览结果
6. **预制件机制** - 保存验证过的 prompt + 工具链为可复用块

---

## 技术栈

- **框架**: FastAPI + LangChain + LangGraph
- **向量检索**: FAISS (语义匹配工具)
- **图表**: ECharts
- **LLM**: OpenAI GPT-4o (可配置)

---

## 项目结构

```
app/
├── main.py                     # FastAPI 入口
├── config.py                   # 配置管理 (YAML + 环境变量)
│
├── agents/                     # Agent 模块
│   ├── prompt_rewriting_agent.py   # Prompt 改写 Agent (LangChain)
│   ├── query_agent.py               # 查询执行 Agent
│   ├── analysis_agent.py            # 分析 Agent (趋势/异常/LLM总结)
│   ├── debug_agent.py               # 调试模式 Agent
│   └── report_generation_agent.py   # 主报表生成 Agent (LangGraph)
│
├── api/                        # REST API
│   ├── routes.py               # /api/v1/report/* 路由
│   └── tools.py                # /api/v1/tools/* 路由
│
├── schemas/                    # Pydantic 数据模型
│   ├── tool.py                # Tool, ToolRegistry
│   ├── data_part.py            # DataPart
│   ├── block.py                # Block, BlockStore
│   ├── template.py             # Template, Chapter
│   └── report.py               # ReportGenerationRequest/Result
│
└── tools/                      # 工具模块
    ├── embedding.py            # 语义向量化 (sentence-transformers / OpenAI)
    ├── vector_store.py         # FAISS 向量存储和检索
    └── chart_generator.py      # 图表生成 (Table, Bar, Line, Pie)
```

---

## 核心概念

### 1. Data Part (数据部分)

报表的原子单元，对应用户的一句 prompt。

```python
DataPart:
  id: str                      # 唯一标识
  type: DataPartType           # "query" 或 "analyze"
  original_prompt: str          # 用户原始输入
  rewritten_prompt: str         # 改写后的标准 prompt
  tool_id: str | None           # 查询工具 ID
  params: dict                  # 工具调用参数
  depends_on: list[str]         # 依赖的其他 Data Part
  result: Any | None            # 执行结果
  state: DataPartState          # pending/running/completed/failed
```

### 2. Block (预制件)

已验证的 prompt + 改写 prompt + 工具链组合，可作为 few-shot 示例。

```python
Block:
  id: str
  name: str
  original_prompt: str          # 用户原始输入
  rewritten_prompt: str         # 改写后的标准 prompt (作为别名)
  tool_chain: list[dict]        # [{tool_id, params}, ...]
  result_type: str              # table/chart/text
  category: BlockCategory        # personal/shared
```

### 3. Template (报表模板)

JSON 格式模板，定义章节和 Data Part 引用。

```python
Template:
  id: str
  name: str
  chapters:
    - id: str
      title: str
      data_parts: list[str]     # Data Part ID 列表
      order: int
```

### 4. Tool (工具)

系统级工具清单，支持语义向量检索。

```python
Tool:
  id: str                       # 如 "asset_attacks"
  name: str                     # 如 "资产攻击查询"
  description: str              # 语义描述 (用于向量匹配)
  tool_type: ToolType           # query/chart/analyze/document
  params_schema: dict           # JSON Schema
  result_type: ResultType       # table/chart/text
```

---

## Agent 架构

```
┌─────────────────────────────────────────────────────────────┐
│                    Prompt 改写 Agent                         │
│   - 意图分解: 用户 prompt → n 个查询 + m 个分析              │
│   - 工具匹配: 预制件优先 → 向量检索 fallback                  │
│   - 时间解析: "最近一周" → {time_range: "last_week"}        │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    查询 / 分析 Agent                          │
│   - 查询 Agent: 调用大数据平台 API                            │
│   - 分析 Agent: 趋势分析、异常检测、LLM 总结                   │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    主 Agent (LangGraph)                      │
│   parse_request → rewrite_prompts → execute → assemble → report │
└─────────────────────────────────────────────────────────────┘
```

---

## API 端点

### 报表生成

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/v1/report/generate` | 生成报表 |
| POST | `/api/v1/report/debug/execute` | 调试：执行单个 Data Part |
| POST | `/api/v1/report/debug/rewrite` | 调试：改写并执行 |
| POST | `/api/v1/report/debug/session` | 创建调试会话 |
| GET | `/api/v1/report/debug/session/{id}/history` | 获取调试历史 |

### 预制件

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/v1/report/block/save` | 保存预制件 |
| GET | `/api/v1/report/block` | 列出预制件 |
| GET | `/api/v1/report/block/{id}` | 获取预制件详情 |
| DELETE | `/api/v1/report/block/{id}` | 删除预制件 |

### 模板

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/v1/report/templates` | 列出模板 |
| GET | `/api/v1/report/templates/{id}` | 获取模板详情 |

### 工具

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/v1/tools/` | 列出所有工具 |
| GET | `/api/v1/tools/search?query=xxx` | 语义搜索工具 |
| POST | `/api/v1/tools/register` | 注册新工具 |
| POST | `/api/v1/tools/init` | 初始化默认工具 |

---

## 工具注册表检索流程

```
用户 prompt
    │
    ▼
┌─────────────────┐
│  1. 预制件匹配   │ ──→ 匹配成功 → 直接使用
└────────┬────────┘
         │ 匹配失败
         ▼
┌─────────────────┐
│  2. 向量检索     │ ──→ 匹配成功 → 生成新预制件
│  (FAISS)        │
└────────┬────────┘
         │ 匹配失败
         ▼
    未找到合适工具
```

向量检索使用 `description` 字段，支持语义匹配。

---

## 内置工具

| Tool ID | 名称 | 描述 |
|---------|------|------|
| `asset_attacks` | 资产攻击查询 | 查询资产被攻击的情况 |
| `threat_stats` | 威胁事件统计 | 按类型/来源/严重程度统计 |
| `vulnerability_scan` | 漏洞扫描查询 | 漏洞数量和分布 |
| `log_query` | 日志查询 | 系统日志关键词搜索 |
| `network_flow` | 网络流量查询 | 流量大小和协议分布 |

---

## 内置模板

| 模板 ID | 名称 | 说明 |
|---------|------|------|
| `template_security_weekly` | 安全周报 | 概述、威胁事件、漏洞分析、资产风险、总结 |
| `template_security_monthly` | 安全月报 | 月度概况、威胁态势、漏洞管理、合规检查 |
| `template_vulnerability_analysis` | 漏洞分析报告 | 漏洞概览、高危漏洞、趋势、修复建议 |

---

## 配置说明

配置文件: `config.yaml`

```yaml
app:
  name: "smart-report-bi"
  port: 8000

llm:
  provider: "openai"           # openai | anthropic
  model: "gpt-4o"
  api_key: "${OPENAI_API_KEY}" # 环境变量

embedding:
  provider: "sentence-transformers"  # sentence-transformers | openai
  model: "all-MiniLM-L6-v2"
  device: "cpu"

vector_store:
  type: "faiss"
  dimension: 384

data_platform:
  base_url: "${DATA_PLATFORM_BASE_URL}"
  api_key: "${DATA_PLATFORM_API_KEY}"

blocks:
  storage_type: "file"
  storage_path: "./storage/blocks"

templates:
  storage_type: "file"
  storage_path: "./storage/templates"
  built_in_path: "./templates"
```

---

## 启动方式

```bash
# 安装依赖
pip install -e .

# 配置环境变量
export OPENAI_API_KEY="sk-xxx"

# 启动服务
python -m app.main
# 或
uvicorn app.main:app --reload --port 8000

# API 文档
# http://localhost:8000/docs
```

---

## 测试

```bash
pytest tests/ -v
```

---

## 开发规范

1. **不可变性** - 创建新对象，切勿修改现有对象
2. **错误处理** - 每个层级显式处理错误
3. **输入验证** - 在系统边界处验证用户输入
4. **文件组织** - 多个小文件 > 少数大文件 (<800行)

---

## TODO

- [ ] 用户认证和权限控制
- [ ] 查询结果缓存机制 (Redis)
- [ ] 数据库持久化 (SQLAlchemy)
- [ ] 前端界面
- [ ] Docker 部署
