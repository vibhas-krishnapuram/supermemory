from openai import OpenAI
from dotenv import load_dotenv
from datetime import datetime, timezone
from enum import Enum
from pydantic import BaseModel, Field
from typing import Optional
import pytz

load_dotenv()

client = OpenAI()

class CallOutcome(str, Enum):
    SUCCESSFUL = "SUCCESSFUL"
    CALLBACK = "CALLBACK"
    NOT_INTERESTED = "NOT_INTERESTED"
    MISSED = "MISSED"

class CallAnalysis(BaseModel):
    outcome: CallOutcome

    callback_time_iso: Optional[datetime] = Field(
        default=None, 
        description="The ISO 8601 timestamp for the callback in EST timezone"
    )

class CallSummaryScan:
    def __init__(self, client, model: str = "gpt-4o-mini"):
        self.client = client
        self.model = model
        self.local_tz = pytz.timezone('America/Detroit')  

    def analyze(self, summary: str):

        current_time_local = datetime.now(self.local_tz)
        current_time_context = current_time_local.strftime("%A, %B %d, %Y at %I:%M %p %Z")
        
        response = self.client.beta.chat.completions.parse(
            model=self.model,
            messages=[
                {
                    "role": "system",
                    "content": (
                        f"The current time is {current_time_context}.\n"
                        "You are a call outcome classifier. Classify the call into exactly one outcome.\n"
                        "If the user mentions a relative time (e.g., 'in 5 minutes', 'tomorrow at 2pm'), "
                        "calculate the absolute ISO timestamp based on the current time provided above.\n"
                        "IMPORTANT: Return times in America/Detroit timezone (EST/EDT), not UTC."
                    )
                },
                {"role": "user", "content": f"Call summary: {summary}"}
            ],
            response_format=CallAnalysis, 
        )

        parsed = response.choices[0].message.parsed
        

        if parsed.callback_time_iso:

            if parsed.callback_time_iso.tzinfo == timezone.utc:
                parsed.callback_time_iso = parsed.callback_time_iso.astimezone(self.local_tz)

            elif parsed.callback_time_iso.tzinfo is None:
                parsed.callback_time_iso = self.local_tz.localize(parsed.callback_time_iso)
        
        return parsed