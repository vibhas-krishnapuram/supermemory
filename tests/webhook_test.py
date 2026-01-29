from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import json

app = FastAPI()

@app.post("/retell/webhook")
async def retell_webhook(request: Request):
    payload = await request.json()

    # Pretty-print payload for debugging
    print("==== Retell Webhook Received ====")
    print(json.dumps(payload, indent=2))
    print("================================")

    # OPTIONAL: basic event routing
    event = payload.get("event")

    if event == "call_started":
        print("📞 Call started:", payload.get("call_id"))

    elif event == "call_ended":
        print("☎️ Call ended:", payload.get("call_id"))

    elif event == "call_analyzed":
        print("📊 Call analyzed")

    # Retell expects a 200 OK
    return JSONResponse(content={"status": "ok"}, status_code=200)
