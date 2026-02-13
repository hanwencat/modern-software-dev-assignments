# CS146S Week 2 Study Notes: The Anatomy of Coding Agents & MCP

**Course:** CS146S: The Modern Software Developer (Stanford)
**Week:** 2
**Theme:** Building Agents, MCP Protocol & Tool Use
**Status:** Completed

---

## Part 1: 手搓 Agent (Building a Coding Agent From Scratch)
*Objective: 祛魅 "AI Agent"，理解它不是黑魔法，而是一个由 LLM 驱动的死循环。*

### 1. 核心逻辑：The Loop (循环)
Agent 本质上是一个编排 User、LLM 和 Tools (Runtime) 交互的 **`while` 循环**。

* **Observe (观察):** 接收用户输入或工具运行的结果。
* **Think (思考):** LLM 根据上下文决定是“直接回复”还是“调用工具”。
* **Act (行动):** 如果 LLM 决定调用工具，Python 脚本就在本地执行该函数（如 `read_file`）。
* **Feedback (反馈):** 将工具运行结果（Stdout/Return value）作为新的 Context 喂回给 LLM。

### 2. 关键组件 (代码剖析)
* **System Prompt (大脑):** 定义人设。必须明确协议（如："To use a tool, output `tool: name(args)`"）。
* **The Client (心脏):** 负责解析 LLM 的文本回复，正则匹配工具调用，并执行 Python 函数。
* **Tools (手脚):** 实际干活的 Python 函数（如 `read_file`, `edit_file`）。

---

## Part 2: Model Context Protocol (MCP)
*Objective: 解决连接性问题，为 AI 时代建立统一的“USB 标准”。*

### 1. 痛点：N x M 问题
* **旧方法:** 为每个 LLM (Claude, Gemini) 和每个数据源 (Local FS, Postgres) 单独写连接器。
* **MCP 方法:** 标准化协议。写 **1 个 MCP Server**，所有支持 MCP 的客户端 (Cursor, Claude Desktop) 都能直接用。

### 2. 核心魔法：`@mcp.tool`
这是一个**自省 (Introspection)** 装饰器。
* 它自动读取 Python 函数的 **Signature (签名)** 和 **Docstring (文档)**。
* 它将 Python 代码 (`def add(a: int)`) 自动翻译成 LLM 能读懂的 JSON Schema (`{"type": "integer"}`).
* **意义:** 你不需要手写 System Prompt，**代码本身就是 Prompt**。

---

## Part 3: Deep Dive - LLM 如何决策？(Decision Mechanism)
*Key Concept: 为什么 LLM 知道什么时候该用工具，什么时候该陪聊？*

LLM 不是靠硬编码的 `if-else` 来判断的，而是靠 **语义匹配 (Semantic Matching)** 和 **概率预测**。

### 1. 隐形的上下文注入 (Context Injection)
当你连接 MCP Server 时，Host (Claude Desktop) 会默默地把你的 **Docstrings** 注入到 LLM 的 System Prompt 中。
> *System Prompt 示例:* "You have a tool named `get_stock_price`. Description: 'Fetches real-time price for a given ticker'."

### 2. 决策流程 (The "Menu" Analogy)
可以将此过程比作点菜：
1.  **菜单 (The Menu):** 你的 MCP Tools 列表。
2.  **顾客需求 (User Query):** "帮我算一下这波行情的最大回撤。"
3.  **语义比对 (Semantic Matching):** LLM 分析需求，扫描“菜单”。
    * 如果发现工具描述里有 "calculate max drawdown"，**匹配成功** -> **Call Tool**。
    * 如果全是无关工具（如 "read_file"），**匹配失败** -> **Answer Directly**。

### 3. 关键推论
**Docstring is King.** 如果你的函数注释写得含糊不清（如 `"""Helper function"""`），LLM 就无法进行正确的语义匹配，从而忽略该工具。

---

## Part 4: 实操指南 (Configuration & Setup)
*Objective: 让 Claude Desktop 真正连上你的代码。*

### 1. 配置文件在哪里？
你需要修改 Claude Desktop 的配置文件来注册你的 MCP Server。
* **macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`
* **Windows:** `%APPDATA%\Claude\claude_desktop_config.json`

### 2. 配置格式
将你的 Python 脚本路径填入 `mcpServers`。推荐使用 `uv` 来管理环境。

```json
{
  "mcpServers": {
    "my-finance-agent": {
      "command": "uv",
      "args": [
        "run",
        "with",
        "fastmcp",
        "python",
        "/Absolute/Path/To/Your/simple_mcp.py"
      ]
    }
  }
}