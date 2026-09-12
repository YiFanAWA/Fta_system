# FTA System Monorepo Reorganization Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将远程仓库整理为可复现的前后端分离 Monorepo，并从旧工作区安全恢复 Vue 前端与评测资产。

**Architecture:** 远程 `main` 是 Git 基线，旧工作区只提供缺失资产。第一轮把 FastAPI 服务整体迁入 `backend-python/`、Vue 工程迁入 `frontend/`、离线评测保留在根级 `evaluation/`；迁移只修复路径和可复现性，不重写业务算法。

**Tech Stack:** Python 3.11、FastAPI、Pydantic、Neo4j Driver、OpenAI-compatible SDK、Vue 3、Vue CLI 5、Node/npm、Git。

---

## 文件职责与迁移映射

- `backend-python/*.py`：现有 Python 运行代码，第一轮不拆包。
- `backend-python/examples/`：可公开的请求样例和手册样例。
- `backend-python/.env.example`：无真实凭证的配置模板。
- `backend-python/requirements.txt`：在隔离虚拟环境中验证过的 Python 依赖快照。
- `frontend/src/`、`frontend/public/`：Vue 源码与静态资源。
- `frontend/package.json`、`frontend/package-lock.json`：Node 依赖合同。
- `evaluation/`：离线数据修正、数据集构建和质量评测。
- `scripts/verify_repo_layout.py`：仓库结构和禁止跟踪文件的门禁。
- `README.md`：仓库入口、目录边界和最小启动步骤。
- `docs/api-usage.md`：当前 API 使用说明。
- `docs/project-overview.md`：从旧项目说明整理出的产品与评测概览。
- `docs/archive/legacy-docker-deployment.md`：未验证的旧部署说明，只作为历史证据。

## Task 1：建立仓库边界门禁

**学习检查点：** 解释“Git 已跟踪文件”和“.gitignore 匹配文件”的区别，以及为什么补 `.gitignore` 不能自动移除已经提交的 `.env`。

**Files:**
- Create: `.gitignore`
- Create: `scripts/verify_repo_layout.py`

- [x] **Step 1: 写入忽略规则**

```gitignore
# Secrets and local configuration
.env
.env.*
!.env.example

# Python
__pycache__/
*.py[cod]
.pytest_cache/
.mypy_cache/
.ruff_cache/
.venv/
venv/

# Runtime artifacts
outputs/
backend-python/outputs/
*.log

# Frontend dependencies and builds
node_modules/
frontend/dist/

# IDE and OS
.vscode/
.idea/
.DS_Store
Thumbs.db
~$*
```

- [x] **Step 2: 创建跨平台布局检查脚本**

```python
from __future__ import annotations

import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REQUIRED = (
    "README.md",
    "backend-python/api_server.py",
    "backend-python/.env.example",
    "backend-python/requirements.txt",
    "frontend/package.json",
    "frontend/src/main.js",
    "evaluation/quality_eval/run_eval_benchmark.py",
    "docs/api-usage.md",
)
LEGACY_ROOT_FILES = (
    "api_server.py",
    "ai_module.py",
    "main.py",
    "pppppp",
    "API_USAGE.md",
    "DOCKER_DEPLOYMENT.md",
)


def tracked_files() -> list[str]:
    result = subprocess.run(
        ["git", "ls-files", "-z"],
        cwd=ROOT,
        check=True,
        capture_output=True,
    )
    return [item for item in result.stdout.decode("utf-8").split("\0") if item]


def main() -> int:
    errors: list[str] = []
    for relative in REQUIRED:
        if not (ROOT / relative).is_file():
            errors.append(f"missing required file: {relative}")

    for relative in LEGACY_ROOT_FILES:
        if (ROOT / relative).exists():
            errors.append(f"legacy root file remains: {relative}")

    for relative in tracked_files():
        parts = Path(relative).parts
        if relative == ".env" or "__pycache__" in parts or ".vscode" in parts:
            errors.append(f"forbidden tracked file: {relative}")
        if parts and parts[0] == "outputs":
            errors.append(f"forbidden tracked runtime output: {relative}")
        if len(parts) >= 2 and parts[0] == "frontend" and parts[1] == "dist":
            errors.append(f"forbidden tracked frontend build: {relative}")

    if errors:
        print("\n".join(errors))
        return 1

    print("repository layout verified")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [x] **Step 3: 运行门禁并确认它在迁移前失败**

Run: `python scripts/verify_repo_layout.py`

Expected: FAIL，明确报告缺失的 `backend-python/`、`frontend/`、`evaluation/` 和当前仍被跟踪的 `.env`，而不是脚本异常退出。

- [x] **Step 4: 提交门禁**

```powershell
git add -- .gitignore scripts/verify_repo_layout.py
git commit -m "build: add monorepo layout guard"
```

## Task 2：迁移 Python 后端并清理根目录

**学习检查点：** 说明为什么 `git mv` 能保留历史可读性，以及 Python 的导入查找为什么与启动工作目录和 `--app-dir` 有关。

**Files:**
- Move: `*.py` -> `backend-python/*.py`
- Move: `.env.example` -> `backend-python/.env.example`
- Move: `restart_api.ps1` -> `backend-python/restart_api.ps1`
- Move: request samples -> `backend-python/examples/`
- Move: `API_USAGE.md` -> `docs/api-usage.md`
- Move: `DOCKER_DEPLOYMENT.md` -> `docs/archive/legacy-docker-deployment.md`
- Move: `pppppp` -> `docs/project-overview.md`
- Remove from Git: `.env`, `(s`, `cd`, `curl`, `fault_tree.dot`, `fault_tree.xml`
- Modify: `backend-python/api_server.py`
- Modify: `backend-python/restart_api.ps1`

- [x] **Step 1: 创建目标目录并移动运行源码**

```powershell
New-Item -ItemType Directory -Force backend-python, backend-python/examples, docs/archive | Out-Null
git mv agent_workflow.py ai_module.py api_server.py clean_kb.py config.py file_text_extractor.py fta_dot_builder.py fta_generator.py fta_llm_pipeline.py fta_regression_check.py kg_builder.py kg_reasoner.py main.py prompt_templates.py utils.py vector_store.py visualizer.py xml_exporter.py backend-python/
git mv .env.example restart_api.ps1 backend-python/
git mv kg_query.json manual_handbook_sample.txt payload.json payload_737.json request_text.json backend-python/examples/
git mv API_USAGE.md docs/api-usage.md
git mv DOCKER_DEPLOYMENT.md docs/archive/legacy-docker-deployment.md
git mv pppppp docs/project-overview.md
```

- [x] **Step 2: 停止跟踪密钥、生成物和空临时文件**

```powershell
git rm -- .env '(s' cd curl fault_tree.dot fault_tree.xml
```

- [x] **Step 3: 让输出目录归属于 Python 服务**

Modify `backend-python/api_server.py` around the existing `OUTPUT_DIR` declaration:

```python
BASE_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = BASE_DIR / "outputs"
OUTPUT_DIR.mkdir(exist_ok=True)
```

- [x] **Step 4: 让重启脚本从自身目录启动应用**

Modify `backend-python/restart_api.ps1` so the Uvicorn arguments contain:

```powershell
$appDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$uvicornArgs = @(
    "-m", "uvicorn",
    "api_server:app",
    "--host", "127.0.0.1",
    "--port", "8000",
    "--app-dir", $appDir,
    "--reload"
)
```

Use `$uvicornArgs` for both logging and invocation; do not reuse PowerShell's automatic `$args` variable.

- [x] **Step 5: 验证目录移动没有改变 Python 语法和基线结果**

Run: `python -m compileall -q backend-python`

Expected: exit 0。

Run: `$env:PYTHONUTF8='1'; python backend-python/fta_regression_check.py`

Expected baseline: 4 cases total，Hydraulic、E-Drive、Narrative pass，AOCS remains the known failing case. Any different result blocks migration.

- [x] **Step 6: 提交后端迁移**

```powershell
git add -- backend-python docs/api-usage.md docs/archive/legacy-docker-deployment.md docs/project-overview.md
git add -u --
git commit -m "refactor: move Python service into backend directory"
```

## Task 3：恢复 Vue 前端源码

**学习检查点：** 区分源代码、依赖、构建产物和静态资源；说明为什么 `package-lock.json` 应提交而 `node_modules/`、`dist/` 不应提交。

**Files:**
- Create: `frontend/.browserslistrc`
- Create: `frontend/.gitignore`
- Create: `frontend/babel.config.js`
- Create: `frontend/jsconfig.json`
- Create: `frontend/package.json`
- Create: `frontend/package-lock.json`
- Create: `frontend/public/**`
- Create: `frontend/src/**`
- Create: `frontend/vue.config.js`
- Modify: `frontend/src/components/Workbench.vue`
- Modify: `frontend/vue.config.js`

- [x] **Step 1: 校验旧工作区来源**

The executor sets `FTA_LEGACY_ROOT` to the audited legacy project root outside this repository. Then run:

```powershell
$legacyFrontend = Join-Path $env:FTA_LEGACY_ROOT 'vue\vue-1\vue-demo'
if (-not (Test-Path -LiteralPath (Join-Path $legacyFrontend 'package-lock.json'))) {
    throw 'legacy frontend package-lock.json not found'
}
if (Test-Path -LiteralPath (Join-Path $legacyFrontend 'node_modules')) {
    Write-Output 'node_modules exists in legacy workspace and will not be copied'
}
```

- [x] **Step 2: 只复制构建所需内容**

```powershell
New-Item -ItemType Directory -Force frontend | Out-Null
$rootFiles = '.browserslistrc', '.gitignore', 'babel.config.js', 'jsconfig.json', 'package.json', 'package-lock.json', 'vue.config.js'
foreach ($name in $rootFiles) {
    Copy-Item -LiteralPath (Join-Path $legacyFrontend $name) -Destination (Join-Path 'frontend' $name)
}
Copy-Item -LiteralPath (Join-Path $legacyFrontend 'public') -Destination 'frontend/public' -Recurse
Copy-Item -LiteralPath (Join-Path $legacyFrontend 'src') -Destination 'frontend/src' -Recurse
```

Do not copy `dist/`, `node_modules/`, `.vscode/` or `webpack.inspect.js`. The five media files imported by `IndexLight.vue`, including the background MP4, are source dependencies and remain local-branch candidates pending the final public-license review.

- [x] **Step 3: 将 API 地址改成环境配置加开发代理**

Replace the current host-selection function in `frontend/src/components/Workbench.vue` with the following implementation, which preserves the user-saved override and uses the environment value as the deploy-time default:

```javascript
const CONFIGURED_API_BASE = (process.env.VUE_APP_API_BASE_URL || '').replace(/\/$/, '')

const API_BASE = (() => {
  try {
    const saved = localStorage.getItem('api_base_url')
    if (saved && /^https?:\/\//i.test(saved)) {
      return saved.replace(/\/$/, '')
    }
  } catch (e) {
    // Storage can be unavailable in restricted browser contexts.
  }
  return CONFIGURED_API_BASE
})()
```

Replace `frontend/vue.config.js` with the following equivalent configuration so existing build behavior remains intact while the proxy target becomes configurable:

```javascript
const { defineConfig } = require('@vue/cli-service')
const apiProxyTarget = process.env.VUE_APP_API_PROXY_TARGET || 'http://127.0.0.1:8000'

module.exports = defineConfig({
  transpileDependencies: true,
  chainWebpack: (config) => {
    config.plugin('copy').tap((args) => {
      if (args && args[0] && Array.isArray(args[0].patterns) && args[0].patterns[0]) {
        const pattern = args[0].patterns[0]
        pattern.globOptions = pattern.globOptions || {}
        pattern.globOptions.ignore = ['**/.DS_Store', '**/index.html']
      }
      return args
    })
  },
  devServer: {
    port: 8080,
    proxy: {
      '/api': {
        target: apiProxyTarget,
        changeOrigin: true
      }
    }
  }
})
```

- [x] **Step 4: 安装锁定依赖并构建**

Run: `npm ci --prefix frontend`

Expected: exit 0 and `frontend/node_modules/` remains ignored.

Run: `npm run build --prefix frontend`

Expected: exit 0 and `frontend/dist/` remains ignored.

- [x] **Step 5: 提交前端恢复**

```powershell
git add -- frontend
git commit -m "feat: restore Vue frontend source"
```

## Task 4：恢复可复现的评测资产

**学习检查点：** 区分测试集、评测程序、历史报告和当前验证证据；说明为什么旧 JSON 报告存在不等于当前版本已经通过评测。

**Files:**
- Create: `evaluation/data_correction/*.py`
- Create: `evaluation/data_correction/README.md`
- Create: `evaluation/data_correction/rules/*.json`
- Create: `evaluation/data_correction/outputs/kb_corrected_v2.json`
- Create: `evaluation/data_correction/reports/kb_corrected_v2.*.json`
- Create: `evaluation/quality_eval/*.py`
- Create: `evaluation/quality_eval/datasets/fta_eval_seed.json`
- Create: `evaluation/quality_eval/eval_dataset_template.json`
- Create: selected files under `evaluation/quality_eval/runs/`
- Modify: `evaluation/data_correction/ai_quality_evaluator.py`
- Modify: `evaluation/quality_eval/build_eval_dataset.py`

- [x] **Step 1: 复制评测程序、数据集和精选基线**

```powershell
$legacyEval = Join-Path $env:FTA_LEGACY_ROOT 'evaluation'
New-Item -ItemType Directory -Force evaluation/data_correction/rules, evaluation/data_correction/outputs, evaluation/data_correction/reports, evaluation/quality_eval/datasets, evaluation/quality_eval/runs | Out-Null
Copy-Item -LiteralPath "$legacyEval\data_correction\ai_quality_evaluator.py", "$legacyEval\data_correction\apply_data_corrections.py", "$legacyEval\data_correction\README.md" -Destination evaluation/data_correction/
Copy-Item -LiteralPath "$legacyEval\data_correction\rules\correction_rules.template.json", "$legacyEval\data_correction\rules\correction_rules.v2.json" -Destination evaluation/data_correction/rules/
Copy-Item -LiteralPath "$legacyEval\data_correction\outputs\kb_corrected_v2.json" -Destination evaluation/data_correction/outputs/
Copy-Item -LiteralPath "$legacyEval\data_correction\reports\kb_corrected_v2.ai_quality.json", "$legacyEval\data_correction\reports\kb_corrected_v2.report.json" -Destination evaluation/data_correction/reports/
Copy-Item -LiteralPath "$legacyEval\quality_eval\build_eval_dataset.py", "$legacyEval\quality_eval\event_logic_eval.py", "$legacyEval\quality_eval\render_eval_chart.py", "$legacyEval\quality_eval\render_event_logic_chart.py", "$legacyEval\quality_eval\render_improvement_template_chart.py", "$legacyEval\quality_eval\run_eval_benchmark.py", "$legacyEval\quality_eval\eval_dataset_template.json" -Destination evaluation/quality_eval/
Copy-Item -LiteralPath "$legacyEval\quality_eval\datasets\fta_eval_seed.json" -Destination evaluation/quality_eval/datasets/
Copy-Item -LiteralPath "$legacyEval\quality_eval\runs\metric_report_20260331_122935.json", "$legacyEval\quality_eval\runs\metric_report_20260331_122935_chart_refined.png", "$legacyEval\quality_eval\runs\event_logic_report_20260331_134338.json", "$legacyEval\quality_eval\runs\event_logic_report_20260331_134338_chart.png" -Destination evaluation/quality_eval/runs/
```

- [x] **Step 2: 修复评测脚本对 Python 后端的导入路径**

At the top of `evaluation/data_correction/ai_quality_evaluator.py`, use:

```python
PROJECT_ROOT = Path(__file__).resolve().parents[2]
BACKEND_ROOT = PROJECT_ROOT / "backend-python"
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))
```

In `evaluation/quality_eval/build_eval_dataset.py`, change the optional runtime-output source to:

```python
output_dir = ROOT / "backend-python" / "outputs"
```

- [x] **Step 3: 运行无模型调用的评测入口检查**

Run: `python evaluation/data_correction/apply_data_corrections.py --help`

Expected: exit 0 and usage text.

Run: `python evaluation/quality_eval/run_eval_benchmark.py --help`

Expected: exit 0 and usage text.

Run: `python evaluation/quality_eval/event_logic_eval.py --help`

Expected: exit 0 and usage text.

- [x] **Step 4: 扫描数据集中的敏感模式**

Run:

```powershell
rg -n -i "api[_-]?key|secret|token|password|BEGIN (RSA |OPENSSH |EC )?PRIVATE KEY|@[a-z0-9.-]+\.[a-z]{2,}" evaluation
```

Expected: no credential or personal-email matches. Domain words such as model `token` counts must be manually classified and recorded as non-secret.

- [x] **Step 5: 提交评测资产**

```powershell
git add -- evaluation
git commit -m "test: restore FTA evaluation assets"
```

## Task 5：建立可复现依赖和入口文档

**学习检查点：** 说明“依赖范围”“锁文件”“运行时外部程序”分别解决什么问题，以及为什么 Graphviz 可执行文件不能只写进 Python 依赖。

**Files:**
- Create: `backend-python/requirements.txt`
- Create: `README.md`
- Modify: `docs/api-usage.md`
- Modify: `docs/project-overview.md`
- Modify: `docs/archive/legacy-docker-deployment.md`

- [x] **Step 1: 在隔离环境安装实际依赖并生成快照**

```powershell
python -m venv .venv
& .\.venv\Scripts\python.exe -m pip install --upgrade pip
& .\.venv\Scripts\python.exe -m pip install fastapi "uvicorn[standard]" pydantic python-multipart openai httpx neo4j pypdf python-docx openpyxl pillow
& .\.venv\Scripts\python.exe -m pip freeze | Set-Content -Encoding utf8 backend-python/requirements.txt
```

Expected: all commands exit 0; `.venv/` remains ignored.

- [x] **Step 2: 验证干净环境能够导入 API**

Run:

```powershell
& .\.venv\Scripts\python.exe -c "import sys; sys.path.insert(0, 'backend-python'); import api_server; print(api_server.app.title)"
```

Expected: prints `AI FTA API` without contacting the model or requiring Neo4j to be online.

- [x] **Step 3: 写根 README 的真实启动闭环**

`README.md` must contain these commands and explain that Graphviz and Neo4j are optional runtime integrations:

```powershell
python -m venv .venv
& .\.venv\Scripts\python.exe -m pip install -r backend-python/requirements.txt
Copy-Item backend-python/.env.example backend-python/.env
& .\.venv\Scripts\python.exe -m uvicorn api_server:app --app-dir backend-python --host 127.0.0.1 --port 8000
npm ci --prefix frontend
npm run serve --prefix frontend
```

The README must label historical evaluation metrics as archived evidence and link to the exact selected JSON reports.

- [x] **Step 4: 修正文档漂移**

Update `docs/api-usage.md` to use `backend-python/` and remove the machine-specific Conda path. Mark `docs/archive/legacy-docker-deployment.md` as non-current because the repository has no verified Docker configuration. Update `docs/project-overview.md` so every referenced evaluation path exists after migration.

- [x] **Step 5: 提交依赖和文档**

```powershell
git add -- README.md backend-python/requirements.txt docs
git commit -m "docs: add reproducible monorepo setup"
```

## Task 6：执行完整迁移验收

**学习检查点：** 让用户判断每条命令证明了哪一层事实：语法、依赖导入、业务回归、前端构建、仓库卫生；强调单条绿色命令不能证明整个系统可用。

**Files:**
- Modify only if a verification failure identifies a migration regression.

- [x] **Step 1: 运行结构与漂移门禁**

Run: `python scripts/verify_repo_layout.py`

Expected: `repository layout verified`.

Run: `rg -n "C:[\\/]|/Users/|app\.py|vue/vue-1/vue-demo" README.md docs backend-python frontend evaluation -g '!docs/archive/**'`

Expected: no active-document or source-code matches. Matches in sample fault text must be manually classified.

- [x] **Step 2: 运行 Python 验收**

Run: `& .\.venv\Scripts\python.exe -m compileall -q backend-python evaluation`

Expected: exit 0.

Run: `$env:PYTHONUTF8='1'; & .\.venv\Scripts\python.exe backend-python/fta_regression_check.py`

Expected: the documented baseline of three passes and one known AOCS failure. This is migration equivalence evidence, not product-quality acceptance.

Run: `& .\.venv\Scripts\python.exe -c "import sys; sys.path.insert(0, 'backend-python'); import api_server; print(len(api_server.app.routes))"`

Expected: a positive route count and exit 0.

- [x] **Step 3: 运行 Vue 验收**

Run: `npm run build --prefix frontend`

Expected: exit 0 with no compile errors.

Run: `git status --short --ignored | Select-String 'frontend/(node_modules|dist)'`

Expected: both directories appear only as ignored entries.

- [x] **Step 4: 运行 Git 与敏感信息审计**

Run: `git status --short`

Expected: clean before final review commit.

Run: `git ls-files | rg "(^|/)(\.env|__pycache__|outputs|dist|\.vscode)(/|$)"`

Expected: no matches except `backend-python/.env.example` is intentionally allowed and therefore checked separately.

Run:

```powershell
git grep -n -I -E "(sk-[A-Za-z0-9_-]{20,}|BEGIN (RSA |OPENSSH |EC )?PRIVATE KEY|api[_-]?key[[:space:]]*=[[:space:]]*[^[:space:]\"']+)" -- . ':(exclude)backend-python/.env.example'
```

Expected: no secret matches.

- [x] **Step 5: 检查分支差异和提交边界**

Run: `git diff --check main...HEAD`

Expected: no whitespace errors.

Run: `git diff --stat main...HEAD`

Expected: changes are limited to repository organization, recovered frontend/evaluation assets, reproducibility files and docs.

Run: `git log --oneline --decorate main..HEAD`

Expected: small commits corresponding to design, guard, backend move, frontend recovery, evaluation recovery and docs.

## Task 7：用户复核与远程边界

**执行记录（2026-09-12）：** Task 1-6 已在 `refactor/v2-monorepo` 本地分支闭合。结构门禁、隔离依赖、Python 编译/API 导入、手工无外部依赖生成、Vue 构建、生产依赖审计和 Git/敏感信息审计通过；FTA 回归保持迁移前的 3/4 基线，AOCS 仍失败。完整 Vue 开发依赖审计、构建体积告警、在线模型/Neo4j、真实浏览器和部署验收仍按 `docs/known-issues.md` 记录，不作为已通过事实。尚未推送远程。

**学习检查点：** 解释本地分支、远程分支、Pull Request 和 `main` 的关系，让用户能够说清楚代码何时真正对外可见。

**Files:**
- No source changes unless the user requests corrections after reviewing the diff.

- [ ] **Step 1: 向用户展示最终事实**

Report:

- exact branch and commit list;
- directories and files moved, restored, excluded and deleted;
- Python import, regression and Vue build results;
- known AOCS regression failure;
- the 22 MB background video and its unresolved public-license decision;
- historical evaluation reports were restored but not rerun as current evidence;
- no push has occurred.

- [ ] **Step 2: 等待明确的推送授权**

Do not run `git push` until the user reviews the complete diff scope, confirms whether the background video may be public, and explicitly authorizes pushing `refactor/v2-monorepo`.
