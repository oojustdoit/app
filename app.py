from flask import Flask
# 1. 导入 PrometheusMetrics
from prometheus_flask_exporter import PrometheusMetrics

app = Flask(__name__)

# 2. 初始化 PrometheusMetrics，并关联到 app
#    这一步会自动为所有路由添加默认的监控指标[reference:2]
metrics = PrometheusMetrics(app)

# (可选) 添加一些静态的应用信息作为指标[reference:3]
metrics.info('app_info', 'Application info', version='1.0.0')

@app.route('/')
def hello():
    return "Hello DevOps! 我的第一个容器化应用"

if __name__ == '__main__':
    # 3. 确保监听 0.0.0.0，使 Prometheus 能访问到
    app.run(host='0.0.0.0', port=5000)
