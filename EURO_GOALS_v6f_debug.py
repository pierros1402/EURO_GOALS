# ==================================================
# EURO_GOALS_v6f_debug.py (Render working version)
# ==================================================

from fastapi import FastAPI
import pandas as pd
import os, sys, time, json, random, threading, requests
from datetime import datetime, timedelta
from typing import Dict

print("🚀 Render new deploy check")

# ==============================================
# FastAPI initialization
# ==============================================
app = FastAPI()

@app.get("/")
def home():
    return {"status": "ok", "message": "EURO_GOALS Render online ✅"}

print("🌍 EURO_GOALS ξεκινά κανονικά...")
