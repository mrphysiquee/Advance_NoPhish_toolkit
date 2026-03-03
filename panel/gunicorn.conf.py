bind = "0.0.0.0:5000"
workers = 4
worker_class = "sync"
worker_connections = 1000
timeout = 30
keepalive = 2
max_requests = 1000
max_requests_jitter = 50
preload_app = False
accesslog = "-"
errorlog = "-"
loglevel = "info"
access_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s"'
raw_env = ["FLASK_ENV=production"]

# Security settings
limit_request_line = 4094
limit_request_fields = 100
limit_request_field_size = 8190