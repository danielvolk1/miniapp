import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from supabase import create_client, Client
from datetime import datetime
import uvicorn

app = FastAPI()

# --- REPLACE THESE WITH YOUR ACTUAL SUPABASE KEYS ---
SUPABASE_URL = "https://wcuccijzzxwnnytkxhvz.supabase.co" 
SUPABASE_KEY = "sb_publishable_LztBUE9jjqGQcduPJPvSUg_lBgZVxef"
# ----------------------------------------------------

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

class Deal(BaseModel):
    agent_name: str
    amount: float
    client_id: str
    client_email: str
    deal_type: str 
    payment_method: str

@app.get("/")
async def home():
    with open("index.html", "r") as f:
        return f.read()

@app.post("/api/deal")
async def add_deal(deal: Deal):
    try:
        # Saves to the 'deals' table we created earlier
        supabase.table("deals").insert(deal.dict()).execute()
        return {"status": "success"}
    except Exception as e:
        print(f"Error: {e}")
        raise HTTPException(status_code=500, detail="Database Error")

@app.get("/api/stats")
async def get_stats():
    try:
        res = supabase.table("deals").select("*").execute()
        deals = res.data
        total = sum(d['amount'] for d in deals)
        return {"total": total, "count": len(deals)}
    except:
        return {"total": 0, "count": 0}

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
