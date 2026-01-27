from datetime import datetime
from sqlalchemy.orm import Session
from db.models import CallOutcome, Task_Manager
from db.database import SessionLocal
from db.crud import _update_error

from supermemory_func import add_memory
from scan_payload import CallSummaryScan

from openai import OpenAI

from dotenv import load_dotenv

load_dotenv()

client = OpenAI()
analyzer = CallSummaryScan(client)


def process_webhook_pipeline(call_id: str, phone: str, summary: str):

    try:
        with SessionLocal() as db:

            try:
                analysis = analyzer.analyze(summary)
                outcome: CallOutcome = analysis.outcome
                callback_time = analysis.callback_time_iso
                callback_time = callback_time.strftime("%Y-%m-%d %H:%M") if callback_time else "No callback"
                print("Summary analysis done")
            except Exception as analysis_err:
                _update_error(db, call_id, f"Analysis Error: {analysis_err}")
                return

            # ADD SCHEDULE HELPER HERE 
            # if outcome == CallOutcome.CALLBACK and callback_time:
            #     schedule_callback(call_id, phone, callback_time)


            try:
                memory_content = (
                    f"Call with {phone}.\n"
                    f"Outcome: {outcome.value}\n"
                    f"Summary: {summary}"
                )

                payload = {
                    "call_id": call_id,
                    "phone": phone,
                    #"outcome": outcome.value,
                    "callback_time": callback_time if callback_time else None,
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
                db_task.callback_time = callback_time
                db_task.processed = True
                db_task.last_error = None
                db_task.analyzed_at = datetime.utcnow()
                db.commit()
                print("new task added")

    except Exception as e:
        print(f"Critical error in process_webhook_pipeline: {e}")


def schedule_callback(call_id: str, phone: str, callback_time: datetime):
    print(
        f"[SCHEDULER] Callback scheduled "
        f"for {phone} at {callback_time.isoformat()}"
    )