"""
J.A.R.V.I.S. Backend API Server
---------------------------------
FastAPI-based HTTP API for the Jarvis Agent system.
Enhanced with rate limiting, timeout control, and WebSocket support.
"""

import asyncio
import json
import logging
import os
import sys
import uuid
import time
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Dict, Any, List, Optional

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv()

import uvicorn
from fastapi import (
    Depends,
    FastAPI,
    HTTPException,
    Request,
    WebSocket,
    WebSocketDisconnect,
    Query,
    status,
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import BaseModel

# Plugin system
try:
    from plugins import PluginManager, PluginRegistry, PluginStatus, PluginCapability
    PLUGIN_SYSTEM_AVAILABLE = True
except ImportError:
    PLUGIN_SYSTEM_AVAILABLE = False
    PluginManager = None
    PluginRegistry = None

