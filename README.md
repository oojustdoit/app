# 🚀 DevOps 部署配置设计流程 —— Flask 应用全链路 CI/CD 与监控

## 📖 项目简介

本项目是一个基于 **Flask** 的 Web 应用示例，旨在演示从代码提交到生产部署的完整 DevOps 实践。通过容器化、持续集成、持续部署、监控告警等技术栈，构建了一套可扩展、可观测的自动化运维体系。

- **技术栈**：Python Flask + Docker + GitHub Actions + Docker Hub + Prometheus + Grafana
- **运行环境**：阿里云 ECS（Ubuntu 20.04）
- **核心目标**：实现「代码推送即部署，部署即验证，验证即监控」的全自动闭环。

---

## 📁 项目目录结构

```
devops-demo/
├── app.py                          # Flask 应用主程序（已集成 Prometheus metrics）
├── requirements.txt                # Python 依赖（含 prometheus-flask-exporter）
├── Dockerfile                      # 容器镜像构建文件
├── .github/
│   └── workflows/
│       └── build-and-deploy.yml    # CI/CD 流水线定义
├                    # 监控栈独立部署
│── docker-compose.yml          # Prometheus + Grafana 编排
│── prometheus.yml              # Prometheus 抓取配置
└── README.md                       # 本文档
```

---

## 🔧 1. 应用容器化设计

### 1.1 基础镜像与依赖管理
- 使用 `python:3.9-slim` 作为基础镜像，减小体积。
- 分层复制 `requirements.txt` 并安装依赖，利用 Docker 缓存加速构建。
- 设置国内 PyPI 镜像源（清华源）避免下载超时。

### 1.2 暴露监控端点
- 引入 `prometheus-flask-exporter` 库，自动为 Flask 路由生成 `/metrics` 端点。
- 该端点提供 HTTP 请求数、响应时间、异常计数等核心指标，供 Prometheus 抓取。

### 1.3 容器运行规范
- 应用监听 `0.0.0.0:5000`，确保容器内外可访问。
- 容器运行命令为 `python app.py`（开发模式，生产环境可替换为 Gunicorn）。

---

## 🔁 2. CI/CD 流水线设计（GitHub Actions）

### 2.1 触发条件
- 当代码推送到 `main` 分支时自动触发。

### 2.2 构建阶段（Build）
- 登录 Docker Hub（使用存储在 GitHub Secrets 中的用户名和 Access Token）。
- 构建 Docker 镜像，并同时打上两个标签：
  - `latest`：表示最新稳定版。
  - `${{ github.sha }}`：唯一版本标识，用于回滚和版本追踪。

### 2.3 部署阶段（Deploy via SSH）
通过 `appleboy/ssh-action` 远程登录目标服务器，执行以下脚本：

```bash
# 1. 拉取指定版本镜像
docker pull muzioooo/my-first-app:$IMAGE_TAG

# 2. 蓝绿部署：先启动新容器在 5001 端口
docker run -d -p 5001:5000 --name my-app-new muzioooo/my-first-app:$IMAGE_TAG

# 3. 健康检查新容器（最多30秒）
for i in {1..30}; do
  curl -f http://localhost:5001 && break
  sleep 1
done

# 4. 若健康，则停止旧容器，重命名为 my-running-app 并映射到 5000 端口
docker stop my-running-app || true
docker rm my-running-app || true
docker run -d -p 5000:5000 --name my-running-app muzioooo/my-first-app:$IMAGE_TAG

# 5. 清理临时新容器
docker stop my-app-new || true
docker rm my-app-new || true

# 6. 最终健康检查（验证 5000 端口服务可用）
for i in {1..30}; do
  curl -f http://localhost:5000 && exit 0
  sleep 1
done
exit 1  # 失败则流水线报错
```

### 2.4 部署策略特点
- **蓝绿部署**：新版本先启动在备用端口，验证通过后再切换流量，最大限度降低中断。
- **健康检查**：部署前后均执行 HTTP 探测，确保服务可用性，否则回滚（流水线失败）。
- **版本固化**：每次部署使用 commit SHA 作为镜像标签，便于快速回滚至任意历史版本。

---

## 📦 3. 镜像仓库与版本管理

- **镜像仓库**：Docker Hub（公开仓库 `muzioooo/my-first-app`）。
- **标签策略**：
  - `latest`：始终指向最新成功构建的版本。
  - `<commit-sha>`：每个 commit 的唯一镜像，支持精准回滚。
- **回滚操作**：若新版本异常，只需在服务器手动执行：
  ```bash
  docker pull muzioooo/my-first-app:<old-sha>
  docker run -d -p 5000:5000 --name my-running-app muzioooo/my-first-app:<old-sha>
  ```

---

## 📊 4. 监控体系设计（Prometheus + Grafana）

### 4.1 部署架构
- 监控组件独立运行在 `monitoring/` 目录下，通过 Docker Compose 编排。
- Prometheus 负责时序数据采集，Grafana 负责可视化展示。

### 4.2 Prometheus 配置
- 配置 `prometheus.yml`，定义抓取任务：
  ```yaml
  scrape_configs:
    - job_name: 'flask-app'
      static_configs:
        - targets: ['<服务器内网IP>:5000']   # 从 Flask 的 /metrics 拉取数据
  ```
- 采集频率：15 秒。

### 4.3 Grafana 仪表盘
- 导入社区仪表盘（ID `9688` 或 `10915`）快速展示应用性能指标。
- 关键指标面板：
  - HTTP 请求速率（QPS）
  - 请求延迟分布（P50, P95, P99）
  - HTTP 状态码比例（2xx/4xx/5xx）
  - 活跃连接数等。

### 4.4 数据流示意
```
Flask App (/metrics)  -->  Prometheus (pull)  -->  Grafana (query & visualize)
```

---

## 🔐 5. 安全与密钥管理

- **GitHub Secrets** 存储敏感信息：
  - `DOCKER_USERNAME`：Docker Hub 用户名
  - `DOCKER_PASSWORD`：Docker Hub Access Token（非登录密码）
  - `SERVER_HOST`：服务器公网 IP
  - `SERVER_USERNAME`：服务器登录用户名（通常为 root）
  - `SERVER_SSH_KEY`：用于 SSH 登录的私钥（部署专用）
- 所有 Secrets 仅在 Actions 运行期间加密传递，不写入日志。

---

## 🖥️ 6. 服务器环境准备

### 6.1 基础环境
- 安装 Docker 及 Docker Compose。
- 配置国内镜像加速器（阿里云/中科大）以加速镜像拉取。

### 6.2 防火墙与安全组
- 开放端口：
  - `5000`：应用服务端口（供用户访问）
  - `9090`：Prometheus 管理界面（可限制内网访问）
  - `3000`：Grafana 界面（可限制内网访问）
- 阿里云安全组需添加相应入方向规则。

### 6.3 部署专用 SSH 密钥
- 生成一对新密钥 `~/.ssh/github_actions_deploy`，并将公钥加入 `~/.ssh/authorized_keys`，避免 Actions 每次需要密码。

---

## 🧪 7. 测试与验证

### 7.1 本地验证
- 构建镜像：`docker build -t my-app .`
- 运行容器：`docker run -p 5000:5000 my-app`
- 访问 `http://localhost:5000` 查看应用；访问 `/metrics` 查看指标。

### 7.2 端到端 CI/CD 测试
1. 修改 `app.py` 并提交到 main 分支。
2. 观察 GitHub Actions 运行状态。
3. 访问服务器 IP 查看更新是否生效。
4. 检查 Grafana 是否出现新的数据点。

### 7.3 回滚测试
- 在服务器上手动运行旧版本镜像，验证切换过程是否顺利。

---

## 🛠️ 8. 维护与扩展建议

- **扩展监控指标**：在 Flask 代码中添加自定义业务指标（如用户操作计数）。
- **告警配置**：通过 Alertmanager 设置告警规则（如请求错误率 > 5% 触发通知）。
- **日志集中管理**：引入 ELK Stack 或 Loki 收集容器日志。
- **高可用部署**：使用 Kubernetes 替代单机 Docker，提升弹性和自愈能力。
- **镜像仓库升级**：迁移到阿里云 ACR 或 Harbor，提高拉取速度及安全性。

---

## 📚 9. 参考资源

- [Prometheus Flask Exporter 官方文档](https://github.com/rycus86/prometheus_flask_exporter)
- [GitHub Actions 文档](https://docs.github.com/actions)
- [Docker 官方文档](https://docs.docker.com)
- [Grafana 仪表盘共享社区](https://grafana.com/grafana/dashboards)

---

## 📝 结语

通过本项目，我们实现了从代码提交到生产监控的全链路自动化，涵盖了 DevOps 核心要素：**CI/CD、容器化、版本管理、健康检查、可观测性**。这套设计模式可轻松移植到其他语言或框架，为团队提供稳定高效的交付基础设施。

如果你有任何问题或改进建议，欢迎提交 Issue 或 Pull Request！

---

**项目维护者**：[@oojustdoit](https://github.com/oojustdoit)  
**最后更新**：2026-06-24
