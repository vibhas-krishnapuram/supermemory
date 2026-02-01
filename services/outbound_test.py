from retell import Retell
from services.Memory_Functions import get_caller_context, format_caller_context
from datetime import datetime
import os

import pytz
from dotenv import load_dotenv
load_dotenv()

key = os.getenv("RETELL_API_KEY_DAVID")
client = Retell(api_key=key)


def start_call(from_number, to_number, agent_id, is_callback=False):  # ✅ Add default parameter
    """
    Trigger a call via Retell and pass previous conversation context.
    """
    try:
        raw_context = get_caller_context(to_number)
        formatted_context = format_caller_context(raw_context, is_callback)  # ✅ Pass is_callback

        print(f"[START_CALL] Triggered for {to_number} at {datetime.now()}")
        print(f"[START_CALL] Is callback: {is_callback}")  # ✅ Add debug log
        print(f"[START_CALL] Context entries: {len(raw_context.results) if raw_context and raw_context.results else 0}")
        print(f"[START_CALL] Formatted context:\n{formatted_context}")

        # ✅ IMPROVED dynamic variables
        dynamic_vars = {
            "previous_conversation": formatted_context,  # Changed from callback_history
            "is_callback": "yes" if is_callback else "no",  # Changed from true/false string
            "customer_phone": to_number,
            "call_timestamp": datetime.now(pytz.timezone('America/Detroit')).strftime("%B %d, %Y at %I:%M %p")
        }

        phone_call_response = client.call.create_phone_call(
            from_number=from_number,
            to_number=to_number,
            override_agent_id=agent_id,
            retell_llm_dynamic_variables=dynamic_vars
        )

        print(f"[START_CALL] Call initiated, Retell call ID: {phone_call_response.call_id}")
        return phone_call_response.call_id

    except Exception as e:
        print(f"[START_CALL ERROR] Failed to initiate call: {e}")
        import traceback
        traceback.print_exc()
        return None