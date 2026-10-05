from apscheduler.schedulers.background import BackgroundScheduler

from .core import surface

scheduler = BackgroundScheduler()


def start() -> None:
    if not scheduler.running:
        scheduler.add_job(lambda: surface("default"), "interval", weeks=1, id="surface", replace_existing=True)
        scheduler.start()


def stop() -> None:
    if scheduler.running:
        scheduler.shutdown(wait=False)
