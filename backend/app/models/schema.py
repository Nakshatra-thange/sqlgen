from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any
from enum import Enum


class ColumnType(str, Enum):
    """Common column types"""
    INTEGER = "INTEGER"
    VARCHAR = "VARCHAR" 
    TEXT = "TEXT"
    REAL = "REAL"
    BLOB = "BLOB"
    BOOLEAN = "BOOLEAN"
    DATETIME = "DATETIME"
    DATE = "DATE"
    TIME = "TIME"
    DECIMAL = "DECIMAL"
    FLOAT = "FLOAT"
    DOUBLE = "DOUBLE"
    UNKNOWN = "UNKNOWN"


class ColumnInfo(BaseModel):
    """Detailed information about a database column"""
    name: str = Field(..., description="Column name")
    type: str = Field(..., description="Column data type")
    type_category: ColumnType = Field(default=ColumnType.UNKNOWN, description="Standardized column type")
    nullable: bool = Field(default=True, description="Whether column can be NULL")
    primary_key: bool = Field(default=False, description="Whether column is primary key")
    foreign_key: Optional[str] = Field(default=None, description="Foreign key reference (table.column)")
    default_value: Optional[str] = Field(default=None, description="Default value if any")
    max_length: Optional[int] = Field(default=None, description="Maximum length for string types")
    auto_increment: bool = Field(default=False, description="Whether column auto increments")
    
    class Config:
        json_schema_extra = {
            "example": {
                "name": "CustomerId",
                "type": "INTEGER",
                "type_category": "INTEGER",
                "nullable": False,
                "primary_key": True,
                "foreign_key": None,
                "default_value": None,
                "max_length": None,
                "auto_increment": True
            }
        }


class ForeignKeyRelation(BaseModel):
    """Foreign key relationship information"""
    from_table: str = Field(..., description="Source table name")
    from_column: str = Field(..., description="Source column name")
    to_table: str = Field(..., description="Target table name")
    to_column: str = Field(..., description="Target column name")
    constraint_name: Optional[str] = Field(default=None, description="FK constraint name")
    
    class Config:
        json_schema_extra = {
            "example": {
                "from_table": "Invoice",
                "from_column": "CustomerId",
                "to_table": "Customer", 
                "to_column": "CustomerId",
                "constraint_name": "FK_InvoiceCustomerId"
            }
        }


class TableInfo(BaseModel):
    """Complete information about a database table"""
    name: str = Field(..., description="Table name")
    columns: List[ColumnInfo] = Field(..., description="List of columns in the table")
    primary_keys: List[str] = Field(default_factory=list, description="Primary key column names")
    foreign_keys: List[ForeignKeyRelation] = Field(default_factory=list, description="Foreign key relationships")
    row_count: Optional[int] = Field(default=None, description="Approximate number of rows")
    table_comment: Optional[str] = Field(default=None, description="Table description/comment")
    
    @property
    def column_names(self) -> List[str]:
        """Get list of column names"""
        return [col.name for col in self.columns]
    
    @property
    def nullable_columns(self) -> List[str]:
        """Get list of nullable column names"""
        return [col.name for col in self.columns if col.nullable]
    
    @property
    def required_columns(self) -> List[str]:
        """Get list of required (non-nullable) column names"""
        return [col.name for col in self.columns if not col.nullable]
    
    class Config:
        json_schema_extra = {
            "example": {
                "name": "Customer",
                "columns": [
                    {
                        "name": "CustomerId",
                        "type": "INTEGER",
                        "nullable": False,
                        "primary_key": True
                    }
                ],
                "primary_keys": ["CustomerId"],
                "foreign_keys": [],
                "row_count": 59
            }
        }


class DatabaseSchema(BaseModel):
    """Complete database schema information"""
    database_name: str = Field(..., description="Database name/identifier")
    database_type: str = Field(..., description="Database type (sqlite, postgresql, etc.)")
    tables: List[TableInfo] = Field(..., description="List of all tables")
    relationships: List[ForeignKeyRelation] = Field(default_factory=list, description="All foreign key relationships")
    total_tables: int = Field(..., description="Total number of tables")
    schema_version: str = Field(default="1.0", description="Schema version for caching")
    extracted_at: str = Field(..., description="When schema was extracted (ISO timestamp)")
    
    @property
    def table_names(self) -> List[str]:
        """Get list of all table names"""
        return [table.name for table in self.tables]
    
    def get_table(self, table_name: str) -> Optional[TableInfo]:
        """Get table info by name"""
        for table in self.tables:
            if table.name.lower() == table_name.lower():
                return table
        return None
    
    def get_related_tables(self, table_name: str) -> List[str]:
        """Get tables that are related to the given table via foreign keys"""
        related = set()
        for rel in self.relationships:
            if rel.from_table.lower() == table_name.lower():
                related.add(rel.to_table)
            elif rel.to_table.lower() == table_name.lower():
                related.add(rel.from_table)
        return list(related)
    
    def get_join_path(self, table1: str, table2: str) -> List[ForeignKeyRelation]:
        """Find foreign key path between two tables (simple direct relationship)"""
        path = []
        for rel in self.relationships:
            if ((rel.from_table.lower() == table1.lower() and rel.to_table.lower() == table2.lower()) or
                (rel.from_table.lower() == table2.lower() and rel.to_table.lower() == table1.lower())):
                path.append(rel)
        return path
    
    class Config:
        json_schema_extra = {
            "example": {
                "database_name": "chinook",
                "database_type": "sqlite",
                "tables": [],
                "relationships": [],
                "total_tables": 11,
                "schema_version": "1.0",
                "extracted_at": "2024-01-01T12:00:00Z"
            }
        }


# Response models for API endpoints
class SchemaResponse(BaseModel):
    """Response model for schema information"""
    success: bool
    error: Optional[str] = None
    schema: Optional[DatabaseSchema] = None


class TableResponse(BaseModel):
    """Response model for single table information"""
    success: bool
    error: Optional[str] = None
    table: Optional[TableInfo] = None


class RelationshipsResponse(BaseModel):
    """Response model for relationship information"""
    success: bool
    error: Optional[str] = None
    relationships: List[ForeignKeyRelation] = Field(default_factory=list) 