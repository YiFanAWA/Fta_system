# 历史 Docker 部署说明（非当前方案）

> 本文仅用于保留旧项目记录。当前仓库没有对应的 Dockerfile、`ziliao.tar`、`app.py` 或经过验证的镜像构建链路，以下命令不可作为当前部署说明。重新启用 Docker 前，应以现有 `backend-python/api_server.py` 和 `frontend/` 为入口设计并验证新的部署合同。

## 旧说明：提供可部署的 Docker 镜像文件

在此次任务中，本团队也提供了可快速部署的 Docker 镜像文件。Docker 镜像包含了应用程序所需要的所有配置环境和依赖项，确保了应用程序在不同环境中的行为一致性。其采取分层存储和增量更新的方式，使得镜像的创建、存储和传输都非常高效。多个镜像可以共享相同的底层文件系统，进一步减少了存储空间的需求。

本项目镜像文件名为 `ziliao.tar`，以百度网盘共享链接给出。对于 Docker 镜像加载，按如下顺序依次输入指令，即可启动项目。

## 2.1 启动步骤

1. 加载镜像ziliao

```bash
docker load -i ziliao.tar
```

2. 创建容器

```bash
docker run -it --name demo-p -p 8003:8003 ziliao /bin/bash
```

3. 进入容器目录

```bash
cd /demo
```

4. 启动应用

```bash
python3 app.py
```

默认启动端口号为 `8080`。

## 2.2 访问地址

应用启动后，浏览器访问：

```text
http://127.0.0.1:8080
```

## 2.3 补充说明

- 若终端支持输入重定向，也可使用 `docker load < ziliao.tar`。
- 创建容器时端口映射需要使用 `-p` 参数。
- 若 `demo-p` 容器名已存在，可先执行：

```bash
docker rm -f demo-p
```
