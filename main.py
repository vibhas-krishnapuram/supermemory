from fastapi import APIRouter, Request, FastAPI, BackgroundTasks, Depends
from fastapi.responses import JSONResponse

import json
from datetime import datetime
import os
from dotenv import load_dotenv

from sqlalchemy.orm import Session
from db.models import Task_Manager
from db.database import get_db, engine, Base

from services.Background_Task import process_webhook_pipeline
from services.scheduler import get_scheduler

from retell import Retell

load_dotenv()

Base.metadata.create_all(bind=engine)

app = FastAPI()

router = APIRouter()

retell = Retell(api_key=os.environ["RETELL_API_KEY"])

@app.on_event("startup")
def start_scheduler():
    get_scheduler()

@app.post("/api/webhooks/retell")
async def retell_call_ended(request: Request, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    try:
        post_data = await request.json()
        if post_data.get("event") != "call_analyzed":
            return {"status": "ignored"}

        data = post_data["call"]
        call_id = data.get("call_id")
        
        from_phone = data.get("from_number")
        to_phone = data.get("to_number")
        agent_id = data.get("agent_id")
        summary = data.get("call_analysis", {}).get("call_summary")
        
        existing_task = db.query(Task_Manager).filter_by(call_id=call_id).first()
        if existing_task:
            return JSONResponse(status_code=200, content={"message": "Already exists"})


        background_tasks.add_task(
            process_webhook_pipeline, 
            call_id,
            agent_id,
            from_phone,
            to_phone,
            summary
        )

        new_task = Task_Manager(
            call_id=call_id,
            agent_id=agent_id,
            phone=to_phone,
            summary=summary,
            processed=False      
        )
        db.add(new_task)
        db.commit()

        return {"status": "accepted", "call_id": call_id}

    except Exception as err:
        print(f"Error in webhook: {err}")
        return JSONResponse(
            status_code=500, content={"message": "Internal Server Error"}
        )

@app.get("/test")
async def test():
    return {"status": "working"}

@app.get("/api/scheduled-callbacks")
async def get_scheduled_callbacks():
    from services.scheduler import get_scheduler

    scheduler = get_scheduler()

    jobs = []
    for job in scheduler.get_jobs():
        jobs.append({
            "job_id": job.id,
            "next_run": job.next_run_time.isoformat() if job.next_run_time else None,
            "function": job.func.__name__,
            "args": str(job.args) if job.args else None
        })

    return {
        "scheduled_jobs": jobs,
        "total_jobs": len(jobs),
        "scheduler_running": scheduler.running
    }


@app.post("/test-schedule-callback")
async def test_schedule_callback():
    from services.Background_Task import schedule_callback
    from datetime import datetime, timedelta
    import pytz
    
    local_tz = pytz.timezone('America/Detroit')
    

    callback_time = datetime.now(local_tz) + timedelta(seconds=15)
    
  
    schedule_callback(
        call_id="test_call_123456",
        agent_id="agent_aa186c0dd94cbb6d87b0f28ed6",
        from_phone="+16182664493",
        to_phone="+17342941312",
        callback_time=callback_time
    )
    
    return {
        "message": "schedule_callback function called",
        "callback_time": callback_time.isoformat(),
        "wait_seconds": 15
    }