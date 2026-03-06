import os
from datetime import datetime, timezone, timedelta
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from supabase import create_client, Client
import uvicorn

app = FastAPI()
supabase: Client = create_client(os.environ.get("SUPABASE_URL"), os.environ.get("SUPABASE_KEY"))

class DealModel(BaseModel):
    agent_name: str
    amount: float
    client_id: str
    client_email: str
    deal_type: str
    payment_method: str

@app.get("/", response_class=HTMLResponse)
async def home():
    with open("index.html", "r", encoding="utf-8") as f: return f.read()

@app.get("/api/dashboard")
async def get_dashboard():
    # Only pull the last 24 hours to ensure the app never lags
    window = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()
    try:
        deals = supabase.table("deals").select("*").gte("created_at", window).order('created_at', desc=True).execute().data
        breaks = supabase.table("active_breaks").select("*").execute().data
        logs = supabase.table("break_logs").select("*").gte("created_at", window).execute().data
        settings_req = supabase.table("settings").select("value").eq("key", "system").execute().data
        settings = settings_req[0]['value'] if settings_req else {"target": 50000, "broadcast": ""}
        
        return {"status": "ok", "deals": deals, "active_breaks": breaks, "break_logs": logs, "settings": settings}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.post("/api/deal")
async def add_deal(deal: DealModel):
    supabase.table("deals").insert(deal.model_dump()).execute()
    return {"status": "ok"}

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
    return {"status": "ok"}

@app.post("/api/break/end")
async def end_break(data: dict):
    active = supabase.table("active_breaks").select("*").eq("user_id", data["user_id"]).execute().data
    if active:
        b = active[0]
        start_time = datetime.fromisoformat(b["start_time"].replace("Z", "+00:00"))
        duration = int((datetime.now(timezone.utc) - start_time).total_seconds() / 60)
        supabase.table("break_logs").insert({
            "user_id": b["user_id"], "agent_name": b["agent_name"], 
            "break_type": b["break_type"], "duration_mins": max(1, duration)
        }).execute()
        supabase.table("active_breaks").delete().eq("user_id", data["user_id"]).execute()
    return {"status": "ok"}

@app.post("/api/admin/settings")
async def update_settings(data: dict):
    if data.get("password") != "13012": raise HTTPException(status_code=403)
    supabase.table("settings").upsert({"key": "system", "value": data["settings"]}).execute()
    return {"status": "ok"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
