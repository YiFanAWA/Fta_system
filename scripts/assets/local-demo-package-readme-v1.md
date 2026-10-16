# FTA System 本地离线演示候选包

本目录只供当前用户本地研究/演示，不是公开发布包，也不是已经完成 M4 验收的独立环境。不得上传整包或转授素材许可。原始数据/媒体权利仍待确认；文件可读取不等于许可获批。

## 能做什么

沿用 M3 已验收的离线入口：查看工作台、提交有来源的 F35400/F06000 语义候选进行只读校验、查看证据与阻断。不自动调用模型。RAG、抽取及正式建树请求会返回明确的“能力未启用”，不伪造答案。F35400 仍限定消息触发判据，F06000 仍阻断，不提供全量可信 FTA 或定量概率。

## 目录与职责

| 路径 | 用途 |
| --- | --- |
| `scripts/start_local_demo.py` | 唯一推荐离线启动入口；端口、服务时限、解释器检查 |
| `scripts/local_demo_runtime.py` | 指纹/工作目录隔离、同源和请求预算；不是故障语义 owner |
| `scripts/local_demo_windows.py` | Windows 专属进程归属、退出与资源限制 |
| `backend-python/app` | 既有 FastAPI 组合/协议接线 |
| `backend-python/contracts` | 抽取、证据、审核、语义候选的共享合同 |
| `backend-python/core` | 配置、模型客户端端口和基础工具 |
| `backend-python/extraction` | 既有抽取/审核/放行与持久化应用服务；本离线宿主未开放写工作流 |
| `backend-python/domains`、`rag` | 领域适配、检索/证据型回答的既有实现；本包不带权重，不启用在线问答 |
| `backend-python/fta`、`workflows` | 语义校验/投影及既有编排；不替代专家因果/门型审核 |
| `backend-python/requirements.txt` | 固定版本的基础应用依赖；不含大模型检索依赖 |
| `evaluation/quality_eval/datasets` | 仅两份具名冻结 S210 数据/关系；不是整个评测库 |
| `evaluation/quality_eval/runs` | 仅启动必需的指纹/配置资料及两个原样 Preview 样例，不包含评测执行代码/模型响应历史 |
| `evaluation/quality_eval/public_sources/retrieval_environment.yml` | 可选检索环境的历史参考，不是完整传递依赖锁；本离线演示不安装它 |
| `tmp/first_delivery_m3_mobile_layout_build_v1` | 已验收的 33 个前端构建文件；名字中的 tmp 不表示可以任意清理 |
| `delivery-manifest.json` | 交付文件名、角色、字节数和 SHA-256；prepared 不表示 M4 已通过 |

为复用原样启动器和既有指纹，保留上述相对布局，不随意移动/改名。包内历史配置含来源机器的旧绝对路径，启动器会把数据/关系/数据库/cache 四类路径重新绑定到本包和独立工作目录；这些旧值不作为本机运行状态或授权。

## 环境准备（尚未执行安装验收）

仅 Windows；M3 实测解释器为 Python 3.11.15。应在本包根目录新建独立 `.venv`，不要复制旧 `.venv`，也不要用指向原仓库 site-packages 的 `.pth` 或环境变量冒充独立安装。明确选择 Python 3.11 解释器后，由操作者确认执行 `-m venv .venv`。

然后在本包根目录执行（可能需要下载依赖，须先确认联网/安装范围；生成候选包不会自动执行）：

```powershell
& ./.venv/Scripts/python.exe -B -X utf8 -m pip install -r backend-python/requirements.txt
& ./.venv/Scripts/python.exe -B -X utf8 -m pip check
& ./.venv/Scripts/python.exe -B -X utf8 scripts/start_local_demo.py --workspace tmp/my_demo --check
& ./.venv/Scripts/python.exe -B -X utf8 scripts/start_local_demo.py --workspace tmp/my_demo
```

只使用打印的 `http://127.0.0.1:端口`，在新隐私浏览器窗口打开，不用旧 Service Worker 缓存。默认 1800 秒后停止；Ctrl+C 正常退出；再次使用同一 workspace 保留独立记录。`--max-seconds` 范围 1～7200。端口被占会拒绝，不结束其他程序。

没有独立 `.venv` 时，借原仓库 Python 运行本包 CLI 会被正确拒绝；这不是独立启动通过。真正 M4 验收还要补齐新环境安装、搬迁后 HTTP/浏览器/退出重启和使用者确认。

不要创建 `.env` 或填 Key：本入口显式清空 Provider 配置、禁外联、禁模型下载。需要真实在线问答须另定受控调用范围与预算，旧 M3 的单次请求授权已消费。本包没有 Python 安装程序、wheelhouse、模型权重、node_modules 或离线自动安装器。

## 完整性与限制

每个具名文件必须与交付清单一致；缺失/改动/额外可执行文件均不应被当成原候选包。清单的 SHA 用于内容完整性，不是数字签名，也不认证来源可信或许可。原工作树的 `scripts/prepare_local_demo_package.py --destination <本目录绝对路径> --check` 可按可信源清单复核；不需要为了运行复制整个原仓库。

独立运行后产生的 `.venv` 和演示工作目录不属于原候选包静态指纹集合。后续完整性验收应区分运行产物，不把它们悄悄纳入发布材料。不要删除演示 SQLite 来“恢复”清单。

此版本未认证新机器安装、无限在线 RAG、公开分发、任意原文自动建树或生产运行。Gold、unknown、证据门禁和全局 `fta_ready=false`/`production_ready=false` 均不因打包改变。
