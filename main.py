import os
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from supabase import create_client, Client
import uvicorn

app = FastAPI()

# --- CONNECTION ---
# Replace these or use Render Environment Variables
SUPABASE_URL = os.environ.get("SUPABASE_URL", "https://wcuccijzzxwnnytkxhvz.supabase.co")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "sb_publishable_LztBUE9jjqGQcduPJPvSUg_lBgZVxef")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

class Deal(BaseModel):
    agent_name: str
    amount: float
    client_id: str
    client_email: str
    deal_type: str 
    payment_method: str

class AdminUpdate(BaseModel):
    agent_name: str
    amount: float
    client_id: str

@app.get("/", response_class=HTMLResponse)
async def home():
    with open("index.html", "r", encoding="utf-8") as f:
        return f.read()

@app.get("/api/dashboard")
async def get_dashboard():
    try:
        deals = supabase.table("deals").select("*").order('created_at', desc=True).execute().data
        breaks = supabase.table("active_breaks").select("*").execute().data
        config = supabase.table("settings").select("value").eq("key", "shift_config").execute().data[0]['value']
        return {"deals": deals, "active_breaks": breaks, "config": config}
    except Exception as e:
        return {"error": str(e)}

@app.post("/api/deal")
async def add_deal(deal: Deal):
    supabase.table("deals").insert(deal.model_dump()).execute()
    return {"status": "success"}

@app.post("/api/break")
async def start_break(data: dict):
    supabase.table("active_breaks").upsert(data).execute()
    return {"status": "success"}

@app.post("/api/break/end")
async def end_break(data: dict):
    supabase.table("active_breaks").delete().eq("user_id", data["user_id"]).execute()
    return {"status": "success"}

# --- ADMIN ACTIONS ---
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
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run(app, host="0.0.0.0", port=port)
