# DB connection logic
from typing import Dict, Any, List
import sqlalchemy
from sqlalchemy import create_engine, text

class DatabaseService:
    def __init__(self):
        self.connections = {}
    
    async def connect(self, connection_params: Dict[str, Any]) -> bool:
        """Connect to a database"""
        try:
            connection_string = connection_params.get("connection_string")
            engine = create_engine(connection_string)
            
            # Test connection
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            
            self.connections[connection_params.get("name")] = engine
            return True
        except Exception as e:
            raise Exception(f"Failed to connect to database: {str(e)}")
    
    async def get_tables(self, connection_name: str) -> List[str]:
        """Get all tables from connected database"""
        try:
            engine = self.connections.get(connection_name)
            if not engine:
                raise Exception("Database not connected")
            
            with engine.connect() as conn:
                result = conn.execute(text("SHOW TABLES"))
                return [row[0] for row in result]
        except Exception as e:
            raise Exception(f"Failed to get tables: {str(e)}") 