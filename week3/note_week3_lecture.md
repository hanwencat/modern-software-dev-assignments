# CS146S Week 3: The AI IDE - Learning Notes

**Topic:** The AI IDE & Agentic Workflows
**Core Concept:** Transitioning from "Writing Code" to "Architecting Specs"
**Date:** February 2026

---

## 1. 核心思维转变 (The Paradigm Shift)

这一周的核心不在于学习某个具体的工具操作，而在于**开发者角色的根本转变**。

### 1.1 从 Coder 到 Architect/PM
* **Old Role:** 关注每一行代码的语法和实现细节（"How"）。
* **New Role:** 关注系统的设计、接口定义和验收标准（"What"）。
* **Spec is the New Source Code:** LLM 本质上是一个新的编译器。你的 Spec（需求文档）就是新的源代码。如果代码跑不通，通常是因为你的 Spec 写得有歧义。

### 1.2 Agent 是初级工程师
* 把 AI Agent 想象成一个**聪明但缺乏上下文的实习生**。
* 你不能只给它一个模糊的指令（"做个网页"），你必须给它：
    * **Context:** 文档和现有代码结构。
    * **Tools:** 它可以调用的工具（Linter, Test Runner）。
    * **Guardrails:** 预判它可能犯的错（Defensive Prompting）。

---

## 2. 关键方法论 (Core Methodologies)

### 2.1 上下文工程 (Context Engineering)
*Context is finite and fragile.*

* **四大失效模式 (The 4 Context Fails):**
    1.  **Poisoning (中毒):** 错误的幻觉被留在历史记录里，导致 AI 持续犯错。
    2.  **Distraction (分心):** 上下文太长，AI 忽略了最新的指令，倾向于复读历史。
    3.  **Confusion (困惑):** 给太多无关的工具或文件，AI 不知道用哪个。
    4.  **Clash (冲突):** 前后信息不一致。
* **解决方案：频繁有意的压缩 (Frequent Intentional Compaction)**
    * 不要在一个 Session 里无休止地对话。
    * **Workflow:** `Research (调研)` -> **压缩成 Markdown** -> `Plan (计划)` -> **压缩成 Markdown** -> `Implement (实施)`。
    * 每完成一个阶段，**清空上下文 (Reset Context)**，只带着压缩后的文档进入下一阶段。

### 2.2 生产级开发标准 (FAANG Standard)
* **Shredding the Docs (文档撕碎):** 在写代码前，文档必须经过严苛的人工审查。
* **TDD (Test-Driven Development) 作为围栏:**
    1.  **Human:** 编写 Spec 文档。
    2.  **AI:** 根据 Spec 编写 **Test Cases**。
    3.  **Human:** 确认测试用例覆盖了需求。
    4.  **AI:** 编写功能代码以 **Pass Tests**。
    * *原理：测试代码是防止 AI 产生幻觉的最强约束。*

### 2.3 工具设计原则 (Writing Tools for Agents)
* **Tools as APIs:** Agent 是 API 的消费者。
* **Naming Matters:** 工具名和 Docstring 就是 Prompt。要详细描述“做什么”、“返回什么”、“何时使用”。
* **Forgiving Outputs:** 工具报错时不要直接 Crash，要返回有用的错误信息（Error as Feedback），指导 Agent 自我修正。

---

## 3. 工具箱与配置 (The Toolkit)

### 3.1 人类指挥棒：`design_doc_template.md`
这是你控制 AI 输出质量的核心文档（System Prompt）。

* **Current Context:** 告诉 AI 当前系统状态，防止幻觉。
* **Non-Functional Requirements:** 强制 AI 关注性能、安全、可扩展性。
* **Files Changes:** 明确指定**只允许修改哪些文件**（Context Hygiene）。
* **Out-of-Scope:** 明确**不要做什么**，防止画蛇添足。

### 3.2 AI 说明书：`AGENTS.md` / `.cursorrules`
这是一个放在项目根目录的文件，专门写给 AI 看。

* **Repo Orientation:** 项目结构是怎样的？Monorepo 还是 Polyrepo？
* **Dev Commands:** 启动命令是 `npm run dev` 还是 `pnpm dlx turbo...`？
* **Testing Strategy:** 运行测试的确切命令是什么？
* *目的：减少 AI 的“试错成本”，让它一次做对。*

---

## 4. 终极工作流策略 (The Workflow Strategy)

### 4.1 AI 工具的三个时代
1.  **Copilot (Era 1):** Code Completion (补全)。效率提升 ~10%。
2.  **AI IDEs (Era 2):** Cursor/Windsurf (自动化)。效率提升 ~20%。
3.  **Agents (Era 3):** Devin (异步委托)。效率提升 ~10x。

### 4.2 避免“尴尬区” (Avoid The Awkward Middle)
根据任务的时间尺度选择工具：

| 区域 | 时间尺度 | 模式 | 推荐工具 | 典型任务 |
| :--- | :--- | :--- | :--- | :--- |
| **Sync (同步)** | < 1 min | **Flow (心流)** | Cursor, Windsurf | 补全、重构、Code Review、修复简单 Bug |
| **Awkward Middle** | 1 - 10 min | **Wait (等待)** | ❌ *Avoid* | *打断心流又不足以切换任务，效率最低* |
| **Async (异步)** | > 10 min | **Delegate (委托)** | Devin | 新功能开发、大型重构、编写测试套件、调研 |

* **策略：** 要么把任务拆小（Sync），要么合并变大（Async）。

### 4.3 混合工作流 (Hybrid Workflow)
1.  **Planning (Sync/Async):** 使用 Search/DeepWiki 快速定位上下文，生成 Plan。
2.  **Coding (Async):** 将 Plan 交给 Agent (Devin) 在后台执行，你需要像 Tech Lead 一样管理 Ticket。
3.  **Refining (Sync):** Agent 提交 PR 后，拉取到本地 IDE (Cursor)，进行人工 Review 和微调。

---

## 5. Action Items (立即行动)

1.  **配置环境:** 在你的项目根目录创建 `AGENTS.md` (或 `.cursorrules`)，写入环境配置和测试命令。
2.  **练习 Spec:** 下次写代码前，强迫自己先填满 `design_doc_template.md`，不写代码。
3.  **尝试 TDD:** 把填好的 Spec 发给 AI，指令：“Read this spec. Write the unit tests first. Do not implement the feature yet.”
4.  **分类任务:** 遇到问题时，先判断是 Sync 任务还是 Async 任务，选择正确的工具。

---
*Created based on CS146S Week 3 Reading List & Lectures.*