from __future__ import annotations
import math
import os
import re
from typing import Dict, List, Tuple

from ..models.schema import DatabaseSchema, TableInfo

# Optional embeddings (if OPENAI_API_KEY is set). Fallback to keyword only.
USE_EMBEDDINGS = bool(os.getenv("OPENAI_API_KEY"))

try:
    if USE_EMBEDDINGS:
        from langchain_openai import OpenAIEmbeddings
        _emb = OpenAIEmbeddings()
    else:
        _emb = None
except Exception:
    _emb = None
    USE_EMBEDDINGS = False


def _tokenize(s: str) -> List[str]:
    """Tokenize text into lowercase alphanumeric tokens"""
    return re.findall(r"[a-z0-9_]+", s.lower())


def _table_keywords(t: TableInfo) -> List[str]:
    """Extract keywords from table name, columns, and aliases"""
    toks = _tokenize(t.name)
    for c in t.columns:
        toks.extend(_tokenize(c.name))
        toks.extend(_tokenize(c.type))
    # Add common table name variations
    if t.name.endswith('s'):
        toks.extend(_tokenize(t.name[:-1]))  # customers -> customer
    else:
        toks.extend(_tokenize(t.name + 's'))  # customer -> customers
    return list(dict.fromkeys(toks))  # dedupe, preserve order


def _keyword_score(query: str, table: TableInfo) -> float:
    """Calculate keyword similarity score between query and table"""
    q_toks = set(_tokenize(query))
    t_toks = set(_table_keywords(table))
    if not q_toks or not t_toks:
        return 0.0
    inter = len(q_toks & t_toks)
    return inter / math.sqrt(len(q_toks) * len(t_toks))


def _embed(texts: List[str]) -> List[List[float]]:
    """Embed text using OpenAI embeddings if available"""
    if not _emb:
        return []
    try:
        vecs = _emb.embed_documents(texts)  # returns List[List[float]]
        return vecs
    except Exception:
        return []


def _cosine(a: List[float], b: List[float]) -> float:
    """Calculate cosine similarity between two vectors"""
    try:
        import numpy as np
        va = np.array(a)
        vb = np.array(b)
        denom = (np.linalg.norm(va) * np.linalg.norm(vb)) or 1e-9
        return float(np.dot(va, vb) / denom)
    except ImportError:
        # Fallback if numpy not available
        if len(a) != len(b):
            return 0.0
        dot_product = sum(x * y for x, y in zip(a, b))
        norm_a = math.sqrt(sum(x * x for x in a))
        norm_b = math.sqrt(sum(x * x for x in b))
        denom = norm_a * norm_b or 1e-9
        return dot_product / denom


def select_relevant_tables(
    schema: DatabaseSchema,
    nl_query: str,
    top_k: int = 8
) -> Tuple[List[TableInfo], Dict[str, float]]:
    """
    Rank tables by (keyword + optional embedding) and return top_k.
    Returns: (tables_sorted, score_map)
    """
    # Baseline: keyword scores
    kw_scores: Dict[str, float] = {t.name: _keyword_score(nl_query, t) for t in schema.tables}

    # Embedding: combine with keyword score
    if USE_EMBEDDINGS and _emb:
        table_texts = []
        names = []
        for t in schema.tables:
            names.append(t.name)
            cols = ", ".join([c.name for c in t.columns])
            table_texts.append(f"{t.name}: {cols}")
        try:
            tbl_vecs = _embed(table_texts)
            q_vec = _emb.embed_query(nl_query)
            emb_scores = {names[i]: _cosine(tbl_vecs[i], q_vec) for i in range(len(names))}
        except Exception:
            emb_scores = {n: 0.0 for n in names}
    else:
        emb_scores = {t.name: 0.0 for t in schema.tables}

    # Combine keyword and embedding scores
    combined: Dict[str, float] = {}
    for t in schema.tables:
        combined[t.name] = 0.6 * kw_scores.get(t.name, 0.0) + 0.4 * emb_scores.get(t.name, 0.0)

    # Sort by combined score
    ranked = sorted(schema.tables, key=lambda t: combined.get(t.name, 0.0), reverse=True)
    return ranked[:top_k], combined


def build_schema_snippet(tables: List[TableInfo], schema: DatabaseSchema) -> str:
    """
    Build compact, LLM-friendly schema text.
    Includes relationship hints if neighbors exist in the filtered set.
    """
    chosen = {t.name for t in tables}
    lines: List[str] = []
    
    for t in tables:
        # Table header with columns
        cols = ", ".join([f"{c.name}:{c.type}" for c in t.columns])
        lines.append(f"- {t.name}({cols})")
        
        # Add primary key info
        if t.primary_keys:
            pk_cols = ", ".join(t.primary_keys)
            lines.append(f"  PK: {pk_cols}")
        
        # Relationship hints (only within chosen subset)
        for fk in t.foreign_keys:
            if fk.to_table in chosen:
                via = f" [FK {fk.constraint_name}]" if fk.constraint_name else ""
                lines.append(f"  joins {fk.to_table} ON {t.name}.{fk.from_column} = {fk.to_table}.{fk.to_column}{via}")
    
    return "\n".join(lines)


def get_related_tables_for_query(
    schema: DatabaseSchema,
    nl_query: str,
    include_relationships: bool = True,
    max_tables: int = 10
) -> List[TableInfo]:
    """
    Get relevant tables for a query, optionally including related tables.
    """
    # Get initial relevant tables
    relevant_tables, scores = select_relevant_tables(schema, nl_query, top_k=max_tables)
    
    if not include_relationships:
        return relevant_tables
    
    # Find related tables
    related_tables = set()
    for table in relevant_tables:
        # Add tables that have foreign key relationships with our relevant tables
        for rel in schema.relationships:
            if rel.from_table == table.name:
                related_tables.add(rel.to_table)
            elif rel.to_table == table.name:
                related_tables.add(rel.from_table)
    
    # Add related tables that aren't already in our list
    for table_name in related_tables:
        if not any(t.name == table_name for t in relevant_tables):
            table = schema.get_table(table_name)
            if table and len(relevant_tables) < max_tables:
                relevant_tables.append(table)
    
    return relevant_tables


def create_schema_context(
    schema: DatabaseSchema,
    nl_query: str,
    include_relationships: bool = True,
    max_tables: int = 8
) -> str:
    """
    Create a comprehensive schema context for SQL generation.
    """
    # Get relevant tables
    relevant_tables = get_related_tables_for_query(
        schema, nl_query, include_relationships, max_tables
    )
    
    # Build schema snippet
    schema_snippet = build_schema_snippet(relevant_tables, schema)
    
    # Add database info
    context = f"Database: {schema.database_name} ({schema.database_type})\n"
    context += f"Total tables: {schema.total_tables}\n"
    context += f"Relevant tables ({len(relevant_tables)}):\n"
    context += schema_snippet
    
    return context 