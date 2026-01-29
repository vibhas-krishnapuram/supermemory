from supermemory import Supermemory
import os 
from dotenv import load_dotenv
import time

load_dotenv()

client = Supermemory(
    api_key = os.getenv("SUPERMEMORY_API_KEY")
)

def add_memory(payload):
    summary = payload["summary"]
    call_id = payload["call_id"]
    phone_num = payload["phone"]
    callback_time = payload["callback_time"]

    client.add(
        content=summary,
        container_tag=call_id,
        metadata=payload
    )




def get_caller_context(phone):
    results = client.search.memories(
    q= f"give relevant information about user with the phone number: {phone} from last call to help the next phone call be personable and smooth.",
    search_mode="hybrid",
    limit=5
)
    return results


def format_caller_context(response):
    if not response.results:
        return "No previous call history found."

    formatted_context = []
    for i, res in enumerate(response.results[:3]):

        summary = res.memory or res.chunk
        
 
        if res.metadata and 'summary' in res.metadata:
            summary = res.metadata['summary']
            
        if summary:
            formatted_context.append(f"- {summary}")

    return "\n".join(formatted_context)

# Usage:
# raw_response = get_caller_context("+17342941312")
# clean_history = format_caller_context(raw_response)

# print(clean_history)






