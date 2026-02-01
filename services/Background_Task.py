from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from db.models import CallOutcome, Task_Manager
from db.database import SessionLocal
from db.crud import _update_error

from Memory_Functions import add_memory, get_caller_context, format_caller_context
from services.Analyze_Webhook import CallSummaryScan

from openai import OpenAI
from dotenv import load_dotenv

from services.outbound_test import start_call
from apscheduler.triggers.date import DateTrigger
import pytz

from services.scheduler import get_scheduler

load_dotenv()

client = OpenAI()
analyzer = CallSummaryScan(client)


def process_webhook_pipeline(call_id: str, agent_id: str, from_phone: str, to_phone: str, summary: str):
    """
    Processes a call webhook:
    1. Analyze the call summary
    2. Store memory in Supermemory
    3. Schedule a callback if needed
    4. Update DB task
    """
    try:
        with SessionLocal() as db:

            try:
                analysis = analyzer.analyze(summary)
                outcome: CallOutcome = analysis.outcome
                callback_time_dt = analysis.callback_time_iso  # datetime object
                callback_time_str = callback_time_dt.strftime("%Y-%m-%d %H:%M") if callback_time_dt else None
                print(f"[ANALYSIS] Summary analyzed: outcome={outcome}, callback_time={callback_time_str}")
            except Exception as analysis_err:
                _update_error(db, call_id, f"Analysis Error: {analysis_err}")
                return

            try:
                if outcome != CallOutcome.MISSED:
                    memory_content = (
                        f"Call with {to_phone}.\n"
                        f"Outcome: {outcome.value}\n"
                        f"Summary: {summary}"
                    )

                    payload = {
                        "entity_id": to_phone,        
                        "call_id": call_id,
                        "phone": to_phone,
                        "callback_time": callback_time_str,
                        "summary": memory_content,
                    }

                    add_memory(payload)
                    print(f"[MEMORY] Memory added for {to_phone}")
            except Exception as api_err:
                _update_error(db, call_id, f"Memory API Error: {api_err}")
                return

          
            if callback_time_dt and outcome.value == CallOutcome.CALLBACK.value:
                schedule_callback(call_id, agent_id, from_phone, to_phone, callback_time_dt)
                print(f"[SCHEDULER] Callback scheduled at {callback_time_str}")
            else:
                print("[SCHEDULER] No callback to schedule")

    
            try:
                db_task = db.query(Task_Manager).filter_by(call_id=call_id).first()
                if db_task:
                    db_task.outcome = outcome
                    db_task.callback_time = callback_time_str
                    db_task.processed = True
                    db_task.last_error = None
                    db.commit()
                    print(f"[DB] Task updated for call_id={call_id}")
            except Exception as db_err:
                print(f"[DB ERROR] Failed to update task: {db_err}")

    except Exception as e:
        print(f"[CRITICAL] process_webhook_pipeline failed: {e}")


def schedule_callback(call_id: str, agent_id: str, from_phone: str, to_phone: str, callback_time: datetime):
    """
    Schedule a callback using APScheduler
    """
    scheduler = get_scheduler()
    try:
        local_tz = pytz.timezone('America/Detroit')


        if callback_time.tzinfo is None:
            callback_time = local_tz.localize(callback_time)
        else:
            callback_time = callback_time.astimezone(local_tz)

        now_local = datetime.now(local_tz)
        print(f"[SCHEDULER DEBUG] Callback time: {callback_time}, Now: {now_local}")

        # If callback time is in the past, schedule a few seconds ahead
        if callback_time <= now_local:
            print("[SCHEDULER WARNING] Callback time is in the past, scheduling immediately (+5s)")
            callback_time = now_local + timedelta(seconds=5)

 
        job = scheduler.add_job(
            func=start_call,
            trigger=DateTrigger(run_date=callback_time),
            args=[from_phone, to_phone, agent_id],
            id=f"callback_{call_id}",
            replace_existing=True,
            misfire_grace_time=300
        )

        print(f"[SCHEDULER] Callback scheduled for {to_phone}")
        print(f"[SCHEDULER] Next run: {job.next_run_time}")

        # debug all scheduled jobs
        all_jobs = scheduler.get_jobs()
        print(f"[SCHEDULER] Total scheduled jobs: {len(all_jobs)}")
        for j in all_jobs:
            print(f"[SCHEDULER] - {j.id} -> {j.next_run_time}")

    except Exception as e:
        print(f"[SCHEDULER ERROR] Failed to schedule callback: {e}")
        import traceback
        traceback.print_exc()
