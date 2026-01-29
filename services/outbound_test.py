from retell import Retell
import os
from dotenv import load_dotenv

from Memory_Functions import *

load_dotenv()

key = os.getenv("RETELL_API_KEY_DAVID")

client = Retell(api_key=key)



def start_call(from_number, to_number, agent_id):
    try:
        raw = get_caller_context(to_number)
        context = format_caller_context(raw)

        phone_call_response = client.call.create_phone_call(
            from_number=from_number,
            to_number=to_number, 
            override_agent_id=agent_id,
            retell_llm_dynamic_variables={
                "callback_history": context,
            }
        )
        
        print(f"Call initiated! ID: {phone_call_response.call_id}")
        
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    # YOU MUST PASS THE VALUES HERE:
    start_call(
        from_number="+16182664493", 
        to_number="+17342941312",   
        agent_id="agent_aa186c0dd94cbb6d87b0f28ed6"
    )

