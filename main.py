import os
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, PlainTextResponse
from pydantic import BaseModel
from supabase import create_client, Client
from datetime import datetime, timedelta
import uvicorn
import csv
import io

app = FastAPI()

# --- SUPABASE CONFIG ---
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

class BreakReq(BaseModel):
    user_id: int
    agent_name: str
    duration: int

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
        supabase.table("deals").insert(deal.model_dump()).execute()
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/break")
async def start_break(req: BreakReq):
    try:
        # Upsert: Overwrites if the user is already on break
        data = req.model_dump()
        supabase.table("active_breaks").upsert(data).execute()
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/break/end")
async def end_break(user_id: dict):
    try:
        supabase.table("active_breaks").delete().eq("user_id", user_id["user_id"]).execute()
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/dashboard")
async def get_dashboard():
    try:
        # Get Deals
        deals_res = supabase.table("deals").select("*").execute()
        deals = deals_res.data
        
        # Get Active Breaks
        breaks_res = supabase.table("active_breaks").select("*").execute()
        active_breaks = breaks_res.data

        # Calculate timeframes
        now = datetime.now()
        today_deals = [d for d in deals if datetime.fromisoformat(d['created_at']).date() == now.date()]
        
        start_of_week = now - timedelta(days=now.weekday())
        weekly_deals = [d for d in deals if datetime.fromisoformat(d['created_at']).date() >= start_of_week.date()]
        
        monthly_deals = [d for d in deals if datetime.fromisoformat(d['created_at']).month == now.month]

        return {
            "daily": {"total": sum(d['amount'] for d in today_deals), "deals": today_deals},
            "weekly": {"total": sum(d['amount'] for d in weekly_deals), "deals": weekly_deals},
            "monthly": {"total": sum(d['amount'] for d in monthly_deals), "deals": monthly_deals},
            "active_breaks": active_breaks
        }
    except Exception as e:
        return {"error": str(e)}

@app.get("/api/admin/export")
async def export_deals(password: str):
    if password != "13012":
        raise HTTPException(status_code=403, detail="Unauthorized")
    
    deals = supabase.table("deals").select("*").execute().data
    
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Date", "Agent", "Amount", "Client ID", "Email", "Type", "Method"])
    for d in deals:
        writer.writerow([d['created_at'], d['agent_name'], d['amount'], d['client_id'], d['client_email'], d['deal_type'], d['payment_method']])
    
    return PlainTextResponse(output.getvalue(), media_type="text/csv")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run(app, host="0.0.0.0", port=port)
