# gunicorn.conf.py — конфигурация для Render

import os

# Bind
port = int(os.environ.get("PORT", 10000))
bind = f"0.0.0.0:{port}"

# Workers: 2 × CPU + 1 (Render Free даёт 0.1 CPU — минимум 2 worker)
workers = int(os.environ.get("WEB_CONCURRENCY", 2))
worker_class = "sync"
threads = 2
timeout = 120
keepalive = 5

# Logging
accesslog = "-"   # stdout
errorlog  = "-"   # stderr
loglevel  = os.environ.get("LOG_LEVEL", "info")

# Security
forwarded_allow_ips = "*"          # Render проксирует через load balancer
proxy_protocol      = False
