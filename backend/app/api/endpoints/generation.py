from __future__ import annotations
from fastapi import APIRouter, HTTPException
from typing import List, Dict, Optional
import logging

from ...models.requests import SQLGenerationRequest
from ...models.responses import SQLGenerationResponse
from ...services.sql_generation_service import generate_sql, generate_sql_with_examples

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/generate", tags=["SQL Generation"])


@router.post("/sql", response_model=SQLGenerationResponse)
async def generate_sql_endpoint(request: SQLGenerationRequest):
    """
    Generate SQL from natural language query.
    Requires an active database connection.
    """
    try:
        if request.examples:
            response = generate_sql_with_examples(request.query, request.examples)
        else:
            response = generate_sql(request.query)
        
        logger.info(f"Generated SQL for query: '{request.query[:50]}...' (confidence: {response.confidence})")
        return response
        
    except ValueError as e:
        logger.error(f"SQL generation failed: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error in SQL generation: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error during SQL generation")


@router.post("/sql/simple", response_model=SQLGenerationResponse)
async def generate_sql_simple(query: str):
    """
    Simple SQL generation endpoint that accepts just a query string.
    """
    try:
        response = generate_sql(query)
        logger.info(f"Generated SQL for simple query: '{query[:50]}...'")
        return response
        
    except ValueError as e:
        logger.error(f"SQL generation failed: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error in SQL generation: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error during SQL generation")


@router.get("/health")
async def generation_health_check():
    """
    Health check for SQL generation service.
    """
    try:
        # Check if we have an active database connection
        from ...services.database_service import database_service
        current_db = database_service.get_current_database()
        
        if current_db is None:
            return {
                "status": "warning",
                "message": "No active database connection",
                "service": "sql_generation"
            }
        
        return {
            "status": "healthy",
            "message": "SQL generation service is ready",
            "service": "sql_generation",
            "database_connected": True
        }
        
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return {
            "status": "error",
            "message": f"Service error: {str(e)}",
            "service": "sql_generation"
        } 