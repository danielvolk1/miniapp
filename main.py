import os
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from supabase import create_client, Client
from datetime import datetime, timedelta
import uvicorn

app = FastAPI()

# --- CONFIG ---
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

class DealUpdate(BaseModel):
    amount: float
    client_id: str
    client_email: str

@app.get("/", response_class=HTMLResponse)
async def home():
    with open("index.html", "r", encoding="utf-8") as f:
        return f.read()

# --- ADMIN ACTIONS ---
@app.delete("/api/admin/deal/{deal_id}")
async def delete_deal(deal_id: int, password: str):
    if password != "13012": raise HTTPException(status_code=403)
    supabase.table("deals").delete().eq("id", deal_id).execute()
    return {"status": "deleted"}

@app.put("/api/admin/deal/{deal_id}")
async def update_deal(deal_id: int, update: DealUpdate, password: str):
    if password != "13012": raise HTTPException(status_code=403)
    supabase.table("deals").update(update.model_dump()).eq("id", deal_id).execute()
    return {"status": "updated"}

@app.post("/api/admin/config")
async def update_config(data: dict):
    if data.get("password") != "13012": raise HTTPException(status_code=403)
    supabase.table("settings").upsert({"key": "shift_config", "value": data["config"]}).execute()
    return {"status": "success"}

# --- SHOUTBOX ---
@app.post("/api/shout")
async def add_shout(data: dict):
    supabase.table("shoutbox").insert(data).execute()
    return {"status": "sent"}

@app.get("/api/dashboard")
async def get_dashboard():
    deals = supabase.table("deals").select("*").order('created_at').execute().data
    breaks = supabase.table("active_breaks").select("*").execute().data
    shouts = supabase.table("shoutbox").select("*").order('created_at', desc=True).limit(5).execute().data
    config = supabase.table("settings").select("value").eq("key", "shift_config").execute().data[0]['value']
    
    return {
        "deals": deals,
        "active_breaks": breaks,
        "shouts": shouts,
        "config": config
    }

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run(app, host="0.0.0.0", port=port)
