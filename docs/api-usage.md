# Vue 对接接口说明

## 1. 安装依赖

```bash
pip install fastapi uvicorn pydantic
```

## 2. 启动服务

```bash
uvicorn api_server:app --host 0.0.0.0 --port 8000 --reload
```

若在项目父目录启动，建议使用（避免模块路径错误）：

```bash
E:/Miniconda/envs/NLP/python.exe -m uvicorn api_server:app --host 127.0.0.1 --port 8000 --app-dir "c:/Users/2/Desktop/AI_FTA_System(2)/AI_FTA_System" --reload
```

启动后先检查健康接口，确认已命中新版本：

```bash
curl http://127.0.0.1:8000/api/health
```

预期返回包含：`"build": "2026-04-15-template-parser-v12"`。

## 3. 接口列表

- `GET /api/health`
- `POST /api/fta/generate`
- `POST /api/fta/review`

## 4. 生成故障树接口

### 请求体

```json
{
  "system": "Drone",
  "top_event": "Drone Crash",
  "source": "ai",
  "manual_failures": [],
  "use_knowledge_graph": true,
  "run_analysis_report": true,
  "run_draft_review": true,
  "output_prefix": "demo_run"
}
```

- `source=ai` 时，系统自动调用AI生成故障事件。
- `source=manual` 时，需要传 `manual_failures`。
- `source=text` 时，需要传 `raw_text`（长文本故障手册），后端会分块抽取并自动合并结构化故障记录。

### `source=text` 示例（推荐用于工业手册）

```json
{
  "system": "通用型驱动系统",
  "top_event": "驱动系统硬件异常",
  "source": "text",
  "raw_text": "故障代码F01630...（可粘贴长文档）",
  "text_chunk_size_chars": 6000,
  "text_chunk_overlap_chars": 300,
  "use_knowledge_graph": true,
  "run_analysis_report": true,
  "run_draft_review": true,
  "output_prefix": "drive_manual_run"
}
```

说明：
- `text_chunk_size_chars` 控制每次送入模型的分块长度（字符）。
- `text_chunk_overlap_chars` 控制相邻分块重叠长度，减少跨块信息丢失。
- 返回中新增 `extracted_faults` 字段，`files.extracted_json` 会保存抽取结果文件路径。

### manual_failures 示例

```json
[
  {
    "name": "动力系统失效",
    "probability": 0.12,
    "gate": "OR",
    "causes": [
      { "name": "电机过热停转", "probability": 0.07, "gate": "OR", "causes": [] },
      { "name": "电调故障", "probability": 0.03, "gate": "OR", "causes": [] }
    ]
  }
]
```

## 5. Vue 调用示例

```javascript
const res = await fetch('http://localhost:8000/api/fta/generate', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    system: 'Drone',
    top_event: 'Drone Crash',
    source: 'ai',
    use_knowledge_graph: true,
    run_analysis_report: true,
    run_draft_review: true
  })
});

const data = await res.json();
console.log(data);
```

## 6. 返回结果

返回包含：
- `tree`: 构建好的故障树 JSON
- `dot_content`: DOT文本（前端可直接渲染为故障树图）
- `extracted_faults`: 文本抽取得到的结构化故障记录（仅 `source=text`）
- `analysis_report`: AI 分项分析
- `draft_review`: AI 初稿检验（不足项）
- `files`: 生成文件路径（xml/dot/png/报告）
