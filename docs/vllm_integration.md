# vLLM 接入说明（GPU 服务器上仅用 CPU 运行的场景）

## 结论摘要
- 可以通过 **vLLM 的 OpenAI 兼容服务**把本项目接入到 vLLM 推理框架。即使在 GPU 服务器上仅用 CPU，也可以使用 vLLM 的 CPU 模式启动服务，但吞吐和延迟会显著低于 GPU，需要控制模型规模与并发量。

## 推荐接入方式（OpenAI 兼容 API）
vLLM 提供 OpenAI 兼容的 HTTP 接口。你只需在部署侧启动 vLLM 服务，然后在本项目中以 HTTP 调用即可：

### 1) 启动 vLLM 服务
**GPU 模式（推荐）**
```bash
vllm serve <model_id_or_path> --host 0.0.0.0 --port 8000
```

**CPU 模式（GPU 服务器上仅用 CPU）**
```bash
vllm serve <model_id_or_path> --host 0.0.0.0 --port 8000 --device cpu
```
> 说明：CPU 模式通常只能支持更小的模型；并且吞吐量较低，需根据 CPU 核心数与内存配置调小并发和最大 token。

### 2) 在客户端侧调用（OpenAI 兼容）
**cURL 示例**
```bash
curl http://<host>:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "<model_id_or_path>",
    "messages": [{"role": "user", "content": "你好"}],
    "temperature": 0.7,
    "max_tokens": 256
  }'
```

**Python 示例（requests）**
```python
import requests

resp = requests.post(
    "http://<host>:8000/v1/chat/completions",
    json={
        "model": "<model_id_or_path>",
        "messages": [{"role": "user", "content": "你好"}],
        "temperature": 0.7,
        "max_tokens": 256,
    },
    timeout=60,
)
print(resp.json())
```

## 接入到本项目的落地建议
由于当前仓库没有业务代码结构说明，建议先确认以下事项：
1. **推理调用路径**：项目是否已有 LLM 客户端封装？如果有，把 OpenAI 兼容的 Base URL 指向 vLLM 服务即可。
2. **模型与资源匹配**：CPU 模式下请优先选择更小的模型（7B 或更小），并降低并发/上下文长度。
3. **可观测性**：CPU 运行时要监控内存和延迟，以避免 OOM 或超时。

如果你提供现有调用逻辑（代码入口或 LLM 客户端封装位置），我可以进一步把 vLLM 的调用改造成具体的代码改动。
