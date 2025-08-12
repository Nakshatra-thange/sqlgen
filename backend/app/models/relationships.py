from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any
from enum import Enum


class RelationshipType(str, Enum):
    """Types of database relationships"""
    ONE_TO_ONE = "one_to_one"
    ONE_TO_MANY = "one_to_many"
    MANY_TO_ONE = "many_to_one"
    MANY_TO_MANY = "many_to_many"
    UNKNOWN = "unknown"


class JoinType(str, Enum):
    """Types of SQL joins"""
    INNER = "INNER"
    LEFT = "LEFT"
    RIGHT = "RIGHT"
    FULL = "FULL"
    CROSS = "CROSS"


class RelationshipStrength(str, Enum):
    """Strength of relationship based on data analysis"""
    STRONG = "strong"      # High referential integrity
    WEAK = "weak"          # Low referential integrity
    UNKNOWN = "unknown"    # Cannot determine


class JoinPathStep(BaseModel):
    """Single step in a join path between tables"""
    from_table: str = Field(..., description="Source table name")
    from_column: str = Field(..., description="Source column name")
    to_table: str = Field(..., description="Target table name")
    to_column: str = Field(..., description="Target column name")
    join_type: JoinType = Field(default=JoinType.INNER, description="Type of join to use")
    relationship_type: RelationshipType = Field(default=RelationshipType.UNKNOWN, description="Type of relationship")
    constraint_name: Optional[str] = Field(default=None, description="Foreign key constraint name")
    
    class Config:
        json_schema_extra = {
            "example": {
                "from_table": "Invoice",
                "from_column": "CustomerId",
                "to_table": "Customer",
                "to_column": "CustomerId",
                "join_type": "INNER",
                "relationship_type": "many_to_one",
                "constraint_name": "FK_InvoiceCustomerId"
            }
        }


class JoinPath(BaseModel):
    """Complete join path between two tables"""
    start_table: str = Field(..., description="Starting table name")
    end_table: str = Field(..., description="Ending table name")
    steps: List[JoinPathStep] = Field(..., description="List of join steps")
    total_steps: int = Field(..., description="Number of join steps")
    estimated_cost: Optional[float] = Field(default=None, description="Estimated query cost")
    confidence: float = Field(default=1.0, description="Confidence in the path (0.0-1.0)")
    
    @property
    def is_direct(self) -> bool:
        """Check if this is a direct relationship (one step)"""
        return len(self.steps) == 1
    
    @property
    def intermediate_tables(self) -> List[str]:
        """Get list of intermediate tables in the path"""
        if len(self.steps) <= 1:
            return []
        return [step.to_table for step in self.steps[:-1]]
    
    class Config:
        json_schema_extra = {
            "example": {
                "start_table": "Invoice",
                "end_table": "Customer",
                "steps": [
                    {
                        "from_table": "Invoice",
                        "from_column": "CustomerId",
                        "to_table": "Customer",
                        "to_column": "CustomerId",
                        "join_type": "INNER"
                    }
                ],
                "total_steps": 1,
                "confidence": 1.0
            }
        }


class RelationshipAnalysis(BaseModel):
    """Detailed analysis of a relationship"""
    from_table: str = Field(..., description="Source table name")
    from_column: str = Field(..., description="Source column name")
    to_table: str = Field(..., description="Target table name")
    to_column: str = Field(..., description="Target column name")
    relationship_type: RelationshipType = Field(..., description="Type of relationship")
    strength: RelationshipStrength = Field(..., description="Relationship strength")
    referential_integrity: float = Field(..., description="Referential integrity percentage (0.0-1.0)")
    sample_data: Optional[Dict[str, Any]] = Field(default=None, description="Sample data from the relationship")
    constraint_info: Optional[Dict[str, Any]] = Field(default=None, description="Constraint information")
    
    class Config:
        json_schema_extra = {
            "example": {
                "from_table": "Invoice",
                "from_column": "CustomerId",
                "to_table": "Customer",
                "to_column": "CustomerId",
                "relationship_type": "many_to_one",
                "strength": "strong",
                "referential_integrity": 0.95,
                "sample_data": {
                    "total_invoices": 1000,
                    "unique_customers": 59,
                    "avg_invoices_per_customer": 16.95
                }
            }
        }


class RelationshipGraph(BaseModel):
    """Graph representation of database relationships"""
    nodes: List[Dict[str, Any]] = Field(..., description="Table nodes with metadata")
    edges: List[Dict[str, Any]] = Field(..., description="Relationship edges")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Graph metadata")
    
    class Config:
        json_schema_extra = {
            "example": {
                "nodes": [
                    {"id": "Customer", "type": "table", "row_count": 59},
                    {"id": "Invoice", "type": "table", "row_count": 1000}
                ],
                "edges": [
                    {
                        "from": "Invoice",
                        "to": "Customer",
                        "type": "many_to_one",
                        "strength": "strong"
                    }
                ],
                "metadata": {
                    "total_tables": 11,
                    "total_relationships": 8,
                    "graph_type": "directed"
                }
            }
        }


# Request models
class JoinPathRequest(BaseModel):
    """Request model for finding join paths"""
    start_table: str = Field(..., description="Starting table name")
    end_table: str = Field(..., description="Ending table name")
    max_steps: int = Field(default=3, description="Maximum number of join steps")
    prefer_direct: bool = Field(default=True, description="Prefer direct relationships")
    
    class Config:
        json_schema_extra = {
            "example": {
                "start_table": "Invoice",
                "end_table": "Customer",
                "max_steps": 3,
                "prefer_direct": True
            }
        }


class RelationshipAnalysisRequest(BaseModel):
    """Request model for relationship analysis"""
    table_name: str = Field(..., description="Table to analyze relationships for")
    include_sample_data: bool = Field(default=True, description="Include sample data in analysis")
    analyze_integrity: bool = Field(default=True, description="Analyze referential integrity")
    
    class Config:
        json_schema_extra = {
            "example": {
                "table_name": "Invoice",
                "include_sample_data": True,
                "analyze_integrity": True
            }
        }


# Response models
class JoinPathResponse(BaseModel):
    """Response model for join path results"""
    success: bool
    error: Optional[str] = None
    paths: List[JoinPath] = Field(default_factory=list)
    best_path: Optional[JoinPath] = None
    total_paths_found: int = Field(default=0)


class RelationshipAnalysisResponse(BaseModel):
    """Response model for relationship analysis"""
    success: bool
    error: Optional[str] = None
    table_name: str
    relationships: List[RelationshipAnalysis] = Field(default_factory=list)
    summary: Dict[str, Any] = Field(default_factory=dict)


class RelationshipGraphResponse(BaseModel):
    """Response model for relationship graph"""
    success: bool
    error: Optional[str] = None
    graph: Optional[RelationshipGraph] = None
    format: str = Field(default="json", description="Graph format (json, dot, etc.)")


class RelationshipStatisticsResponse(BaseModel):
    """Response model for relationship statistics"""
    success: bool
    error: Optional[str] = None
    statistics: Dict[str, Any] = Field(default_factory=dict)
    recommendations: List[str] = Field(default_factory=list) 