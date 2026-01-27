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
        container_tag=call_id, # use phone number instead after testing, nvm use agent_id
        metadata=payload
    )

def get_caller_context(phone):
    results = client.search.memories(
    q= f"give information about user from last call to help the next phone call be personable and smooth: {phone}",
    search_mode="hybrid",
    limit=5
)


# phone_num = "+17342941312"
# ans = get_caller_context(phone_num)
# #print(ans)

# for result in ans.results:
#     print(result.memory or result.chunk, result.similarity)