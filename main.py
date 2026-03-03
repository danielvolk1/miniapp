import os
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from supabase import create_client, Client
from datetime import datetime
import uvicorn

app = FastAPI()

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

class AdminUpdate(BaseModel):
    agent_name: str
    amount: float
    client_id: str
    client_email: str
    deal_type: str
    payment_method: str

@app.get("/", response_class=HTMLResponse)
async def home():
    with open("index.html", "r", encoding="utf-8") as f:
        return f.read()

@app.get("/api/dashboard")
async def get_dashboard():
    try:
        deals = supabase.table("deals").select("*").order('created_at', desc=True).execute().data
        breaks = supabase.table("active_breaks").select("*").execute().data
        history = supabase.table("break_history").select("*").order('started_at', desc=True).limit(20).execute().data
        config = supabase.table("settings").select("value").eq("key", "shift_config").execute().data[0]['value']
        return {"deals": deals, "active_breaks": breaks, "history": history, "config": config}
    except Exception as e:
        return {"error": str(e)}

@app.post("/api/deal")
async def add_deal(deal: dict):
    supabase.table("deals").insert(deal).execute()
    return {"status": "success"}

@app.post("/api/break")
async def start_break(data: dict):
    supabase.table("active_breaks").upsert(data).execute()
    return {"status": "success"}

@app.post("/api/break/end")
async def end_break(data: dict):
    # Log to history before deleting
    b = supabase.table("active_breaks").select("*").eq("user_id", data["user_id"]).execute().data
    if b:
        supabase.table("break_history").insert({
            "agent_name": b[0]['agent_name'],
            "duration": b[0]['duration'],
            "started_at": b[0]['start_time']
        }).execute()
    supabase.table("active_breaks").delete().eq("user_id", data["user_id"]).execute()
    return {"status": "success"}

# --- ADMIN POWER ---
@app.post("/api/admin/reset-breaks")
async def reset_breaks(data: dict):
    if data.get("password") != "13012": raise HTTPException(status_code=403)
    supabase.table("active_breaks").delete().neq("user_id", 0).execute() # Clear all active
    # If using banks, you'd reset the bank table here
    return {"status": "reset_done"}

@app.delete("/api/admin/deal/{id}")
async def delete_deal(id: int, password: str):
    if password != "13012": raise HTTPException(status_code=403)
    supabase.table("deals").delete().eq("id", id).execute()
    return {"status": "ok"}

@app.put("/api/admin/deal/{id}")
async def update_deal(id: int, update: AdminUpdate, password: str):
    if password != "13012": raise HTTPException(status_code=403)
    supabase.table("deals").update(update.model_dump()).eq("id", id).execute()
    return {"status": "ok"}

@app.post("/api/admin/config")
async def set_config(data: dict):
    if data.get("password") != "13012": raise HTTPException(status_code=403)
    supabase.table("settings").upsert({"key": "shift_config", "value": data["config"]}).execute()
    return {"status": "ok"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
