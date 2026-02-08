# SimAgent

SimAgent 是一个纯 CPU 的本地 Agentic AI 框架，专为在容器内阅读另一个软件项目代码并执行任务而设计。它提供：

- **本地代码读取**：递归扫描指定仓库，按块索引代码。
- **轻量级 RAG**：用纯标准库实现的 BM25 风格检索，无需 GPU。
- **可交互的多轮对话**：支持 REPL 多轮迭代，遇到错误自动反馈给模型继续修正。
- **工具调用**：模型可以直接读取文件、搜索、写文件、列出目录等。

> 说明：SimAgent 自身运行在 CPU；如需决策会通过可配置的 LLM 接口调用外部大模型。模型通过工具调用对你的环境进行读写。

## 快速开始

```bash
python -m simagent --repo /path/to/target-repo
```

或安装后：

```bash
pip install -e .
simagent --repo /path/to/target-repo
```

启动后直接输入自然语言任务，例如：

```
请为项目添加一个健康检查接口，并更新 README。
```

## 环境变量

SimAgent 通过 HTTP 调用外部 LLM。你可以配置：

- `LLM_BASE_URL`：模型接口地址（如 `http://localhost:8000/v1/chat/completions`）
- `LLM_API_KEY`：可选的 API Key
- `LLM_MODEL`：模型名称（默认 `gpt-4.1-mini`）

## 交互协议（模型输出）

模型输出 JSON 指令，SimAgent 会执行并回传结果。例如：

```json
{"tool": "read_file", "path": "src/main.py"}
```

或者直接返回最终答案：

```json
{"final": "我已完成修改并更新了说明"}
```

## 设计结构

- `simagent/agent.py`：主调度器与多轮对话管理
- `simagent/rag.py`：BM25 风格检索实现
- `simagent/tools.py`：文件与搜索工具
- `simagent/llm.py`：HTTP LLM 调用
- `simagent/repo_reader.py`：仓库索引与切块

## 适用场景

- 在容器内分析大型仓库
- 自动完成工程任务（修 bug / 写测试 / 生成文档）
- 多轮迭代直到问题解决

## 免责声明

SimAgent 提供强力的文件操作能力，请仅在可信环境中使用。
