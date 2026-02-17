# CS146S Week 2 Assignment Notes: Action Item Extractor 实战

**Course:** CS146S: The Modern Software Developer (Stanford)
**Week:** 2
**Theme:** 用 AI 辅助开发一个 FastAPI + SQLite + Ollama 应用
**Status:** Completed

---

## Part 1: LLM Structured Outputs (TODO 1)
*Objective: 让 LLM 不再自由发挥，而是被迫输出我们定义好的 JSON 格式。*

### 1. 核心问题
LLM 默认输出自然语言文本，但我们需要的是 **程序可解析的结构化数据**（一个字符串列表）。

### 2. 解决方案：Pydantic + Ollama `format` 参数
这是一个"双保险"机制：

* **发送前** — `ActionItems.model_json_schema()`：把 Pydantic model 转成 JSON Schema（一份"规格说明书"），传给 Ollama 的 `format` 参数，**约束模型只能输出这个格式**。
* **接收后** — `ActionItems.model_validate_json()`：解析 LLM 返回的 JSON 字符串，**验证它是否真的符合 schema**，不符合就抛异常。

```python
class ActionItems(BaseModel):
    items: List[str]   # 这就是全部的"规格说明书"

# 发送
response = chat(model=..., messages=[...], format=ActionItems.model_json_schema())
# 接收 & 验证
result = ActionItems.model_validate_json(response.message.content)
```

### 3. 关键设计决策
* **模型可配置：** `LLM_MODEL = os.getenv("OLLAMA_MODEL", "qwen3-coder:30b")` — 不硬编码，通过环境变量切换。
* **空输入短路：** `if not text.strip(): return []` — 不浪费一次 LLM 调用。
* **System Prompt 里写 "return as JSON"：** Ollama 文档推荐的做法，帮助模型理解输出格式。

### 4. LLM vs 规则引擎的对比
规则引擎只能匹配固定模式（bullet、checkbox、关键字前缀），而 LLM 能理解语义。例如：
> "John will set up the database schema by Friday."

规则引擎完全无法识别这是一个行动项，但 LLM 可以。

---

## Part 2: 单元测试与 Mock (TODO 2)
*Objective: 测试调用外部服务（LLM）的函数，但不真的调用外部服务。*

### 1. 核心矛盾
`extract_action_items_llm()` 依赖 Ollama 服务。直接调用的问题：
* LLM 每次返回结果可能不同 → 没法写确定性的 assert
* CI 环境没有 Ollama → 测试必挂

### 2. `@patch` 的工作原理
`@patch("week2.app.services.extract.chat")` 做了一件事：**在测试运行期间，把 `extract.py` 里的 `chat` 替换成一个假对象（MagicMock），测试结束自动恢复。**

关键规则：**patch 的路径是 `chat` 被使用的位置**（`extract.py`），而不是被定义的位置（`ollama` 库）。

### 3. MagicMock — 万能假对象
```python
m = MagicMock()
m.anything          # 不报错，返回另一个 MagicMock
m.foo.bar.baz       # 链式访问也不报错
m(1, 2, 3)          # 当函数调用也不报错
```

所以 `fake_response.message.content = '...'` 能工作——MagicMock 允许你在任意层级设置属性。

### 4. Mock 测试到底在测什么？

**重要认知：** Mock 数据是写死的，输入文本的内容不影响测试结果（因为 LLM 被 mock 了）。
那测试的意义在哪？

它测的不是 LLM 的智能，而是**我们自己代码的逻辑**：
* 空输入是否真的短路了（`mock_chat.assert_not_called()`）
* JSON 解析逻辑是否正确（返回值是 `list[str]` 而不是字典）
* 异常路径是否正确（无效 JSON → 抛异常而不是静默失败）
* **回归保护：** 未来有人改代码时，能立刻发现改坏了什么

### 5. MagicMock 自带的断言方法

| 方法 | 作用 |
|------|------|
| `mock.assert_called_once()` | 恰好被调用了 1 次 |
| `mock.assert_not_called()` | 从未被调用 |
| `mock.assert_called_once_with(...)` | 恰好 1 次，且参数匹配 |
| `mock.call_count` | 返回被调用次数 |

---

## Part 3: 代码重构 (TODO 3)
*Objective: 把"能跑"的代码变成"规范"的代码。*

### 1. API 契约：`Dict[str, Any]` → Pydantic Model

**Before (坏味道)：**
```python
def extract(payload: Dict[str, Any]) -> Dict[str, Any]:
    text = str(payload.get("text", "")).strip()
```
问题：传什么字段都不报错，`/docs` 看不到请求结构，容易出 bug。

**After (类型安全)：**
```python
def extract(payload: ExtractRequest) -> ExtractResponse:
    text = payload.text.strip()   # 直接用属性访问，有类型提示
```
好处：FastAPI 自动验证请求体，字段缺失直接返回 422，自动生成 API 文档。

**最佳实践：** 集中管理 — 新建 `schemas.py` 放所有 Pydantic model，路由文件保持精简。

### 2. 应用生命周期：模块级调用 → Lifespan

**Before：** `init_db()` 在 `import main` 时就执行 — 测试中只要 import 就触发数据库初始化。

**After：** 用 FastAPI 的 `lifespan` 上下文管理器：
```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()    # 启动时
    yield        # 运行中
    # 关闭时的清理（如果需要）

app = FastAPI(lifespan=lifespan)
```
数据库只在应用真正启动时才初始化，可控性更强。

### 3. 数据库层：`sqlite3.Row` → `dict`

**Before：** 返回 `sqlite3.Row`，调用方必须用 `row["id"]` 取值，没类型提示。
**After：** 用 `dict(row)` 转换后返回 `dict[str, Any]`，不暴露 SQLite 的实现细节。

### 4. 错误处理：裸奔 → try-except + logging

**Before：** 数据库异常直接冒泡到路由层，没有日志。
**After：** 所有数据库操作包裹在 `try-except sqlite3.Error` 中，用 `logger.exception()` 记录完整堆栈，路由层捕获并返回有意义的 HTTP 500。

---

## Part 4: Agentic 模式实战 (TODO 4)
*Objective: 用 Cursor Agent 模式一次性完成"加端点 + 改前端"的跨文件任务。*

### 1. 新增端点
* `POST /action-items/extract-llm` — 和原有的 `/extract` 平行，但调用 LLM 版本的提取函数。
* `GET /notes` — 返回所有保存的笔记，`notes.py` 中原本只有 POST 和 GET by ID，缺了 list all。

### 2. 前端：避免重复代码
原来的 JS 把提取逻辑写在 click handler 里。加第二个按钮时，**不要复制粘贴**，而是提取公共函数：
```javascript
async function doExtract(endpoint) { ... }
$('#extract').addEventListener('click', () => doExtract('/action-items/extract'));
$('#extract-llm').addEventListener('click', () => doExtract('/action-items/extract-llm'));
```

### 3. Agent 模式的价值
这种"后端加端点 + 前端加按钮 + 改 JS 逻辑"的跨文件任务，手动做需要在多个文件间跳转。Agent 模式一次性完成所有改动并保持一致性。

---

## Part 5: 自动生成 README (TODO 5)
*Objective: 让 AI 从代码中提取信息，生成人类可读的文档。*

### 核心 Takeaway
好的 README 应该包含：
1. **项目概述** — 一句话说清楚这是什么
2. **安装运行** — 新人拿到代码后能跑起来
3. **API 文档** — 端点、参数、返回值
4. **测试方法** — 怎么验证代码是否正确

AI 生成文档的优势：它能"看到"所有代码，不会遗漏端点或参数。但仍需人工审查确认准确性。

---

## 总结：本周学到的核心概念

| 概念 | 一句话总结 |
|------|-----------|
| Ollama Structured Outputs | 用 JSON Schema 约束 LLM 输出格式，Pydantic 做发送前的 schema 生成和接收后的验证 |
| `@patch` / Mock | 测试期间临时替换外部依赖为假对象，测试代码逻辑而非外部服务 |
| Pydantic + FastAPI | 用类型定义替代 `Dict[str, Any]`，自动请求验证 + 自动生成 API 文档 |
| FastAPI Lifespan | 控制应用启动/关闭时的资源初始化，比模块级调用更可控 |
| Agent 模式 | 跨文件的一致性改动（后端 + 前端）一次性完成 |
