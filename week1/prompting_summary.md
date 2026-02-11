# Week 1 — Prompting 技术总结

## 概述

本周学习了 6 种 LLM Prompting 技术，通过设计不同的 System Prompt 引导本地模型（Mistral-Nemo 12B / Llama 3.1 8B）完成特定任务。

---

## 1. K-Shot Prompting（少样本提示）

**核心思想：** 通过提供 K 个"输入→输出"示例，让模型学习任务模式。

- **0-shot**：不给示例，直接问
- **1-shot**：给 1 个示例
- **Few-shot（K-shot）**：给多个示例（通常 2-5 个）

**适用场景：** 模式识别、格式转换、分类任务等。

**关键经验：**
- 示例要覆盖不同长度和复杂度
- System Prompt 提供示例，User Prompt 提供具体任务，职责分离
- LLM 在字符级操作（如反转单词）上受 tokenization 限制，较长的词容易出错
- 可以用代码逻辑生成示例，确保示例的准确性

---

## 2. Chain-of-Thought（思维链）

**核心思想：** 引导模型逐步推理，而非直接给出答案。

```
问题 → 步骤1 → 步骤2 → 步骤3 → ... → 答案
```

**适用场景：** 数学推理、逻辑问题、多步骤计算。

**关键经验：**
- 提示模型"Think step by step"可以显著提升推理准确率
- 适合需要中间推导过程的复杂问题（如模运算 3^12345 mod 100）
- 引导模型使用数学性质（如欧拉定理、周期性）分步求解

---

## 3. Self-Consistency Prompting（自洽性提示）

**核心思想：** 多次采样，通过多数投票选出最终答案。

```
Run 1 → 答案 A
Run 2 → 答案 A    →  多数投票 → 答案 A ✓
Run 3 → 答案 B
Run 4 → 答案 A
Run 5 → 答案 A
```

**适用场景：** 答案空间有限、需要高可靠性的推理任务。

**关键经验：**
- 使用较高的 temperature（如 1.0）增加采样多样性
- Prompt 质量仍然重要——需要让模型大部分时候都能推理正确
- 利用统计学思想：正确答案在多次采样中出现频率最高

---

## 4. Tool Calling（工具调用）

**核心思想：** 模型不直接回答问题，而是输出结构化的 JSON 工具调用请求，由外部系统执行。

```
模型输出:  {"tool": "工具名", "args": {"参数": "值"}}
系统执行:  调用对应函数，返回真实结果
```

**类比：** 模型是秘书写"请求单"，系统是跑腿的人去执行。

**适用场景：** 需要访问外部 API、文件系统、数据库等模型无法直接操作的资源。

**关键经验：**
- System Prompt 必须清楚描述：可用工具名称、参数、功能、JSON 输出格式
- 模型只负责"决定做什么"，系统负责"真正去做"
- 这是现代 AI Agent 的核心机制

---

## 5. RAG（检索增强生成）

**核心思想：** 将外部知识库中的相关文档检索出来，作为上下文提供给模型，辅助生成答案。

```
问题 → 检索相关文档 → 文档 + 问题 → 模型 → 答案
```

**适用场景：** 模型训练数据中没有的专有知识（如内部 API 文档、公司规范）。

**关键经验：**
- 需要实现两个部分：Context Provider（选择相关文档）+ System Prompt（指导模型使用上下文）
- 模型应该只基于提供的 context 回答，避免"幻觉"
- 文档选择的质量直接影响生成结果的准确性

---

## 6. Reflexion（反思）

**核心思想：** 让模型看到自己的错误反馈，进行自我修正的迭代过程。

```
生成初始代码 → 运行测试 → 发现错误 → 反馈给模型 → 生成改进代码
```

**类比：** 模拟人类"写代码 → 跑测试 → 看报错 → 修 bug"的循环。

**适用场景：** 代码生成、需要精确满足测试条件的任务。

**关键经验：**
- 需要设计两个部分：Reflexion Prompt（指导修复策略）+ Context Builder（组织错误信息）
- 将之前的代码和具体的失败信息一起反馈给模型
- 即使初始代码有错，通过反思通常能在一轮迭代后修正

---

## System Prompt vs User Prompt

| | System Prompt | User Prompt |
|---|---|---|
| **角色** | 设定 AI 的身份和行为规则 | 用户的具体请求 |
| **类比** | 员工的"工作手册" | 用户的"任务指令" |
| **变化频率** | 通常固定 | 每次对话可以不同 |

---

## 技术对比总结

| 技术 | 核心机制 | 模型做什么 |
|---|---|---|
| K-Shot | 提供示例学模式 | 模仿示例输出答案 |
| Chain-of-Thought | 逐步推理 | 展示思考过程再输出答案 |
| Self-Consistency | 多次采样 + 投票 | 多次回答，取多数 |
| Tool Calling | 结构化工具调用 | 输出 JSON 请求单 |
| RAG | 检索外部知识 | 基于提供的文档回答 |
| Reflexion | 自我反思修正 | 根据错误反馈改进输出 |

---

## 本地模型 vs 在线模型（ChatGPT / Gemini 等）

### System Prompt 的设置方式

| | 本地模型 (Ollama) | 在线 API (OpenAI / Google) | 网页聊天界面 |
|---|---|---|---|
| **设置方式** | 代码中 `{"role": "system", ...}` | 代码中 `{"role": "system", ...}` | 无法直接设置 |
| **替代方案** | — | — | Custom Instructions / GPTs / Gems |
| **灵活度** | 完全控制 | 完全控制 | 有限 |

**API 调用示例（OpenAI）：**

```python
from openai import OpenAI
client = OpenAI(api_key="your-key")

response = client.chat.completions.create(
    model="gpt-4",
    messages=[
        {"role": "system", "content": "你是一个数学老师"},
        {"role": "user", "content": "什么是微积分？"},
    ]
)
```

**API 调用示例（Google Gemini）：**

```python
import google.generativeai as genai

model = genai.GenerativeModel(
    model_name="gemini-pro",
    system_instruction="你是一个数学老师",
)
response = model.generate_content("什么是微积分？")
```

**网页界面替代方案：**
- **ChatGPT**：设置 → Custom Instructions（类似持久化的 System Prompt）；或创建 GPTs 时定义
- **Gemini**：创建 Gems 时可预设角色和行为
- **通用方法**：在对话第一条消息中写"你是一个...请按照以下规则..."，虽然技术上是 User Prompt，但效果类似

### Tool Calling 的区别

| | 本地模型（手动模拟） | 在线 API（原生支持） | 网页界面 |
|---|---|---|---|
| **工具描述** | 写在 System Prompt 里（自然语言） | 用 JSON Schema 结构化定义 | 平台预置，用户无法自定义 |
| **模型输出** | 纯文本 JSON（可能格式出错） | 结构化对象（保证格式正确） | 自动调用，用户无感知 |
| **解析方式** | 自己写 `json.loads()` 解析 | SDK 自动解析 | 不需要解析 |
| **可靠性** | 模型可能输出非法 JSON | 几乎不会出错 | 完全由平台保证 |
| **自定义工具** | 完全自定义 | 完全自定义 | 不可自定义 |

**API 原生 Tool Calling 示例（OpenAI）：**

```python
response = client.chat.completions.create(
    model="gpt-4",
    messages=[{"role": "user", "content": "北京今天天气怎么样？"}],
    tools=[{
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "获取指定城市的天气",
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {"type": "string", "description": "城市名称"}
                },
                "required": ["city"]
            }
        }
    }]
)
# 模型返回结构化的 tool_calls 对象，而非纯文本 JSON
```

**网页上的 Tool Calling 实例（用户无感知）：**
- ChatGPT 联网搜索 → 调用搜索工具
- ChatGPT Code Interpreter → 调用代码执行工具
- ChatGPT DALL-E 画图 → 调用图像生成工具
- Gemini 搜索/代码执行 → 同理

### 总结

> **网页是给普通用户的简化界面，API 是给开发者的完整接口。**
> 本周作业中用 Ollama + Python 代码做的事情，本质上就是在用 API 的方式与模型交互。
> 所有 6 种 Prompting 技术在本地模型和在线模型上都适用，区别只在于接口形式不同。
