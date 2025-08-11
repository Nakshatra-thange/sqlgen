from langchain_community.utilities import SQLDatabase
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
import os
from typing import Optional, Tuple
from utils.config import settings


class DatabaseFactory:
    """Factory for creating database connections"""
    
    @staticmethod
    def create_sqlite_connection(db_path: str) -> Tuple[Optional[SQLDatabase], Optional[str]]:
        """
        Create SQLite connection using LangChain's SQLDatabase
        Returns: (SQLDatabase instance, error_message)
        """
        try:
            # Check if file exists
            if not os.path.exists(db_path):
                return None, f"Database file not found: {db_path}"
            
            # Create SQLite URI
            sqlite_uri = f"sqlite:///{db_path}"
            
            # Test basic connection first
            engine = create_engine(sqlite_uri)
            with engine.connect() as conn:
                # Test if it's a valid SQLite database
                result = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table' LIMIT 1;"))
                result.fetchone()  # This will fail if not a valid SQLite DB
            
            # Create LangChain SQLDatabase instance
            db = SQLDatabase.from_uri(sqlite_uri)
            
            # Validate it has tables
            tables = db.get_usable_table_names()
            if not tables:
                return None, "Database contains no tables"
            
            return db, None
            
        except SQLAlchemyError as e:
            return None, f"Database connection error: {str(e)}"
        except Exception as e:
            return None, f"Unexpected error: {str(e)}"
    
    @staticmethod
    def get_default_connection() -> Tuple[Optional[SQLDatabase], Optional[str]]:
        """Get default SQLite connection (Chinook database)"""
        return DatabaseFactory.create_sqlite_connection(settings.SQLITE_DB_PATH)
    
    @staticmethod
    def test_connection(db: SQLDatabase) -> Tuple[bool, Optional[str]]:
        """Test if database connection is working"""
        try:
            # Try to get table names
            tables = db.get_usable_table_names()
            
            # Try a simple query
            result = db.run("SELECT 1 as test_query;")
            
            if "1" in str(result):
                return True, None
            else:
                return False, "Test query failed"
                
        except Exception as e:
            return False, f"Connection test failed: {str(e)}" 