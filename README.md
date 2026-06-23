基于 Multi-Agent 的智能期末复习系统——"学伴·SuperTrainer"

版本: v4.0 | 文档状态: 正式版 | 最后更新: 2026年6月23日


## 目录

1. [项目概述](#1-项目概述)
2. [系统架构](#2-系统架构)
3. [AI Agent 设计](#3-ai-agent-设计)
4. [接口设计](#4-接口设计)
5. [技术栈](#5-技术栈)


## 1. 项目概述

### 1.1 项目定位

面向期末复习大学生，支持多学科知识库构建，自动提取PPT、PDF、Word文档核心考点，通过前置小测试摸清学生水平，根据考试日期自动排期复习计划，提供考点精讲、智能出题、模拟测试和问答服务。

### 1.2 核心功能

| 功能 | 说明 |
|------|------|
| 多格式资料解析 | 支持PDF、PPT、Word、TXT上传，自动提取核心考点 |
| 跨学科知识库 | 不同学科独立建立知识库，互不干扰 |
| 前置测验与诊断 | 8-15题小测试，自动识别薄弱点和水平分级 |
| 个性化复习计划 | 根据考试日期和每日可用时间，SM-2算法自动排期 |
| 考点精讲 | 定义+公式+考法+例题，支持RAG增强问答 |
| 智能出题 | 选择/填空/简答/计算，难度自适应 |
| 模拟测试 | 按真实考试生成套卷，计时+自动判分 |
| 错题本 | 自动收录错题，7类错因诊断，苏格拉底式引导 |

### 1.3 核心指标

| 指标 | 目标值 |
|------|--------|
| 文档解析速度 | ≤30秒/50页 |
| 问答响应时间 | ≤3秒 |
| 批改准确率 | ≥90% |
| 考点提取准确率 | ≥85% |
| 并发支持 | 50用户 |


## 2. 系统架构

### 2.1 整体架构图

```
┌─────────────────────────────────────────────────────────────┐
│                  前端 React 18 + TypeScript                  │
│              仪表盘 | 上传 | 答题 | 计划 | 错题本           │
└───────────────────────────┬─────────────────────────────────┘
                            │ HTTP REST / JSON
┌───────────────────────────▼─────────────────────────────────┐
│                   FastAPI 0.115+ 后端                        │
│                    异步路由 + Pydantic                       │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐    │
│  │         Orchestrator 状态机 (LangGraph)             │    │
│  │  IDLE → PARSING → QUIZ_GEN → EVALUATING → PLANNING  │    │
│  └─────────────────────────────────────────────────────┘    │
│                                                             │
│  ┌────────────┐ ┌────────────┐ ┌─────────────────────┐    │
│  │Tutor Agent │ │Assistant   │ │  Evaluator Agent    │    │
│  │解析+排期    │ │Agent 出题  │ │  批改+诊断          │    │
│  └─────┬──────┘ └─────┬──────┘ └──────────┬──────────┘    │
│        │              │                    │               │
│  ┌─────▼──────────────▼────────────────────▼──────────┐    │
│  │         LLM Client (DeepSeek API / OpenAI SDK)      │    │
│  │              三档算力: heavy/medium/light            │    │
│  └──────────────────────────────────────────────────────┘    │
│                                                             │
│  ┌──────────────────────────────────────────────────────┐    │
│  │    SQLite + sqlite-vec (结构化数据 + 向量检索)       │    │
│  └──────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 数据流转

```
上传资料 → 解析文档 → 提取考点 → 建立向量索引 → 生成前置测验
    → 学生作答 → 批改判分 → 错因诊断 → 生成学情报告
    → 配置考试日期 → SM-2排期 → 每日复习计划
    → 学习过程中可随时提问、刷题、模拟考 → 动态调整计划
```


## 3. AI Agent 设计

### 3.1 Agent 定义

系统由三个AI Agent协作完成所有功能：

| Agent | 角色 | 职责 | 输入 | 输出 | 算力 |
|-------|------|------|------|------|------|
| Tutor | 主导师 | 文档解析、切片、向量化、考点提取、SM-2排期 | 文档路径/考试日期 | 切片+向量+知识点+复习计划 | medium |
| Assistant | 助教 | 生成测验题目（前置测验/专项训练/模拟考试） | 知识点+难度+题型 | JSON格式试题集 | medium |
| Evaluator | 评估者 | 批改作答、错因诊断、水平分级、苏格拉底式引导 | 答案+标准答案+历史记录 | 批改结果+诊断标签+水平报告 | heavy |

### 3.2 Agent 工作流

| 阶段 | 触发动作 | 执行Agent | 核心操作 | 输出 |
|------|----------|-----------|----------|------|
| PARSING | 上传资料 | Tutor | 多格式文档解析、语义切片、向量化、考点提取 | 切片+向量+知识点 |
| PRE_QUIZ | 开始测试 | Assistant | 从知识库抽取8-15题，覆盖各章节 | 前置测验题 |
| EVALUATING | 提交答案 | Evaluator | 自动判分、水平分级、薄弱点识别、错因诊断 | 批改结果+诊断报告 |
| PLANNING | 配置日期 | Tutor | EMA更新掌握度、SM-2算法计算复习间隔 | 复习计划 |
| QUIZ | 请求出题 | Assistant | 基于薄弱点和阶段生成针对性试题 | 专项/模拟试题 |
| ANSWER | 学生提问 | Evaluator | 向量检索+RAG生成答案，附引用来源 | 问答结果 |

### 3.3 状态机

| 状态 | 说明 | 可执行动作 | 下一状态 |
|------|------|------------|----------|
| IDLE | 空闲等待 | start() | PARSING |
| PARSING | 解析中 | get_status() | PARSED |
| PARSED | 解析完成 | proceed() | QUIZ_GEN |
| QUIZ_GEN | 出题中 | get_questions() | QUIZ_READY |
| QUIZ_READY | 等待作答 | submit_answers() | EVALUATING |
| EVALUATING | 批改中 | get_results() | EVALUATED |
| EVALUATED | 批改完成 | proceed() | PLANNING |
| PLANNING | 排期中 | get_plan() | DONE |
| DONE | 完成 | - | - |

### 3.4 Agent 通信机制

采用共享状态池模式，所有Agent通过Orchestrator访问统一State对象，不直接通信：

```
{
  material_id: "uuid",
 学科: "计算机组成原理",
  chunks: [...],
  knowledge_points: [...],
  questions: [...],
  answers: [...],
  mastery_records: {...},
  study_plan: {...},
  exam_date: "2026-07-15",
  daily_hours: 2.5
}
```


## 4. 接口设计

### 4.1 API 概览

| 方法 | 端点 | 功能 | 请求体 | 响应 |
|------|------|------|--------|------|
| POST | /api/v1/materials/upload | 上传资料 | multipart/form-data | {task_id, status} |
| GET | /api/v1/materials/{id}/status | 解析状态 | - | {progress, status, kp_count} |
| POST | /api/v1/sessions/pre-quiz | 创建前置测验 | {material_id} | {session_id, questions} |
| POST | /api/v1/sessions/{id}/answers | 提交作答 | {answers: [...]} | {results: [...]} |
| GET | /api/v1/sessions/{id}/report | 获取诊断报告 | - | {level, weak_points, mastery} |
| POST | /api/v1/plan/generate | 生成复习计划 | {exam_date, daily_hours} | {plan: [...]} |
| GET | /api/v1/plan/today | 今日任务 | - | {tasks: [...]} |
| POST | /api/v1/questions/generate | 生成题目 | {kp_ids, count, difficulty} | {questions: [...]} |
| POST | /api/v1/mock-exam/start | 开始模拟考 | {duration, question_count} | {session_id, paper} |
| POST | /api/v1/mock-exam/submit | 提交模拟考 | {session_id, answers} | {score, report} |
| POST | /api/v1/qa/ask | 提问 | {question} | {answer, sources, related} |
| GET | /api/v1/students/wrong-questions | 错题本 | - | {questions: [...]} |
| GET | /api/v1/students/mastery | 掌握度 | - | {mastery_list} |

### 4.2 标准响应格式

```json
{
  "code": 0,
  "message": "success",
  "data": { ... }
}
```

### 4.3 错误码

| 错误码 | 说明 | HTTP状态码 |
|--------|------|------------|
| 0 | 成功 | 200 |
| 1001 | 参数错误 | 400 |
| 1002 | 资源不存在 | 404 |
| 2001 | 文档解析失败 | 500 |
| 2002 | 向量化失败 | 500 |
| 3001 | LLM调用超时 | 504 |
| 3002 | LLM返回格式错误 | 500 |


## 5. 技术栈

| 层级 | 技术选型 | 版本 | 说明 |
|------|----------|------|------|
| 后端框架 | FastAPI | 0.115+ | 异步支持，自动生成API文档 |
| ASGI服务器 | Uvicorn | 0.30+ | 高性能异步服务器 |
| Agent框架 | LangGraph | 最新 | 状态机管理，多智能体协作 |
| LLM客户端 | OpenAI SDK | 1.0+ | 统一接口，支持DeepSeek/OpenAI切换 |
| 向量数据库 | sqlite-vec | 0.1+ | SQLite原生扩展，零运维 |
| 关系数据库 | SQLite + aiosqlite | 3.40+ | 嵌入式，异步IO |
| PDF解析 | PyMuPDF | 1.24+ | 文本提取精度最高 |
| PPT解析 | python-pptx | 0.6+ | PPTX格式解析 |
| Word解析 | python-docx | 1.1+ | DOCX格式解析 |
| 数据校验 | Pydantic | 2.0+ | 类型安全，自动序列化 |
| 前端框架 | React | 18+ | 组件化开发 |
| 前端语言 | TypeScript | 5.0+ | 类型安全 |
| 样式框架 | Tailwind CSS | 3.0+ | 原子化CSS |
| 状态管理 | Zustand | 4.0+ | 轻量无样板代码 |

