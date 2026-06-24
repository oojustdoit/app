from flask import Flask
import os

app = Flask(__name__)

@app.route('/')
def hello():
    # 显示容器的主机名，稍后我们能看到K8s的Pod名称，这里先预热
    hostname = os.environ.get('HOSTNAME', '本地环境')
    return f"Hello DevOps! 我的第一个容器化应用 (容器ID: {hostname})"

if __name__ == '__main__':
    # 必须绑定 0.0.0.0，否则容器外部访问不到
    app.run(host='0.0.0.0', port=5000)
