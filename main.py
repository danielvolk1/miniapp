import os
from datetime import datetime, timezone, timedelta
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from supabase import create_client, Client
import uvicorn

app = FastAPI()

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

class DealModel(BaseModel):
    agent_name: str
    amount: float
    client_id: str
    client_email: str
    deal_type: str
    payment_method: str
    notes: str = ""

@app.get("/", response_class=HTMLResponse)
async def home():
    with open("index.html", "r", encoding="utf-8") as f:
        return f.read()

@app.get("/api/dashboard")
async def get_dashboard():
    # Fetch data for the last 30 days for comprehensive analytics
    thirty_days_ago = (datetime.now(timezone.utc) - timedelta(days=30)).isoformat()
    
    deals = supabase.table("deals").select("*").gte("created_at", thirty_days_ago).order('created_at', desc=True).execute().data
    breaks = supabase.table("active_breaks").select("*").execute().data
    break_logs = supabase.table("break_logs").select("*").gte("created_at", thirty_days_ago).execute().data
    
    # Get configuration and latest announcement
    targets_data = supabase.table("settings").select("value").eq("key", "system_targets").execute().data
    targets = targets_data[0]['value'] if targets_data else {"daily": 10000, "weekly": 50000, "monthly": 200000}
    
    announcement = supabase.table("announcements").select("*").order('created_at', desc=True).limit(1).execute().data
    
    return {
        "deals": deals, 
        "active_breaks": breaks, 
        "break_logs": break_logs, 
        "targets": targets,
        "announcement": announcement[0] if announcement else None
    }

@app.post("/api/deal")
async def add_deal(deal: DealModel):
    supabase.table("deals").insert(deal.model_dump()).execute()
    return {"status": "success"}

@app.put("/api/admin/deal/{id}")
async def update_deal(id: int, update: DealModel, password: str):
    if password != "13012": raise HTTPException(status_code=403)
    supabase.table("deals").update(update.model_dump()).eq("id", id).execute()
    return {"status": "ok"}

@app.delete("/api/admin/deal/{id}")
async def delete_deal(id: int, password: str):
    if password != "13012": raise HTTPException(status_code=403)
    supabase.table("deals").delete().eq("id", id).execute()
    return {"status": "ok"}

@app.post("/api/break")
async def start_break(data: dict):
    data["start_time"] = datetime.now(timezone.utc).isoformat()
    supabase.table("active_breaks").upsert(data).execute()
    return {"status": "success"}

@app.post("/api/break/end")
async def end_break(data: dict):
    active = supabase.table("active_breaks").select("*").eq("user_id", data["user_id"]).execute().data
    if active:
        b = active[0]
        start_time = datetime.fromisoformat(b["start_time"].replace("Z", "+00:00"))
        duration_minutes = int((datetime.now(timezone.utc) - start_time).total_seconds() / 60)
        supabase.table("break_logs").insert({
            "user_id": str(b["user_id"]), "agent_name": b["agent_name"], 
            "duration": duration_minutes, "break_type": b.get("break_type", "small")
        }).execute()
    supabase.table("active_breaks").delete().eq("user_id", data["user_id"]).execute()
    return {"status": "success"}

# --- ADMIN ENDPOINTS ---

@app.post("/api/admin/targets")
async def set_targets(data: dict):
    if data.get("password") != "13012": raise HTTPException(status_code=403)
    supabase.table("settings").upsert({"key": "system_targets", "value": data["targets"]}).execute()
    return {"status": "ok"}

@app.post("/api/admin/broadcast")
async def send_broadcast(data: dict):
    if data.get("password") != "13012": raise HTTPException(status_code=403)
    supabase.table("announcements").insert({"message": data["message"]}).execute()
    return {"status": "ok"}

@app.post("/api/admin/danger/{action}")
async def danger_zone(action: str, data: dict):
    if data.get("password") != "13012": raise HTTPException(status_code=403)
    if action == "clear_breaks":
        supabase.table("active_breaks").delete().neq("user_id", 0).execute()
    elif action == "wipe_today_logs":
        today = datetime.now(timezone.utc).strftime('%Y-%m-%d')
        supabase.table("break_logs").delete().gte("created_at", today).execute()
    return {"status": "ok"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
