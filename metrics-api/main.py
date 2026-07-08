from fastapi import FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

EMAIL = "24ds2000044@ds.study.iitm.ac.in"
API_KEY = "ak_jyh4729t2cnetyru5uy6mg8g"

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/analytics")
def analytics(payload: dict, x_api_key: str = Header(None)):
    if x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Unauthorized")

    events = payload.get("events", [])

    total_events = len(events)
    unique_users = len(set(e["user"] for e in events))

    revenue = sum(
        e["amount"]
        for e in events
        if e.get("amount", 0) > 0
    )

    user_totals = {}

    for e in events:
        if e.get("amount", 0) > 0:
            user = e["user"]
            user_totals[user] = user_totals.get(user, 0) + e["amount"]

    top_user = max(user_totals, key=user_totals.get) if user_totals else ""

    return {
        "email": EMAIL,
        "total_events": total_events,
        "unique_users": unique_users,
        "revenue": revenue,
        "top_user": top_user
    }