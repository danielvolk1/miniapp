from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from datetime import datetime, timedelta
import uvicorn

app = FastAPI()

# Temporary Mock Database (Replace with Supabase for production)
db = {
    "transactions": [], # Each: {id, agent, amount, date, client_id...}
    "targets": {"global": 10000, "agents": {}}
}

@app.get("/api/dashboard/{period}")
async def get_dashboard(period: str):
    # period can be 'daily', 'weekly', 'monthly'
    now = datetime.now()
    # Filter logic here...
    return {"stats": "data", "total": 5000}

@app.post("/api/admin/update_target")
async def update_target(data: dict):
    if data.get("password") != "13012":
        raise HTTPException(status_code=403, detail="Invalid Admin Password")
    db["targets"]["global"] = data["new_target"]
    return {"status": "success"}

@app.delete("/api/admin/transaction/{tx_id}")
async def delete_tx(tx_id: int, password: str):
    if password != "13012": raise HTTPException(status_code=403)
    # Logic to remove transaction...
    return {"status": "deleted"}
import os
from supabase import create_client, Client

url = "YOUR_SUPABASE_URL"
key = "YOUR_SUPABASE_KEY"
supabase: Client = create_client(url, key)

@app.post("/api/deal")
async def add_deal(deal: Deal):
    # This saves the deal FOREVER in Supabase
    supabase.table("deals").insert(deal.dict()).execute()
    return {"status": "success"}
