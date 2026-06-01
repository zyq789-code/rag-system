"""直接启动 Celery Worker，绕开终端编码问题"""
from celery.apps.worker import Worker
from tasks.celery_app import celery_app

worker = Worker(
    app=celery_app,
    loglevel="INFO",
    pool="solo",
    without_gossip=True,
    without_mingle=True,
    without_heartbeat=True,
)

worker.start()
