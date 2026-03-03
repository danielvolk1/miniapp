from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from typing import Dict, List

app = FastAPI()

# Integrated State
state = {
    "goal": 10000,
    "results": [],
    "agents_data": {} 
}

class Deal(BaseModel):
    user_id: int
    name: str
    amount: float
    type: str  # FTD / Deposit
    method: str # Crypto / Wire / Stripe
    client_email: str
    client_id: str

@app.get("/", response_class=HTMLResponse)
async def home():
    with open("index.html", "r") as f:
        return f.read()

@app.get("/api/stats")
async def get_stats():
    # Group results by agent for the leaderboard
    leaderboard = {}
    for d in state["results"]:
        name = d['name']
        leaderboard[name] = leaderboard.get(name, 0) + d['amount']
    
    # Sort leaderboard: highest revenue first
    sorted_leaderboard = dict(sorted(leaderboard.items(), key=lambda item: item[1], reverse=True))
    
    total_revenue = sum(d['amount'] for d in state["results"])
    return {
        "total": total_revenue,
        "goal": state["goal"],
        "leaderboard": sorted_leaderboard,
        "recent_deals": state["results"][-5:] # Show last 5 deals
    }

@app.post("/api/deal")
async def add_deal(deal: Deal):
    state["results"].append(deal.dict())
    return {"status": "success"}

# Keep the /api/break logic from the previous message