from supermemory import Supermemory
import os 
from dotenv import load_dotenv
import time

load_dotenv()

client = Supermemory(
    api_key = os.getenv("SUPERMEMORY_API_KEY")
)

# client.add(
#     content="The call with Michelle: she said she was interested in switching insurance and saving money, but was busy and wanted to talk later.",
#     container_tag="user_125",
#     metadata={"category": "ai"}
# )

# # Add a URL (auto-extracted)
# client.add(
#     content="https://youtube.com/watch?v=dQw4w9WgXcQ",
#     container_tag="user_123"
# )

results = client.search.memories(
    q="context about user",
    container_tag="user_125",
    search_mode="hybrid",
    limit=5
)

def add_memory(payload):
    client = Supermemory(
    api_key = os.getenv("SUPERMEMORY_API_KEY"))

    summary = payload["summary"]
    call_id = payload["call_id"]
    phone_num = payload["phone"]
    callback_time = payload["callback_time"]

    client.add(
    content=summary,
    container_tag=call_id, # use phone number instead after testing
    metadata=payload
)


# for result in results.results:
#     print(result.memory or result.chunk, result.similarity)