from pydantic import BaseModel, Field
from datetime import datetime, timezone
from typing import Optional
from enum import Enum
from openai import OpenAI

from dotenv import load_dotenv

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
        description="The ISO 8601 timestamp for the callback"
    )

class CallSummaryScan:
    def __init__(self, client, model: str = "gpt-4o-mini"):
        self.client = client
        self.model = model

    def analyze(self, summary: str):

        current_time_context = datetime.now(timezone.utc).strftime("%A, %B %d, %Y")
        
        response = self.client.beta.chat.completions.parse(
            model=self.model,
            messages=[
                {
                    "role": "system",
                    "content": (
                        f"Today is {current_time_context}.\n"
                        "You are a call outcome classifier. Classify the call into exactly one outcome.\n"
                        "If the user mentions a relative time (e.g., 'tomorrow at 2pm'), "
                        "calculate the absolute ISO timestamp based on today's date."
                    )
                },
                {"role": "user", "content": f"Call summary: {summary}"}
            ],
            response_format=CallAnalysis, 
        )

        return response.choices[0].message.parsed


# call_scan = CallSummaryScan(client=client)

# ex_summary = "Agent explains policy rate reduction, verifies personal details, and collects info for a 7:00 PM appointment with John to complete the rate reduction. Initial calendar check had an API error, but after providing a full phone number, the appointment was booked for 7:00 PM today with John. The call ends with confirmation and goodbyes."
# result = call_scan.analyze(ex_summary)

# print(result)
