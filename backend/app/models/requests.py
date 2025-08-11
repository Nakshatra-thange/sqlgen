# Pydantic request models
from pydantic import BaseModel
from typing import Optional, Dict, Any

class DatabaseConnectionRequest(BaseModel):
    name: str
    connection_string: str
    database_type: str

class SQLGenerationRequest(BaseModel):
    natural_language_query: str
    database_connection_id: int
    context: Optional[Dict[str, Any]] = None

class SQLValidationRequest(BaseModel):
    sql_query: str
    database_connection_id: int 