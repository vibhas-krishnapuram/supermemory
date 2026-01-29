from apscheduler.schedulers.background import BackgroundScheduler
import atexit

_scheduler = None

def get_scheduler():
    global _scheduler
    if _scheduler is None:
        _scheduler = BackgroundScheduler()
        _scheduler.start()
        atexit.register(lambda: _scheduler.shutdown())
        print("[SCHEDULER] Background scheduler started")
    return _scheduler
