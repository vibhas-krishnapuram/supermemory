from fastapi import APIRouter, Request, FastAPI, BackgroundTasks, Depends
from fastapi.responses import JSONResponse
from supermemory import Supermemory
from retell import Retell

import json
from datetime import datetime
import os
from dotenv import load_dotenv

from sqlalchemy.orm import Session
from db.models import Task_Manager
from db.database import get_db

from find_date import CallbackTimeExtractor
from process_webhook import process_webhook_pipeline

load_dotenv()

app = FastAPI()

router = APIRouter()
client = Supermemory(api_key=os.getenv("SUPERMEMORY_API_KEY"))
retell = Retell(api_key = os.getenv("RETELL_API_KEY"))


@app.post("/api/webhooks/retell")
async def retell_call_ended(request: Request, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    try:
        post_data = await request.json()
        if post_data.get("event") != "call_analyzed":
            return {"status": "ignored"}

        data = post_data["call"]
        call_id = data.get("call_id")
        
        
        existing_task = db.query(Task_Manager).filter_by(call_id=call_id).first()
        if existing_task:
            return JSONResponse(status_code=200, content={"message": "Already exists"})

        new_task = Task_Manager(
            call_id=call_id,
            phone=data.get("from_number"),
            summary=data.get("call_analysis", {}).get("call_summary"),
            processed=False      
        )
        db.add(new_task)
        db.commit()

        background_tasks.add_task(
            process_webhook_pipeline, 
            call_id, 
            new_task.phone, 
            new_task.summary
        )

        return {"status": "accepted", "call_id": call_id}

    except Exception as err:
        print(f"Error in webhook: {err}")
        return JSONResponse(
            status_code=500, content={"message": "Internal Server Error"}
        )