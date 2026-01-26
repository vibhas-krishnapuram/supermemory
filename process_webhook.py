from datetime import datetime
from sqlalchemy.orm import Session
from db.models import Task_Manager
from db.database import SessionLocal

from supermemory_func import add_memory
from find_date import CallbackTimeExtractor


def process_webhook_pipeline(call_id: str, phone: str, summary: str):
    try:
        with SessionLocal() as db:

            extractor = CallbackTimeExtractor()
            res = extractor.extract_callback_time(summary)
            callback_time = res.get("iso_format", "")

            # memory add 
            try:
                memory_content = f"Call with {phone}. Summary: {summary}"

                payload = {
                    "summary": memory_content,
                    "call_id": call_id,
                    "phone": phone,
                    "callback_time": callback_time
                }
                add_memory(payload)
                
                # DB Update
                db_task = db.query(Task_Manager).filter_by(call_id=call_id).first()
                if db_task:
                    db_task.processed = True
                    db.commit()

            except Exception as api_err:
                db.rollback() 
                db_task = db.query(Task_Manager).filter_by(call_id=call_id).first()
                if db_task:
                    db_task.last_error = f"API Error: {str(api_err)}"
                    db.commit()
    except Exception as e:
        print(f"Critical error in process_webhook_pipeline: {e}")



