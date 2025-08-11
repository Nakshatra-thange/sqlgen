# Pydantic response models
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime

class ConnectionInfo(BaseModel):
    """Database connection information"""
    database_type: str
    database_path: str
    dialect: str
    tables_count: int

class DatabaseConnectionResponse(BaseModel):
    """Response model for database connection"""
    success: bool
    error: Optional[str] = None
    connection_info: Optional[ConnectionInfo] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "error": None,
                "connection_info": {
                    "database_type": "sqlite",
                    "database_path": "chinook.db",
                    "dialect": "sqlite",
                    "tables_count": 11
                }
            }
        }

class ConnectionStatusResponse(BaseModel):
    """Response model for connection status"""
    connected: bool
    connection_info: Optional[ConnectionInfo] = None

class TablesResponse(BaseModel):
    """Response model for database tables"""
    success: bool
    error: Optional[str] = None
    tables: List[str] = []
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "error": None,
                "tables": ["Album", "Artist", "Customer", "Employee", "Genre", "Invoice"]
            }
        }

class TestConnectionResponse(BaseModel):
    """Response model for connection test"""
    success: bool
    error: Optional[str] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "error": None
            }
        }

class SQLGenerationResponse(BaseModel):
    sql: str
    explanation: str
    confidence: float
    execution_time: float

class TableSchemaResponse(BaseModel):
    table_name: str
    columns: List[Dict[str, Any]]
    primary_keys: List[str]
    foreign_keys: List[Dict[str, Any]]

class ErrorResponse(BaseModel):
    error: str
    detail: Optional[str] = None 