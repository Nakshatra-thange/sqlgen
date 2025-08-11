from langchain_community.utilities import SQLDatabase
from typing import Optional, Dict, List, Any
from utils.database_factory import DatabaseFactory
import logging

logger = logging.getLogger(__name__)


class DatabaseService:
    """Service for managing database connections and operations"""
    
    def __init__(self):
        self._current_db: Optional[SQLDatabase] = None
        self._connection_info: Dict[str, Any] = {}
    
    def connect_to_default_database(self) -> Dict[str, Any]:
        """Connect to the default Chinook database"""
        try:
            db, error = DatabaseFactory.get_default_connection()
            
            if error:
                return {
                    "success": False,
                    "error": error,
                    "connection_info": None
                }
            
            # Test the connection
            is_working, test_error = DatabaseFactory.test_connection(db)
            
            if not is_working:
                return {
                    "success": False,
                    "error": f"Connection test failed: {test_error}",
                    "connection_info": None
                }
            
            # Store connection
            self._current_db = db
            self._connection_info = {
                "database_type": "sqlite",
                "database_path": "chinook.db",
                "dialect": db.dialect,
                "tables_count": len(db.get_usable_table_names())
            }
            
            logger.info("Successfully connected to default database")
            
            return {
                "success": True,
                "error": None,
                "connection_info": self._connection_info
            }
            
        except Exception as e:
            logger.error(f"Failed to connect to default database: {str(e)}")
            return {
                "success": False,
                "error": f"Unexpected error: {str(e)}",
                "connection_info": None
            }
    
    def connect_to_custom_database(self, db_path: str) -> Dict[str, Any]:
        """Connect to a custom SQLite database"""
        try:
            db, error = DatabaseFactory.create_sqlite_connection(db_path)
            
            if error:
                return {
                    "success": False,
                    "error": error,
                    "connection_info": None
                }
            
            # Test the connection
            is_working, test_error = DatabaseFactory.test_connection(db)
            
            if not is_working:
                return {
                    "success": False,
                    "error": f"Connection test failed: {test_error}",
                    "connection_info": None
                }
            
            # Store connection
            self._current_db = db
            self._connection_info = {
                "database_type": "sqlite",
                "database_path": db_path,
                "dialect": db.dialect,
                "tables_count": len(db.get_usable_table_names())
            }
            
            logger.info(f"Successfully connected to custom database: {db_path}")
            
            return {
                "success": True,
                "error": None,
                "connection_info": self._connection_info
            }
            
        except Exception as e:
            logger.error(f"Failed to connect to custom database: {str(e)}")
            return {
                "success": False,
                "error": f"Unexpected error: {str(e)}",
                "connection_info": None
            }
    
    def get_current_connection_info(self) -> Dict[str, Any]:
        """Get information about current database connection"""
        if not self._current_db:
            return {
                "connected": False,
                "connection_info": None
            }
        
        return {
            "connected": True,
            "connection_info": self._connection_info
        }
    
    def get_database_tables(self) -> Dict[str, Any]:
        """Get list of tables in current database"""
        if not self._current_db:
            return {
                "success": False,
                "error": "No database connection",
                "tables": []
            }
        
        try:
            tables = self._current_db.get_usable_table_names()
            return {
                "success": True,
                "error": None,
                "tables": tables
            }
        except Exception as e:
            logger.error(f"Failed to get tables: {str(e)}")
            return {
                "success": False,
                "error": f"Failed to get tables: {str(e)}",
                "tables": []
            }
    
    def test_current_connection(self) -> Dict[str, Any]:
        """Test current database connection"""
        if not self._current_db:
            return {
                "success": False,
                "error": "No database connection"
            }
        
        is_working, error = DatabaseFactory.test_connection(self._current_db)
        
        return {
            "success": is_working,
            "error": error
        }
    
    def get_current_database(self) -> Optional[SQLDatabase]:
        """Get current LangChain SQLDatabase instance for SQL generation"""
        return self._current_db
    
    def disconnect(self) -> Dict[str, Any]:
        """Disconnect from current database"""
        try:
            self._current_db = None
            self._connection_info = {}
            
            return {
                "success": True,
                "error": None
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Error during disconnect: {str(e)}"
            }


# Global database service instance
database_service = DatabaseService() 