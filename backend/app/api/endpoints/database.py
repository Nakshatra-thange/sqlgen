from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any
import logging

from services.database_service import database_service
from models.requests import DatabaseConnectionRequest
from models.responses import (
    DatabaseConnectionResponse,
    ConnectionStatusResponse,
    TablesResponse,
    TestConnectionResponse
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/database", tags=["database"])


@router.post("/connect/default", response_model=DatabaseConnectionResponse)
async def connect_to_default_database():
    """
    Connect to the default Chinook SQLite database.
    This will be used for demo purposes and initial testing.
    """
    try:
        result = database_service.connect_to_default_database()
        
        if not result["success"]:
            raise HTTPException(
                status_code=400,
                detail=f"Failed to connect to default database: {result['error']}"
            )
        
        return DatabaseConnectionResponse(**result)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in connect_to_default_database: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error during database connection"
        )


@router.post("/connect/custom", response_model=DatabaseConnectionResponse)
async def connect_to_custom_database(request: DatabaseConnectionRequest):
    """
    Connect to a custom SQLite database.
    Users can provide path to their own SQLite database files.
    """
    try:
        result = database_service.connect_to_custom_database(request.database_path)
        
        if not result["success"]:
            raise HTTPException(
                status_code=400,
                detail=f"Failed to connect to custom database: {result['error']}"
            )
        
        return DatabaseConnectionResponse(**result)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in connect_to_custom_database: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error during database connection"
        )


@router.get("/status", response_model=ConnectionStatusResponse)
async def get_connection_status():
    """
    Get current database connection status and information.
    """
    try:
        result = database_service.get_current_connection_info()
        return ConnectionStatusResponse(**result)
        
    except Exception as e:
        logger.error(f"Error getting connection status: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to get connection status"
        )


@router.get("/tables", response_model=TablesResponse)
async def get_database_tables():
    """
    Get list of tables in the currently connected database.
    Requires an active database connection.
    """
    try:
        result = database_service.get_database_tables()
        
        if not result["success"]:
            raise HTTPException(
                status_code=400,
                detail=result["error"]
            )
        
        return TablesResponse(**result)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting database tables: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to get database tables"
        )


@router.post("/test", response_model=TestConnectionResponse)
async def test_database_connection():
    """
    Test the current database connection.
    Verifies that the database is accessible and responsive.
    """
    try:
        result = database_service.test_current_connection()
        
        if not result["success"]:
            # Don't raise exception for failed test, just return the result
            pass
        
        return TestConnectionResponse(**result)
        
    except Exception as e:
        logger.error(f"Error testing database connection: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to test database connection"
        )


@router.post("/disconnect", response_model=Dict[str, Any])
async def disconnect_database():
    """
    Disconnect from the current database.
    """
    try:
        result = database_service.disconnect()
        
        if not result["success"]:
            raise HTTPException(
                status_code=400,
                detail=result["error"]
            )
        
        return {"message": "Successfully disconnected from database"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error disconnecting from database: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to disconnect from database"
        ) 