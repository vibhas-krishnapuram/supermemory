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
    callback_time = payload.get("callback_time") 

    metadata = {
        "entity_id": payload.get("entity_id"),
        "call_id": call_id,
        "phone": phone_num,
        "summary": summary,
    }

    if callback_time:
        metadata["callback_time"] = callback_time

    client.add(
        content=summary,
        container_tag=call_id,
        metadata=metadata
    )

def get_caller_context(phone):
    results = client.search.memories(
    q= f"give relevant information about user with the phone number: {phone} from last call to help the next phone call be personable and smooth.",
    search_mode="hybrid",
    limit=5
)
    return results


def format_caller_context(response, is_callback=False):
    """
    Format caller context for use in Retell agent prompts.
    
    Args:
        response: Raw response from Supermemory
        is_callback: Whether this is a callback (affects formatting)
        
    Returns:
        Formatted string with conversation history
    """
    if not response or not response.results:
        if is_callback:
            return "No previous call history found, but this was scheduled as a callback."
        return "No previous call history found."

    formatted_context = []
    
    # Only add callback header if is_callback is True
    if is_callback:
        formatted_context.append("THIS IS A SCHEDULED CALLBACK - Reference the information below:")
        formatted_context.append("")
    
    for i, res in enumerate(response.results[:3], 1):

        summary = None
        
        #  check metadata for structured summary
        if res.metadata and 'summary' in res.metadata:
            summary = res.metadata['summary']
        # Fallback to memory or chunk
        elif res.memory:
            summary = res.memory
        else:
            summary = res.chunk
            
        if summary:
            formatted_context.append(f"Previous Call #{i}:")
            formatted_context.append(f"{summary}")
            
            # Add callback time if available
            if res.metadata and 'callback_time' in res.metadata and res.metadata['callback_time']:
                formatted_context.append(f"Scheduled callback: {res.metadata['callback_time']}")
                
            formatted_context.append("")  # Blank line between entries

    # Only add callback reminder if is_callback is True
    if is_callback:
        formatted_context.append("---")
        formatted_context.append("IMPORTANT: Acknowledge that you're calling back as previously scheduled. Reference specific details from the conversation above.")

    return "\n".join(formatted_context)