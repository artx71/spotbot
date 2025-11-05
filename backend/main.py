"""
SpotBot API - FastAPI Backend
Main API server for SpotBot chat functionality
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict
from chat_service import chat_service
from rag_service import rag_service
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
import atexit
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="SpotBot API", version="1.0.0")

# Initialize scheduler for automatic training
scheduler = BackgroundScheduler()


def train_bot():
    """Training job that reloads mock data"""
    try:
        logger.info("Starting automatic bot training...")
        success = rag_service.train()
        if success:
            logger.info("Bot training completed successfully")
        else:
            logger.warning("Bot training completed with warnings")
    except Exception as e:
        logger.error(f"Error during bot training: {e}")


# Schedule automatic training every minute
scheduler.add_job(
    func=train_bot,
    trigger=CronTrigger(second=0),  # Run every minute at :00 seconds
    id='auto_train_bot',
    name='Automatic Bot Training',
    replace_existing=True
)

# Start scheduler when app starts
@app.on_event("startup")
def startup_event():
    """Start the scheduler and run initial training"""
    scheduler.start()
    logger.info("Scheduler started - bot will train automatically every minute")
    # Run initial training on startup
    train_bot()


# Shutdown scheduler when app stops
@app.on_event("shutdown")
def shutdown_event():
    """Stop the scheduler"""
    scheduler.shutdown()
    logger.info("Scheduler stopped")

# CORS middleware for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],  # React dev servers
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request/Response models
class ChatMessage(BaseModel):
    message: str
    user_id: Optional[str] = "default_user"


class ChatResponse(BaseModel):
    response: str
    history: List[Dict]
    hackathon_data: Optional[Dict] = None


class HistoryResponse(BaseModel):
    history: List[Dict]


# API Endpoints
@app.get("/")
def root():
    return {
        "message": "SpotBot API is running",
        "version": "1.0.0",
        "endpoints": {
            "/api/spotbot/query": "POST - Send a chat message",
            "/api/spotbot/history": "GET - Get conversation history",
            "/api/spotbot/clear": "POST - Clear conversation history"
        }
    }


@app.post("/api/spotbot/query", response_model=ChatResponse)
async def chat_query(message_data: ChatMessage):
    """
    Process a chat message and return bot response
    """
    try:
        result = chat_service.process_message(
            user_id=message_data.user_id or "default_user",
            message=message_data.message
        )
        return ChatResponse(
            response=result["response"],
            history=result["history"],
            hackathon_data=result.get("hackathon_data")
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/spotbot/history/{user_id}", response_model=HistoryResponse)
async def get_history(user_id: str):
    """
    Get conversation history for a user
    """
    try:
        history = chat_service.get_conversation_history(user_id)
        return HistoryResponse(history=history)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/spotbot/clear/{user_id}")
async def clear_history(user_id: str):
    """
    Clear conversation history for a user
    """
    try:
        chat_service.clear_conversation(user_id)
        return {"message": "Conversation history cleared", "user_id": user_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/spotbot/train")
async def manual_train():
    """
    Manually trigger bot training (reloads mock data)
    """
    try:
        success = rag_service.train()
        return {
            "message": "Bot training completed" if success else "Bot training completed with warnings",
            "success": success
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class CreateHackathonRequest(BaseModel):
    hackathon_data: Dict
    user_id: Optional[str] = "default_user"


@app.post("/api/spotbot/create")
async def create_hackathon(request: CreateHackathonRequest):
    """
    Create a hackathon from draft data
    """
    try:
        hackathon = chat_service.create_hackathon(
            user_id=request.user_id or "default_user",
            hackathon_data=request.hackathon_data
        )
        return {
            "success": True,
            "hackathon": hackathon,
            "message": f"Hackathon '{hackathon['title']}' created successfully!"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
