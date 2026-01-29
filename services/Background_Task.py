from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from db.models import CallOutcome, Task_Manager
from db.database import SessionLocal
from db.crud import _update_error

from Memory_Functions import add_memory, get_caller_context
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



def process_webhook_pipeline(call_id: str, agent_id: str, from_phone: str, phone: str, summary: str):

    try:
        with SessionLocal() as db:

            try:
                analysis = analyzer.analyze(summary)
                outcome: CallOutcome = analysis.outcome
                callback_time_dt = analysis.callback_time_iso  # Keep as datetime object
                callback_time_str = callback_time_dt.strftime("%Y-%m-%d %H:%M") if callback_time_dt else "No callback"
                print("Summary analysis done")
            except Exception as analysis_err:
                _update_error(db, call_id, f"Analysis Error: {analysis_err}")
                return

            print(f"[DEBUG] outcome = {outcome}, type = {type(outcome)}")
            print(f"[DEBUG] callback_time_dt = {callback_time_dt}, type = {type(callback_time_dt)}")
            print(f"[DEBUG] outcome = {outcome}, type = {type(outcome)}, value = {outcome.value}")
            print(f"[DEBUG] CALLBACK value = {CallOutcome.CALLBACK.value}")
            print(f"[DEBUG] outcome.value = {outcome.value}")
            print(f"[DEBUG] CallOutcome.CALLBACK.value = {CallOutcome.CALLBACK.value}")
            print(f"[DEBUG] outcome.value == CallOutcome.CALLBACK.value? {outcome.value == CallOutcome.CALLBACK.value}")
            if callback_time_dt and outcome.value == CallOutcome.CALLBACK.value:
                schedule_callback(call_id, agent_id, from_phone, phone, callback_time_dt)
                print(f"callback was successfully scheduled at {callback_time_str}")
            else:
                print("nothing scheduled")
            try:
                if outcome != CallOutcome.MISSED:
                    memory_content = (
                        f"Call with {phone}.\n"
                        f"Outcome: {outcome.value}\n"
                        f"Summary: {summary}"
                    )

                    payload = {
                        "call_id": call_id,
                        "phone": phone,
                        #"outcome": outcome.value,
                        "callback_time": callback_time_str if callback_time_str else None,
                        "summary": memory_content,
                    }

                    add_memory(payload)
                    print("memory attempted to add")

            except Exception as api_err:
                _update_error(db, call_id, f"Memory API Error: {api_err}")
                return

            db_task = db.query(Task_Manager).filter_by(call_id=call_id).first()
            if db_task:
                db_task.outcome = outcome
                db_task.callback_time = callback_time_str
                db_task.processed = True
                db_task.last_error = None
                # db_task.analyzed_at = datetime.utcnow()
                db.commit()
                print("new task added")

    except Exception as e:
        print(f"Critical error in process_webhook_pipeline: {e}")


def schedule_callback(call_id: str, agent_id: str, from_phone: str, to_phone: str, callback_time: datetime):
    """Schedule a callback at the specified time"""
    scheduler = get_scheduler()
    try:
        local_tz = pytz.timezone('America/Detroit')
        
        # Ensure callback_time is timezone-aware
        if callback_time.tzinfo is None:
            callback_time = local_tz.localize(callback_time)
        else:
            callback_time = callback_time.astimezone(local_tz)
        
        # Get current time in same timezone
        now_local = datetime.now(local_tz)
        
        print(f"[SCHEDULER DEBUG] Callback time: {callback_time}")
        print(f"[SCHEDULER DEBUG] Current time: {now_local}")
        print(f"[SCHEDULER DEBUG] Time difference: {(callback_time - now_local).total_seconds()} seconds")
        
        # Check if in the future
        if callback_time <= now_local:
            print(f"[SCHEDULER WARNING] Callback time is in the past! Scheduling immediately.")
            callback_time = now_local + timedelta(seconds=5)
        
        # Schedule the job
        job = scheduler.add_job(
            func=start_call,
            trigger=DateTrigger(run_date=callback_time),
            args=[from_phone, to_phone, agent_id],
            id=f"callback_{call_id}",
            replace_existing=True,
            misfire_grace_time=300
        )
        
        print(f"[SCHEDULER] ✅ Callback scheduled for {to_phone}")
        print(f"[SCHEDULER] ✅ Time: {callback_time.strftime('%Y-%m-%d %I:%M:%S %p %Z')}")
        print(f"[SCHEDULER] ✅ Job ID: {job.id}")
        print(f"[SCHEDULER] ✅ Next run: {job.next_run_time}")
        
        # Verify the job was added
        all_jobs = scheduler.get_jobs()
        print(f"[SCHEDULER] Total jobs: {len(all_jobs)}")
        for j in all_jobs:
            print(f"[SCHEDULER] - Job {j.id}: {j.next_run_time}")
        
    except Exception as e:
        print(f"[SCHEDULER ERROR] Failed to schedule callback: {e}")
        import traceback
        traceback.print_exc()