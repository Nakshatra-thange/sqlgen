from __future__ import annotations
import hashlib
import re
from typing import Dict, List, Set, Tuple, Optional, Any
from datetime import datetime

from sqlalchemy import inspect, text
from sqlalchemy.engine import Engine
from sqlalchemy.sql.schema import Column

from ..models.schema import (
    ColumnInfo,
    ForeignKeyRelation,
    TableInfo,
    DatabaseSchema,
    ColumnType
)


def _normalize_identifier(name: str) -> str:
    """Normalize table/column names for comparison"""
    s = name.strip().lower()
    s = re.sub(r"[\s\-]+", "_", s)
    return s


def _table_aliases(name: str) -> List[str]:
    """Generate common aliases for table names"""
    base = _normalize_identifier(name)
    aliases = {base}
    if base.endswith("s"):
        aliases.add(base[:-1])  # customers -> customer
    else:
        aliases.add(base + "s")
    
    # common domain synonyms
    syn = {
        "user": ["customer", "account"],
        "order": ["purchase", "sale"],
        "product": ["item", "sku"],
    }
    for k, arr in syn.items():
        if k in base:
            aliases.update(arr)
    return sorted(aliases)


def _dialect_from_engine(engine: Engine) -> str:
    """Extract database dialect from SQLAlchemy engine"""
    name = engine.dialect.name
    if name.startswith("postgres"):
        return "postgresql"
    if name.startswith("mysql"):
        return "mysql"
    if name.startswith("sqlite"):
        return "sqlite"
    return name


def _map_column_type(column_type: str) -> ColumnType:
    """Map database column type to standardized ColumnType enum"""
    type_str = str(column_type).upper()
    
    if any(t in type_str for t in ["INT", "BIGINT", "SMALLINT"]):
        return ColumnType.INTEGER
    elif any(t in type_str for t in ["VARCHAR", "CHAR"]):
        return ColumnType.VARCHAR
    elif "TEXT" in type_str:
        return ColumnType.TEXT
    elif any(t in type_str for t in ["REAL", "DOUBLE", "FLOAT"]):
        return ColumnType.REAL
    elif "BLOB" in type_str:
        return ColumnType.BLOB
    elif "BOOLEAN" in type_str or "BOOL" in type_str:
        return ColumnType.BOOLEAN
    elif "DATETIME" in type_str:
        return ColumnType.DATETIME
    elif "DATE" in type_str:
        return ColumnType.DATE
    elif "TIME" in type_str:
        return ColumnType.TIME
    elif "DECIMAL" in type_str:
        return ColumnType.DECIMAL
    else:
        return ColumnType.UNKNOWN


def introspect_schema(engine: Engine, database_name: Optional[str] = None) -> DatabaseSchema:
    """
    Introspect database schema and return structured schema information.
    Read-only operation, no data access.
    """
    inspector = inspect(engine)
    dialect = _dialect_from_engine(engine)
    dbname = database_name or (engine.url.database or "default")

    tables_info: List[TableInfo] = []
    all_relationships: List[ForeignKeyRelation] = []
    total_columns = 0

    for table_name in inspector.get_table_names():
        # Get columns
        columns_info: List[ColumnInfo] = []
        raw_columns = inspector.get_columns(table_name)
        
        # Get primary keys
        pk_constraint = inspector.get_pk_constraint(table_name)
        pk_columns = pk_constraint.get("constrained_columns", [])
        
        # Get foreign keys
        raw_foreign_keys = inspector.get_foreign_keys(table_name)
        table_foreign_keys: List[ForeignKeyRelation] = []
        
        for col in raw_columns:
            col_name = col["name"]
            col_type = str(col.get("type", "UNKNOWN"))
            
            # Check if this column is a foreign key
            fk_info = None
            for fk in raw_foreign_keys:
                if col_name in fk.get("constrained_columns", []):
                    fk_info = fk
                    break
            
            column_info = ColumnInfo(
                name=col_name,
                type=col_type,
                type_category=_map_column_type(col_type),
                nullable=bool(col.get("nullable", True)),
                primary_key=col_name in pk_columns,
                foreign_key=f"{fk_info['referred_table']}.{fk_info['referred_columns'][0]}" if fk_info else None,
                default_value=str(col.get("default")) if col.get("default") is not None else None,
                max_length=getattr(col.get("type"), "length", None) if hasattr(col.get("type"), "length") else None,
                auto_increment=bool(col.get("autoincrement", False))
            )
            columns_info.append(column_info)
            
            # Create foreign key relationship
            if fk_info:
                fk_relation = ForeignKeyRelation(
                    from_table=table_name,
                    from_column=col_name,
                    to_table=fk_info["referred_table"],
                    to_column=fk_info["referred_columns"][0] if fk_info["referred_columns"] else col_name,
                    constraint_name=fk_info.get("name")
                )
                table_foreign_keys.append(fk_relation)
                all_relationships.append(fk_relation)
        
        total_columns += len(columns_info)
        
        # Create table info
        table_info = TableInfo(
            name=table_name,
            columns=columns_info,
            primary_keys=pk_columns,
            foreign_keys=table_foreign_keys,
            row_count=None,  # Will be populated later if needed
            table_comment=None
        )
        tables_info.append(table_info)

    # Create database schema
    schema = DatabaseSchema(
        database_name=dbname,
        database_type=dialect,
        tables=tables_info,
        relationships=all_relationships,
        total_tables=len(tables_info),
        schema_version="1.0",
        extracted_at=datetime.utcnow().isoformat()
    )
    
    return schema


def find_shortest_join_path(schema: DatabaseSchema, start: str, end: str) -> Optional[List[str]]:
    """
    Find shortest join path between two tables using BFS.
    Returns list of table names in the path.
    """
    if start == end:
        return [start]
    
    # Build adjacency list from relationships
    graph: Dict[str, List[str]] = {}
    for rel in schema.relationships:
        if rel.from_table not in graph:
            graph[rel.from_table] = []
        if rel.to_table not in graph:
            graph[rel.to_table] = []
        graph[rel.from_table].append(rel.to_table)
        graph[rel.to_table].append(rel.from_table)
    
    if start not in graph or end not in graph:
        return None
    
    # BFS to find shortest path
    from collections import deque
    queue = deque([(start, [start])])
    visited = {start}
    
    while queue:
        current, path = queue.popleft()
        
        for neighbor in graph[current]:
            if neighbor == end:
                return path + [neighbor]
            
            if neighbor not in visited:
                visited.add(neighbor)
                queue.append((neighbor, path + [neighbor]))
    
    return None


def materialize_join_edges(schema: DatabaseSchema, path: List[str]) -> List[ForeignKeyRelation]:
    """
    Convert a table path into concrete foreign key relationships.
    Returns list of ForeignKeyRelation objects for the path.
    """
    if len(path) < 2:
        return []
    
    edges: List[ForeignKeyRelation] = []
    
    for i in range(len(path) - 1):
        table1, table2 = path[i], path[i + 1]
        
        # Find foreign key relationship between these tables
        found_relation = None
        for rel in schema.relationships:
            if ((rel.from_table == table1 and rel.to_table == table2) or
                (rel.from_table == table2 and rel.to_table == table1)):
                found_relation = rel
                break
        
        if found_relation:
            edges.append(found_relation)
        else:
            # Create a placeholder for missing relationship
            placeholder = ForeignKeyRelation(
                from_table=table1,
                from_column="unknown",
                to_table=table2,
                to_column="unknown",
                constraint_name=None
            )
            edges.append(placeholder)
    
    return edges


def analyze_relationships(schema: DatabaseSchema) -> Dict[str, Any]:
    """
    Analyze relationships in the schema and return statistics.
    """
    analysis = {
        "total_tables": len(schema.tables),
        "total_relationships": len(schema.relationships),
        "tables_with_relationships": len(set(
            rel.from_table for rel in schema.relationships
        ).union(set(rel.to_table for rel in schema.relationships))),
        "isolated_tables": [],
        "relationship_distribution": {},
        "most_connected_tables": []
    }
    
    # Find isolated tables (no relationships)
    connected_tables = set()
    for rel in schema.relationships:
        connected_tables.add(rel.from_table)
        connected_tables.add(rel.to_table)
    
    all_tables = {table.name for table in schema.tables}
    analysis["isolated_tables"] = list(all_tables - connected_tables)
    
    # Count relationships per table
    table_relationship_count = {}
    for rel in schema.relationships:
        table_relationship_count[rel.from_table] = table_relationship_count.get(rel.from_table, 0) + 1
        table_relationship_count[rel.to_table] = table_relationship_count.get(rel.to_table, 0) + 1
    
    # Find most connected tables
    sorted_tables = sorted(table_relationship_count.items(), key=lambda x: x[1], reverse=True)
    analysis["most_connected_tables"] = sorted_tables[:5]
    
    return analysis


def generate_schema_hash(schema: DatabaseSchema) -> str:
    """
    Generate a deterministic hash of the schema for change detection.
    """
    hash_input = []
    
    # Sort tables and columns for deterministic output
    for table in sorted(schema.tables, key=lambda x: x.name):
        hash_input.append(table.name)
        for col in sorted(table.columns, key=lambda x: x.name):
            hash_input.extend([col.name, col.type, "1" if col.nullable else "0"])
        
        for fk in sorted(table.foreign_keys, key=lambda x: (x.from_table, x.to_table)):
            hash_input.extend([fk.from_table, fk.to_table, fk.from_column, fk.to_column])
    
    hash_string = "|".join(hash_input)
    return hashlib.sha256(hash_string.encode("utf-8")).hexdigest()[:16]