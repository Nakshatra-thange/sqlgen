from __future__ import annotations
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List


class DatabaseConnectionRequest(BaseModel):
    """Request model for custom database connection"""
    database_path: str = Field(..., description="Path to SQLite database file")
    
    class Config:
        json_schema_extra = {
            "example": {
                "database_path": "/path/to/your/database.db"
            }
        }


class SQLGenerationRequest(BaseModel):
    """Request model for SQL generation from natural language"""
    query: str = Field(..., description="Natural language query to convert to SQL")
    examples: Optional[List[Dict[str, str]]] = Field(default=None, description="Optional example queries for context")
    
    class Config:
        json_schema_extra = {
            "example": {
                "query": "Show me all customers who made purchases in the last month",
                "examples": [
                    {
                        "query": "Get all customers",
                        "sql": "SELECT * FROM Customer"
                    }
                ]
            }
        }


class SQLValidationRequest(BaseModel):
    """Request model for SQL validation"""
    sql_query: str = Field(..., description="SQL query to validate")
    database_connection_id: int = Field(..., description="Database connection identifier") 