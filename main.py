import os
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse # <--- This is the key fix
from pydantic import BaseModel
from supabase import create_client, Client
import uvicorn

app = FastAPI()

# --- SUPABASE CONFIG ---
# Replace with your actual project URL and Anon Key from Supabase settings
SUPABASE_URL = "https://wcuccijzzxwnnytkxhvz.supabase.co" 
SUPABASE_KEY = "sb_publishable_LztBUE9jjqGQcduPJPvSUg_lBgZVxef"
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

class Deal(BaseModel):
    agent_name: str
    amount: float
    client_id: str
    client_email: str
    deal_type: str 
    payment_method: str

# FIX: We use response_class=HTMLResponse to stop the "Pretty-print" text issue
@app.get("/", response_class=HTMLResponse)
async def home():
    try:
        with open("index.html", "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        return f"Error loading index.html: {str(e)}"

@app.post("/api/deal")
async def add_deal(deal: Deal):
    try:
        supabase.table("deals").insert(deal.dict()).execute()
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/stats")
async def get_stats():
    try:
        res = supabase.table("deals").select("*").execute()
        deals = res.data
        total = sum(d['amount'] for d in deals)
        return {"total": total, "deals": deals}
    except:
        return {"total": 0, "deals": []}

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run(app, host="0.0.0.0", port=port)
