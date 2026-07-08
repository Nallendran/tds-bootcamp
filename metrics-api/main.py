from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import time, uuid

EMAIL="24ds2000044@ds.study.iitm.ac.in"
ALLOWED_ORIGIN="https://dash-v6mocn.example.com"

app=FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[ALLOWED_ORIGIN],
    allow_credentials=False,
    allow_methods=["GET","OPTIONS"],
    allow_headers=["*"],
)

@app.middleware("http")
async def add_headers(request, call_next):
    start=time.perf_counter()
    response=await call_next(request)
    response.headers["X-Request-ID"]=str(uuid.uuid4())
    response.headers["X-Process-Time"]=f"{time.perf_counter()-start:.6f}"
    return response

@app.get("/stats")
def stats(values:str):
    nums=[int(x.strip()) for x in values.split(",") if x.strip()]
    return {
        "email":EMAIL,
        "count":len(nums),
        "sum":sum(nums),
        "min":min(nums),
        "max":max(nums),
        "mean":sum(nums)/len(nums)
    }
