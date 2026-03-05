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
    deal_type: str
    asset_class: str
    payment_method: str
    tag: str = "Standard"
    notes: str = ""

@app.get("/", response_class=HTMLResponse)
async def home():
    with open("index.html", "r", encoding="utf-8") as f: return f.read()

@app.get("/api/dashboard")
async def get_dashboard():
    window = (datetime.now(timezone.utc) - timedelta(days=30)).isoformat()
    
    # Default settings including new DEFCON and Allocations
    default_config = {
        "daily": 25000, "defcon": "green",
        "allocations": {"SpaceX Pre-IPO": 500000, "AI Data Centers": 150000},
        "force_refresh": 0
    }
    
    config_data = supabase.table("settings").select("value").eq("key", "system_config").execute().data
    config = config_data[0]['value'] if config_data else default_config

    return {
        "deals": supabase.table("deals").select("*").gte("created_at", window).order('created_at', desc=True).execute().data,
        "active_breaks": supabase.table("active_breaks").select("*").execute().data,
        "chat": supabase.table("floor_chat").select("*").order('created_at', desc=True).limit(30).execute().data,
        "config": config,
        "announcement": next(iter(supabase.table("announcements").select("*").order('created_at', desc=True).limit(1).execute().data), None)
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
    supabase.table("active_breaks").delete().eq("user_id", data["user_id"]).execute()
    return {"status": "success"}

@app.post("/api/admin/config")
async def update_config(data: dict):
    if data.get("password") != "13012": raise HTTPException(status_code=403)
    supabase.table("settings").upsert({"key": "system_config", "value": data["config"]}).execute()
    return {"status": "ok"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
