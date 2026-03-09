"""
Daily verse route.
"""
import logging
from fastapi import APIRouter, HTTPException
from app.services.daily_service import daily_service

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/daily")
async def get_daily():
    try:
        result = await daily_service.get_daily_verse()
        if not result:
            raise HTTPException(status_code=404, detail="No verses found")
        return {"success": True, "data": result}
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Daily verse error: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail="Daily verse failed")
