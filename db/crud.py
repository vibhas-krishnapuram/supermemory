from sqlalchemy.orm import Session

from db.models import Task_Manager
from db.database import SessionLocal

def _update_error(db: Session, call_id: str, error: str):
    db_task = db.query(Task_Manager).filter_by(call_id=call_id).first()
    if db_task:
        db_task.last_error = error
        db.commit()