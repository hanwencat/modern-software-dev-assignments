# Week 3 作业总结 — Finnhub MCP Server

本文档综合本周作业中多个 Agent 的产出：**任务理解与设计**、**代码实现**、**代码解释与架构**、**测试**，便于复习与提交说明。

---

## 一、任务与需求（来自作业 + 设计 Agent）

### 1.1 作业要求摘要

- **目标**：搭建一个自定义 MCP (Model Context Protocol) 服务器，封装真实外部 API。
- **必须**：
  - 至少 2 个 MCP 工具（本作业做了 4 个）；
  - 清晰的参数与类型、错误处理与限流意识；
  - 安装/环境变量/运行方式文档，以及示例调用流程；
  - 本地 STDIO 或（可选）远程 HTTP 部署。
- **加分**：远程 HTTP (+5)、认证 (+5)。

### 1.2 本项目的功能需求

- **4 个 MCP 工具**：
  1. `get_stock_quote(symbol)` — 实时行情
  2. `get_company_profile(symbol)` — 公司基本面
  3. `get_company_news(symbol, from_date, to_date)` — 公司新闻
  4. `search_symbol(query)` — 股票代码搜索
- **非功能**：HTTP 错误/超时/空结果处理、60 次/分钟限流、API Key 用环境变量、异步 HTTP、日志打 stderr。

> 若你有「解读作业 / 规划任务」的 Agent 对话，可在此粘贴或引用关键结论。

---

## 二、设计与实现（来自设计文档 + 写代码 Agent）

### 2.1 设计决策摘要

| 决策         | 选择               | 原因简述 |
|--------------|--------------------|----------|
| MCP SDK      | FastMCP            | 装饰器注册工具、支持 STDIO/HTTP、参数类型推断 |
| HTTP 客户端  | httpx.AsyncClient  | 已有依赖、异步、超时与连接池 |
| 限流         | 内存 token bucket  | 60 req/min、无外部依赖、不阻塞事件循环 |
| 配置         | Pydantic BaseSettings | .env + 环境变量、启动时校验 API Key |

### 2.2 目录与文件职责

```
week3/
  server/
    main.py           # FastMCP 入口，4 个 @mcp.tool() 工具
    config.py         # Settings（API Key、base_url、超时、限流参数）
    finnhub_client.py # FinnhubClient：4 个 API 方法 + 统一 _request
    rate_limiter.py   # TokenBucketRateLimiter
  tests/
    conftest.py       # 公共 fixture、模拟 API 响应
    test_finnhub_client.py  # 客户端单元测试（mock _request / httpx）
    test_tools.py     # 工具层集成测试（mock FinnhubClient）
  design_doc.md       # 设计文档
  README.md           # 使用说明与工具说明
```

### 2.3 实现要点（代码层）

- **main.py**：用 `@mcp.tool()` 注册 4 个 `async def` 工具；工具内 `_get_client()` 取单例 `FinnhubClient`，`await client.get_quote(...)` 等，再把返回的 dict 格式化成给人看的字符串；异常捕获后返回 `"Error: ..."` 字符串。
- **finnhub_client.py**：`FinnhubClient` 持有 `httpx.AsyncClient` 和 `TokenBucketRateLimiter`；四个对外方法（`get_quote`、`get_company_profile`、`get_company_news`、`search_symbol`）都通过 `_request(endpoint, params)` 发请求；`_request` 内先 `await rate_limiter.acquire()`，再 `await self._http_client.get(...)`，统一处理 HTTP 异常并转为 `FinnhubAPIError`。
- **config.py**：从 `.env` 读 `FINNHUB_API_KEY` 等。
- **rate_limiter.py**：按时间滑动补充 token，`acquire()` 扣 1 个 token，扣不到则返回 False（由 client 抛限流错误）。

> 若你有「写代码」Agent 的详细实现说明或关键片段，可粘贴到本节或单独小节。

---

## 三、代码解释与架构（来自解释代码 Agent / 本对话）

### 3.1 两层分工：main 与 FinnhubClient

| 层级           | 文件             | 职责 |
|----------------|------------------|------|
| **MCP 工具层** | `main.py`        | 对外暴露给 Cursor/AI：接收参数、调 client、**格式化成字符串**、捕获异常并返回错误信息。 |
| **API 客户端层** | `finnhub_client.py` | 对 Finnhub：发 HTTP、**解析 JSON 为 dict/list**、限流与错误封装，不关心展示格式。 |

一次调用的数据流示例（如「查苹果股票」）：

1. 用户输入 → Cursor 调用 MCP 工具 `get_stock_quote("AAPL")` 或先 `search_symbol("Apple")` 再 `get_stock_quote("AAPL")`。
2. **main**：`await client.get_quote(symbol)` → **finnhub_client**：`await self._request("/quote", params={"symbol": symbol})`。
3. **\_request**：`await rate_limiter.acquire()` → `await self._http_client.get(...)` → 解析 JSON，返回 dict。
4. **main**：用 dict 拼成多行字符串，通过 MCP 返回给 Cursor，AI 再组织成自然语言回复。

### 3.2 为什么用 async？

- **网络 I/O 是等待型操作**：发请求后要等 Finnhub 响应，用同步写法会在这段时间内**占满当前线程**，整个 MCP 进程无法处理其他请求。
- **async/await**：在等待 HTTP 时**让出控制权**，asyncio 事件循环可以处理其他协程；单线程下也能并发处理多路 I/O。
- **必须用 async 的原因**：FastMCP 在 asyncio 下运行，工具需为 `async def`；`httpx.AsyncClient` 只有异步接口，所以 `get_quote`、`_request` 等都要是 async。

### 3.3 `_request` 的作用

`_request` 是 **FinnhubClient 内部唯一发 HTTP 的入口**，四个对外方法都走它：

1. **限流**：`await self._rate_limiter.acquire()`，超限抛 `FinnhubAPIError`。
2. **发请求与解析**：`await self._http_client.get(endpoint, params=...)`，然后 `response.json()`。
3. **统一错误处理**：把 `httpx` 的 HTTP 错误、超时、连接错误都转成 `FinnhubAPIError`，调用方只需处理这一种异常。

这样限流、超时、错误处理只写一处，便于维护。

### 3.4 架构示意图（数据流）

```
Cursor/AI 调用 get_stock_quote("AAPL")
    ↓
main.get_stock_quote  →  _get_client()  →  await client.get_quote("AAPL")
    ↓
finnhub_client.get_quote  →  await _request("/quote", params={"symbol": "AAPL"})
    ↓
_request: await rate_limiter.acquire()  →  await http_client.get(...)  →  return response.json()
    ↓
main 将 dict 格式化为字符串  →  经 MCP 返回 Cursor
```

> 若你有「解释代码 / 画图」Agent 的更多图示或说明，可粘贴到本节。

---

## 四、测试（来自测试 Agent + 仓库现有测试）

### 4.1 测试策略

- **单元测试**（`test_finnhub_client.py`）：对 `FinnhubClient` 各方法 mock `_request` 或底层 httpx，验证：
  - 正常响应时解析出的 dict 结构正确；
  - 空/无效响应、HTTP 错误、超时、限流失败时抛出 `FinnhubAPIError`；
  - 日期格式等参数校验。
- **集成测试**（`test_tools.py`）：对 main 里四个工具函数 mock `_get_client()` 返回的 `FinnhubClient`，验证：
  - 工具返回的字符串包含预期内容（如价格、公司名）；
  - 当 client 抛 `FinnhubAPIError` 时，工具返回包含 "Error" 的字符串而非崩溃。

### 4.2 运行方式

```bash
poetry run python -m pytest week3/tests/ -v
```

### 4.3 覆盖要点摘要

| 文件                     | 覆盖内容 |
|--------------------------|----------|
| test_finnhub_client.py   | get_quote / get_company_profile / get_company_news / search_symbol 成功与各种失败；限流时抛错 |
| test_tools.py            | 四个工具成功时输出格式、失败时返回错误信息、空 symbol 等 |

> 若你有「测试」Agent 的用例说明、边界情况或覆盖率结论，可粘贴到本节。

---

## 五、使用与交付

### 5.1 环境与运行

- **依赖**：`poetry install`（见 `pyproject.toml`，含 `mcp[cli]`、`httpx`、`pydantic-settings` 等）。
- **环境变量**：`FINNHUB_API_KEY`（.env 或 export）。
- **本地 STDIO**：`poetry run python -m week3.server.main`。
- **远程 HTTP（加分）**：`poetry run python -m week3.server.main --http`。

### 5.2 客户端配置（Cursor）

- Command: `poetry run python -m week3.server.main`
- Working directory: 项目根目录
- Environment: `FINNHUB_API_KEY=...`

详见 `week3/README.md` 中的工具说明与示例输入/输出。

### 5.3 提交物检查

- [x] 代码在 `week3/`（含 `server/`、`tests/`）
- [x] `week3/README.md`：环境、依赖、运行方式、客户端配置、四个工具说明与示例
- [x] 设计文档：`week3/design_doc.md`
- [x] 至少 2 个工具（本项目 4 个）、错误处理、限流、文档完整

---

## 六、可补充内容（来自其他 Agent）

若你还有以下类型的对话内容，可把要点或链接补充在对应位置：

- **写代码 Agent**：实现细节、遇到的坑、关键代码片段 → 可放在 **第二节** 或单独「实现笔记」小节。
- **解释代码 Agent**：更多架构图、调用链、async 示意图 → 可放在 **第三节**。
- **测试 Agent**：额外用例、边界情况、覆盖率或 CI 配置 → 可放在 **第四节**。

当前文档已按「任务 / 设计实现 / 解释架构 / 测试 / 使用」综合了设计文档、README、代码结构和本对话中的解释；你只需要把其他 Agent 的结论或截图粘贴到对应小节即可形成完整总结。
