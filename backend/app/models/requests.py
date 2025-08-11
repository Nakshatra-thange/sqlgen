# Pydantic request models
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any

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
    natural_language_query: str
    database_connection_id: int
    context: Optional[Dict[str, Any]] = None

class SQLValidationRequest(BaseModel):
    sql_query: str
    database_connection_id: int 