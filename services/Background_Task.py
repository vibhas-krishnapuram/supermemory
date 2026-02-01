from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from db.models import CallOutcome, Task_Manager
from db.database import SessionLocal
from db.crud import _update_error

from .Memory_Functions import add_memory, get_caller_context, format_caller_context
from services.Analyze_Webhook import CallSummaryScan

from openai import OpenAI
from dotenv import load_dotenv

from services.outbound_test import start_call
from apscheduler.triggers.date import DateTrigger
import pytz

from services.scheduler import get_scheduler
from dateutil.parser import parse as parse_dt

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
    db = SessionLocal()
    
    try:
        # ============= ANALYSIS =============
        try:
            analysis = analyzer.analyze(summary)
            outcome: CallOutcome = analysis.outcome
            callback_time_dt = analysis.callback_time_iso
            callback_time_str = callback_time_dt.strftime("%Y-%m-%d %H:%M") if callback_time_dt else None
            print(f"[ANALYSIS] Summary analyzed: outcome={outcome}, callback_time={callback_time_str}")
        except Exception as analysis_err:
            print(f"[ANALYSIS ERROR] {analysis_err}")
            import traceback
            traceback.print_exc()
            outcome = None
            callback_time_str = None
            callback_time_dt = None

        # ============= MEMORY =============
        try:
            if outcome and outcome not in [CallOutcome.MISSED, CallOutcome.NOT_INTERESTED]:
                memory_content = (
                    f"Call with {to_phone}.\n"
                    f"Outcome: {outcome.value}\n"
                    f"Summary: {summary}"
                )

                # Build payload - only include callback_time if it's not None
                payload = {
                    "entity_id": to_phone,
                    "call_id": call_id,
                    "phone": to_phone,
                    "summary": memory_content,
                }
                
                # Only add callback_time if it exists
                if callback_time_str:
                    payload["callback_time"] = callback_time_str

                add_memory(payload)
                print(f"[MEMORY] Memory added for {to_phone}")
        except Exception as api_err:
            print(f"[MEMORY ERROR] {api_err}")
            import traceback
            traceback.print_exc()
            # DON'T RETURN - continue to DB update

        # ============= SCHEDULER =============
        callback_time_dt = analysis.callback_time_iso

        # Ensure it's a datetime object
        if isinstance(callback_time_dt, str):
            callback_time_dt = parse_dt(callback_time_dt)

        callback_time_str = callback_time_dt.strftime("%Y-%m-%d %H:%M") if callback_time_dt else None
        
        if outcome and callback_time_dt and outcome == CallOutcome.CALLBACK:
            try:
                schedule_callback(call_id, agent_id, from_phone, to_phone, callback_time_dt)
                print(f"[SCHEDULER] Callback scheduled at {callback_time_str}")
            except Exception as sched_err:
                print(f"[SCHEDULER ERROR] {sched_err}")
                import traceback
                traceback.print_exc()
                # DON'T RETURN - continue to DB update
        else:
            print("[SCHEDULER] No callback to schedule")

        # ============= DATABASE UPDATE =============
        try:
            db_task = db.query(Task_Manager).filter_by(call_id=call_id).first()
            
            if db_task:
                print(f"[DB] Found existing task for call_id={call_id}")
                print(f"[DB] Current outcome in DB: {db_task.outcome}")
                
                db_task.outcome = outcome
                db_task.callback_time = callback_time_str
                db_task.processed = True
                db_task.last_error = None
                
                print(f"[DB] About to commit - setting outcome to: {outcome}")
            else:
                print(f"[DB WARNING] No task found for call_id={call_id}, creating new one")
                db_task = Task_Manager(
                    call_id=call_id,
                    outcome=outcome,
                    callback_time=callback_time_str,
                    processed=True,
                    last_error=None
                )
                db.add(db_task)
            
            print(f"[DB] Committing changes to database...")
            db.commit()
            
            # Verify it saved
            db.refresh(db_task)
            print(f"[DB] SUCCESS! Committed to database")
            print(f"[DB] Verified outcome in DB: {db_task.outcome}")
            print(f"[DB] Verified callback_time in DB: {db_task.callback_time}")
            print(f"[DB] Verified processed in DB: {db_task.processed}")
            
        except Exception as db_err:
            print(f"[DB ERROR] Failed to update database: {db_err}")
            import traceback
            traceback.print_exc()
            db.rollback()

    except Exception as e:
        print(f"[CRITICAL ERROR] process_webhook_pipeline failed: {e}")
        import traceback
        traceback.print_exc()
        if db:
            db.rollback()
    finally:
        if db:
            db.close()


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
            kwargs={"is_callback": True},  # Pass is_callback flag
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