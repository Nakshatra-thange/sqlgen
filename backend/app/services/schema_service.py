# Schema intelligence
from typing import Dict, Any, List
from sqlalchemy import create_engine, text, inspect

class SchemaService:
    def __init__(self):
        self.engine = None
    
    def set_engine(self, engine):
        """Set the database engine"""
        self.engine = engine
    
    async def get_table_schema(self, table_name: str) -> Dict[str, Any]:
        """Get schema for a specific table"""
        try:
            if not self.engine:
                raise Exception("Database engine not set")
            
            inspector = inspect(self.engine)
            
            # Get columns
            columns = inspector.get_columns(table_name)
            
            # Get primary keys
            primary_keys = inspector.get_pk_constraint(table_name)['constrained_columns']
            
            # Get foreign keys
            foreign_keys = inspector.get_foreign_keys(table_name)
            
            return {
                "table_name": table_name,
                "columns": columns,
                "primary_keys": primary_keys,
                "foreign_keys": foreign_keys
            }
        except Exception as e:
            raise Exception(f"Failed to get table schema: {str(e)}")
    
    async def get_relationships(self) -> List[Dict[str, Any]]:
        """Get relationships between tables"""
        try:
            if not self.engine:
                raise Exception("Database engine not set")
            
            inspector = inspect(self.engine)
            tables = inspector.get_table_names()
            relationships = []
            
            for table in tables:
                foreign_keys = inspector.get_foreign_keys(table)
                for fk in foreign_keys:
                    relationships.append({
                        "table": table,
                        "foreign_key": fk
                    })
            
            return relationships
        except Exception as e:
            raise Exception(f"Failed to get relationships: {str(e)}") 