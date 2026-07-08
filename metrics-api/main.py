from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import jwt
import time
import uuid
import os
import yaml
from dotenv import load_dotenv

EMAIL = "24ds2000044@ds.study.iitm.ac.in"

load_dotenv()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

import os

@app.get("/debug")
def debug():
    return {
        "cwd": os.getcwd(),
        "files": os.listdir(".")
    }

@app.middleware("http")
async def add_headers(request, call_next):
    start = time.perf_counter()
    response = await call_next(request)

    response.headers["X-Request-ID"] = str(uuid.uuid4())
    response.headers["X-Process-Time"] = f"{time.perf_counter() - start:.6f}"

    return response


@app.get("/")
def home():
    return {"status": "running"}


# ---------- QUESTION 3 ----------

def to_bool(v):
    return str(v).lower() in ("true", "1", "yes", "on")


@app.get("/effective-config")
def effective_config(set: list[str] = Query(default=[])):
    config = {
        "port": 8000,
        "workers": 1,
        "debug": False,
        "log_level": "info",
        "api_key": "default-secret-000",
    }

    # YAML layer
    if os.path.exists("config.development.yaml"):
        with open("config.development.yaml") as f:
            yaml_cfg = yaml.safe_load(f) or {}
            config.update(yaml_cfg)

    # .env layer
    if os.getenv("APP_PORT"):
        config["port"] = int(os.getenv("APP_PORT"))

    if os.getenv("NUM_WORKERS"):
        config["workers"] = int(os.getenv("NUM_WORKERS"))

    if os.getenv("APP_DEBUG"):
        config["debug"] = to_bool(os.getenv("APP_DEBUG"))

    if os.getenv("APP_API_KEY"):
        config["api_key"] = os.getenv("APP_API_KEY")

    # OS ENV layer
    if os.getenv("APP_WORKERS"):
        config["workers"] = int(os.getenv("APP_WORKERS"))

    # CLI overrides
    for item in set:
        if "=" not in item:
            continue

        key, value = item.split("=", 1)

        if key in ("port", "workers"):
            config[key] = int(value)

        elif key == "debug":
            config[key] = to_bool(value)

        else:
            config[key] = value

    # Mask secret
    config["api_key"] = "****"

    return config


# ---------- QUESTION 2 ----------

ISSUER = "https://idp.exam.local"
AUDIENCE = "tds-46cz6ve6.apps.exam.local"

PUBLIC_KEY = """
-----BEGIN PUBLIC KEY-----
MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEA2okOHspNjgA+2rTLbeuY
cxiP/hG8C6Sb9iwg3yiLAA4HCnpITcbWCSelbvbYGuc3EbNy4xFyf5Cbj5DHJMID
EkryOgyd2giIIIBOUBj8S63uGcnRpOBh9NFatfNwheKuzsPuVNldu6A9cNteNpXc
WyJjG2axVfmq7i6SuKr1JoWYG7xTTAvKPujSl4OtsQfO3h5NepzdfXpr28oNnzfW
ed+zclR6BcmNNo/WVfJ4xyCLSf0BCOgdTgW6PdaChd1l9VDetJZVEgC5tkyvXsfI
SI6iyrYbKR0NEBSqq4XkadEjsCs4F1RncsS4LlgniT7GlkL9Mce3b0wGLs9/7ZIX
dQIDAQAB
-----END PUBLIC KEY-----
"""


class TokenRequest(BaseModel):
    token: str


@app.post("/verify")
def verify(request: TokenRequest):
    try:
        payload = jwt.decode(
            request.token,
            PUBLIC_KEY,
            algorithms=["RS256"],
            issuer=ISSUER,
            audience=AUDIENCE,
        )

        return {
            "valid": True,
            "email": payload.get("email"),
            "sub": payload.get("sub"),
            "aud": payload.get("aud"),
        }

    except Exception:
        return JSONResponse(
            status_code=401,
            content={"valid": False},
        )