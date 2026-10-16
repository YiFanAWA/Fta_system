# FTA System 本地研究与演示交付说明

本目录是无密钥、未初始化的本地交付材料，不是公开发行版。仅供当前用户本地研究/演示：不得把本目录、原始手册数据或媒体整体上传公开仓库。源码推送与完整包交付是两件事。

## 已验证的范围

2026-10-16 已在当前 Windows 机器的独立目录中，新建 Python 3.11.15 虚拟环境、安装相同 36 个固定基础依赖，实跑离线 API、桌面/390 浏览器、两个原样样例、到期停止与重启同库保持。此次交付沿用相同运行源码/构建/数据，仅补齐离线依赖和本文说明。

这不证明另一台机器或任意 Python 版本都已通过，也不新增在线 RAG、原因/门型质量或生产成绩。真实 RAG 的历史单次验收不能复用成日常调用预算。

## 安装与唯一推荐启动入口

前提：Windows x64，已安装且明确选择 Python 3.11。不要复制旧 `.venv`，不要把旧 site-packages 挂进来。本包不带 Python 安装程序，不自动下载任何内容。

先进入本目录，用你确认的 Python 3.11 解释器检查**干净包**；以下第一条的 `python` 必须确实指向你选择的 3.11，无法确定时改成该解释器绝对路径，不采用隐式回退：

```powershell
python -B -X utf8 scripts/verify_local_demo_delivery.py
python -B -X utf8 -m venv .venv
$env:PIP_CONFIG_FILE = 'NUL'
$env:NETRC = 'NUL'
& ./.venv/Scripts/python.exe -B -X utf8 -m pip --isolated --disable-pip-version-check --no-input --keyring-provider disabled install --no-index --find-links dependencies/wheels --only-binary=:all: -r backend-python/requirements.txt
& ./.venv/Scripts/python.exe -B -X utf8 -m pip check
& ./.venv/Scripts/python.exe -B -X utf8 scripts/start_local_demo.py --workspace tmp/my_demo --check
& ./.venv/Scripts/python.exe -B -X utf8 scripts/start_local_demo.py --workspace tmp/my_demo
```

创建环境和安装步骤须逐项成功后再执行下一条，不在安装尚未结束时启动验收。36 个 wheel 已与官方 PyPI 大小/SHA 对账，不必联网安装。缺包、平台不匹配或校验失败就停止，不改版本、不复制旧环境。

使用终端打印的 `http://127.0.0.1:端口`，在新隐私浏览器窗口打开。不要用旧 Service Worker 缓存。默认 1800 秒后停止，Ctrl+C 可正常停止；`--max-seconds` 允许 1～7200。端口被占会拒绝，不结束其他程序。重启用同一个 workspace 保留独立记录。

安装/运行后会出现 `.venv` 与 `tmp/my_demo`，它们不是原始交付文件。全目录干净包检查应在初始化前执行；安装后启动器仍核验冻结运行资产和工作目录身份。不要为了恢复干净清单而删除演示数据库。

## 现在能做什么

- 进入工作台、导入具名原样 JSON，查看候选结构、证据和阻断。
- F35400 保持限定消息触发判据/仅供审阅；F06000 保持整树阻断，两者不是已批准的完整物理故障树。
- 在线问答、AI 抽取、正式建树等未开放路由明确返回能力未启用；不会偷偷调用模型或编造成功答案。

不要创建 `.env` 或填入 Key。本离线入口显式清空 Provider 配置、禁止外联/下载和子进程；不操作原业务库。不保证抵御同账号恶意改文件，也不认证旧浏览器缓存。

## 各目录的功能

| 文件夹 | 功能 |
| --- | --- |
| `backend-python/app` | 既有 FastAPI 组合与协议入口，不自行判断故障语义 |
| `backend-python/contracts` | 抽取、证据、审核、放行及候选语义的共享合同 |
| `backend-python/core` | 配置、模型客户端端口、日志及基础工具 |
| `backend-python/extraction` | 抽取、审核、持久化应用服务；本离线入口未开放其写工作流 |
| `backend-python/domains` | 领域数据适配和路由 |
| `backend-python/rag` | 检索、证据、关系展开与回答实现；本包无权重且默认不启用 |
| `backend-python/fta` | 因果/证据/逻辑边界校验和诊断投影；不替代专家放行 |
| `backend-python/workflows` | 既有阶段编排，不是共享语义的第二 owner |
| `scripts` | 原安全启动/进程管理，以及干净包校验工具 |
| `dependencies/wheels` | 36 项固定基础依赖的兼容 wheel；不是模型或旧虚拟环境 |
| `dependencies/wheelhouse-manifest.json` | wheel 的官方来源、版本、大小和 SHA |
| `evaluation/quality_eval/datasets` | 仅具名冻结 S210 上下文与关系，不是完整评测库 |
| `evaluation/quality_eval/runs` | 仅必要配置、指纹账和 F35400/F06000 原样请求，不带全量评测执行程序 |
| `tmp/first_delivery_m3_mobile_layout_build_v1` | 冻结前端构建，保留旧相对路径以复用原校验；不能随意清理 |
| `tmp/my_demo` | 启动后新建的独立源码镜像/演示记录；不随干净包交付 |

运行参数、数据与构建位置保留原相对布局，没有为了好看重排源码或复制第二套后端。历史配置中的旧绝对路径只作来源记录，启动器会重新绑定本包的数据、关系、cache 和新演示库。

## 完整性、许可与尚未证明的能力

`local-delivery-manifest.json` 列出全部交付文件。SHA 可发现字节变化，但不是数字签名或许可证明。可以把另行取得的清单 SHA 传给校验命令的 `--expected-manifest-sha`，不能只相信包内自报通过。

未带入任何旧虚拟环境、数据库、模型权重、node_modules、完整历史 runs 或密钥。图片/视频及手册数据的公开分发许可未确认；保留它们只为已确认的本地研究演示，不上传完整包。仓库历史已经存在的素材也不因此被追认许可。

当前仍不承诺无限在线 RAG、任意原文自动生成可信 FTA、概率计算或生产运行。unknown/断开节点/待审核与整树阻断必须保留，`fta_ready=false` 和 `production_ready=false` 不因交付改变。
