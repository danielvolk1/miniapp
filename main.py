import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from supabase import create_client, Client
from datetime import datetime, timedelta

app = FastAPI()

# --- SETUP SUPABASE ---
# Add your actual keys here or as Render Environment Variables
SUPABASE_URL = "https://wcuccijzzxwnnytkxhvz.supabase.co" 
SUPABASE_KEY = "sb_publishable_LztBUE9jjqGQcduPJPvSUg_lBgZVxef"
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

class Deal(BaseModel):
    agent_name: str
    amount: float
    client_id: str
    client_email: str
    deal_type: str # FTD or Deposit
    payment_method: str

@app.get("/")
async def home():
    with open("index.html", "r") as f:
        return f.read()

@app.post("/api/deal")
async def add_deal(deal: Deal):
    try:
        supabase.table("deals").insert(deal.dict()).execute()
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/stats")
async def get_stats():
    # Fetch all deals from Supabase
    res = supabase.table("deals").select("*").execute()
    deals = res.data
    
    # Simple logic to group by period (Example: Today)
    today = datetime.now().date()
    daily_total = sum(d['amount'] for d in deals if datetime.fromisoformat(d['created_at']).date() == today)
    
    return {
        "daily": daily_total,
        "total": sum(d['amount'] for d in deals),
        "all_deals": deals[-10:] # Last 10 deals for the feed
    }

