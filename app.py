from flask import Flask
from prometheus_flask_exporter import PrometheusMetrics

app = Flask(__name__)

# 初始化 Prometheus 监控
# 会自动为所有路由添加请求数、响应时间、异常等指标
metrics = PrometheusMetrics(app)

# 添加一个自定义的应用信息指标（可选）
metrics.info('app_info', 'Application info', version='1.0.0')

@app.route('/')
def hello():
    return "Hello DevOps! 我的第一个容器化应用 (监控已集成)"

if __name__ == '__main__':
    # 必须绑定 0.0.0.0，否则容器外部无法访问
    app.run(host='0.0.0.0', port=5000)
