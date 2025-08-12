from fastapi import APIRouter, HTTPException, Query
from typing import Dict, Any, Optional
import logging

from app.services.schema_service import schema_service
from app.models.schema import (
    SchemaResponse,
    TableResponse,
    RelationshipsResponse
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/schema", tags=["schema"])


@router.get("/", response_model=Dict[str, Any])
async def get_complete_schema(
    refresh: bool = Query(False, description="Force refresh of schema cache")
):
    """
    Get complete database schema information including all tables, columns, and relationships.
    Results are cached for 30 minutes unless refresh=true.
    """
    try:
        result = schema_service.get_complete_schema(force_refresh=refresh)
        
        if not result["success"]:
            raise HTTPException(
                status_code=400,
                detail=f"Failed to get schema: {result['error']}"
            )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in get_complete_schema: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error while getting schema"
        )


@router.get("/summary", response_model=Dict[str, Any])
async def get_schema_summary():
    """
    Get a summary of the database schema including statistics and overview information.
    """
    try:
        result = schema_service.get_schema_summary()
        
        if not result["success"]:
            raise HTTPException(
                status_code=400,
                detail=f"Failed to get schema summary: {result['error']}"
            )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in get_schema_summary: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error while getting schema summary"
        )


@router.get("/tables/{table_name}", response_model=TableResponse)
async def get_table_schema(table_name: str):
    """
    Get detailed schema information for a specific table.
    """
    try:
        result = schema_service.get_table_schema(table_name)
        
        if not result["success"]:
            raise HTTPException(
                status_code=404,
                detail=f"Table '{table_name}' not found: {result['error']}"
            )
        
        return TableResponse(**result)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in get_table_schema: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error while getting table schema"
        )


@router.get("/relationships", response_model=RelationshipsResponse)
async def get_relationships(
    table_name: Optional[str] = Query(None, description="Filter relationships for specific table")
):
    """
    Get all foreign key relationships in the database.
    Optionally filter by table name.
    """
    try:
        result = schema_service.get_relationships(table_name)
        
        if not result["success"]:
            raise HTTPException(
                status_code=400,
                detail=f"Failed to get relationships: {result['error']}"
            )
        
        return RelationshipsResponse(**result)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in get_relationships: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error while getting relationships"
        )


@router.get("/tables/{table_name}/related", response_model=Dict[str, Any])
async def get_related_tables(table_name: str):
    """
    Get tables that are related to the specified table via foreign keys.
    """
    try:
        result = schema_service.get_related_tables(table_name)
        
        if not result["success"]:
            raise HTTPException(
                status_code=404,
                detail=f"Table '{table_name}' not found: {result['error']}"
            )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in get_related_tables: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error while getting related tables"
        )


@router.get("/tables/{table_name}/statistics", response_model=Dict[str, Any])
async def get_table_statistics(table_name: str):
    """
    Get statistics for a specific table including row count, column types, etc.
    """
    try:
        result = schema_service.get_table_statistics(table_name)
        
        if not result["success"]:
            raise HTTPException(
                status_code=404,
                detail=f"Table '{table_name}' not found: {result['error']}"
            )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in get_table_statistics: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error while getting table statistics"
        )


@router.get("/search", response_model=Dict[str, Any])
async def search_schema(
    query: str = Query(..., description="Search term for tables, columns, or relationships"),
    search_type: str = Query("all", description="Type of search: 'tables', 'columns', 'relationships', or 'all'")
):
    """
    Search the database schema for tables, columns, or relationships matching the query.
    """
    try:
        result = schema_service.search_schema(query, search_type)
        
        if not result["success"]:
            raise HTTPException(
                status_code=400,
                detail=f"Search failed: {result['error']}"
            )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in search_schema: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error while searching schema"
        )


@router.post("/refresh", response_model=Dict[str, Any])
async def refresh_schema_cache():
    """
    Force refresh of the schema cache.
    Useful when database structure has changed.
    """
    try:
        result = schema_service.refresh_schema_cache()
        
        if not result["success"]:
            raise HTTPException(
                status_code=400,
                detail=f"Failed to refresh schema cache: {result['error']}"
            )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in refresh_schema_cache: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error while refreshing schema cache"
        ) 