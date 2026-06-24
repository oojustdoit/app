# 1. 指定基础镜像（轻量级 Python 环境）
FROM python:3.9-slim

# 2. 设置容器内的工作目录
WORKDIR /app

# 3. 只复制依赖文件（利用 Docker 缓存加速）
COPY requirements.txt .

# 4. 安装依赖（换国内源，避免下载超时）
RUN pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

# 5. 复制所有项目代码进去
COPY . .

# 6. 容器启动时执行的命令
CMD ["python", "app.py"]

# 7. 声明容器监听端口（仅仅是文档说明）
EXPOSE 5000
