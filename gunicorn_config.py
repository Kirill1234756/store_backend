import multiprocessing
import os

# Базовые настройки
bind = "unix:/run/gunicorn.sock"
workers = multiprocessing.cpu_count() * 2 + 1
threads = 2
worker_class = "gthread"
worker_connections = 1000
timeout = 60
keepalive = 5

# Логирование
accesslog = "logs/gunicorn-access.log"
errorlog = "logs/gunicorn-error.log"
loglevel = "info"

# Безопасность
user = "www-data"
group = "www-data"

# Перезагрузка
max_requests = 1000
max_requests_jitter = 50
graceful_timeout = 30

# SSL (если используется)
# keyfile = "/path/to/keyfile"
# certfile = "/path/to/certfile"

# Предзагрузка приложения
preload_app = True

def post_fork(server, worker):
    server.log.info("Worker spawned (pid: %s)", worker.pid)

def pre_fork(server, worker):
    pass

def pre_exec(server):
    server.log.info("Forked child, re-executing.")

def when_ready(server):
    server.log.info("Server is ready. Spawning workers")

def worker_int(worker):
    worker.log.info("worker received INT or QUIT signal")

def worker_abort(worker):
    worker.log.info("worker received SIGABRT signal") 