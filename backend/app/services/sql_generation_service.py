from __future__ import annotations
import os
import re
import time
from typing import Dict, List, Optional, Tuple

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate, SystemMessagePromptTemplate, HumanMessagePromptTemplate

from langchain_openai import ChatOpenAI

from ..models.responses import SQLGenerationResponse
from ..services.database_service import database_service
from ..utils.retrieval import select_relevant_tables, build_schema_snippet, create_schema_context
from ..core.prompts import SYSTEM_PROMPT, make_user_prompt
from ..utils.schema_analyzer import introspect_schema


# Tunables
_MAX_TOKENS = int(os.getenv("GEN_MAX_TOKENS", "256"))
_TEMPERATURE = float(os.getenv("GEN_TEMPERATURE", "0.0"))
_TOP_K_TABLES = int(os.getenv("GEN_TOPK_TABLES", "8"))

# Model
_MODEL = os.getenv("GEN_MODEL_NAME", "gpt-4o-mini")  # pick a small, fast model for latency <2s


def _strip_markdown(sql: str) -> str:
    """Remove markdown code blocks from SQL output"""
    s = sql.strip()
    s = re.sub(r"^```[a-zA-Z]*\s*", "", s)
    s = re.sub(r"\s*```$", "", s)
    return s.strip()


def _single_statement_only(sql: str) -> str:
    """Extract first non-empty SQL statement"""
    # naive: split by semicolon; keep the first non-empty segment
    parts = [p.strip() for p in sql.split(";") if p.strip()]
    if not parts:
        return sql.strip()
    return parts[0]


def _estimate_confidence(raw: str, used_tables: List[str]) -> float:
    """Estimate confidence in generated SQL based on heuristics"""
    score = 0.5
    # heuristic bumps
    if raw.lower().startswith("select"):
        score += 0.2
    if any(t + "." in raw.lower() for t in [t.lower() for t in used_tables]):
        score += 0.15
    if " join " in raw.lower():
        score += 0.05
    score = max(0.0, min(1.0, score))
    return round(score, 2)


def generate_sql(nl_query: str) -> SQLGenerationResponse:
    """
    Main entry: natural language query -> SQL response
    """
    t0 = time.perf_counter()

    # Get current database connection
    current_db = database_service.get_current_database()
    if current_db is None:
        raise ValueError("No active database connection")

    # Get database engine
    engine = current_db._engine
    
    # Introspect schema
    schema = introspect_schema(engine)
    
    # Retrieval: pick top-K relevant tables
    tables, score_map = select_relevant_tables(schema, nl_query, top_k=_TOP_K_TABLES)
    used_tables = [t.name for t in tables]
    
    # Create schema context
    schema_text = create_schema_context(schema, nl_query, include_relationships=True, max_tables=_TOP_K_TABLES)

    # Prompts
    sys_p = SYSTEM_PROMPT
    user_p = make_user_prompt(schema.database_type, nl_query, schema_text, examples=None)

    prompt = ChatPromptTemplate.from_messages([
        SystemMessagePromptTemplate.from_template(sys_p),
        HumanMessagePromptTemplate.from_template("{user}"),
    ])

    chain = prompt | ChatOpenAI(
        model=_MODEL,
        temperature=_TEMPERATURE,
        max_tokens=_MAX_TOKENS,
    ) | StrOutputParser()

    try:
        raw = chain.invoke({"user": user_p})
    except Exception as e:
        raise ValueError(f"SQL generation failed: {str(e)}")

    # Post-process: no markdown, single statement
    raw_sql = _single_statement_only(_strip_markdown(raw))

    latency_ms = int((time.perf_counter() - t0) * 1000)
    confidence = _estimate_confidence(raw_sql, used_tables)

    return SQLGenerationResponse(
        sql=raw_sql,
        explanation=f"Generated SQL using {len(used_tables)} relevant tables",
        confidence=confidence,
        execution_time=latency_ms / 1000.0,
        metadata={
            "dialect": schema.database_type,
            "tables_used": used_tables,
            "model": _MODEL,
            "top_k_tables": _TOP_K_TABLES,
            "schema_tables_total": schema.total_tables
        }
    )


def generate_sql_with_examples(nl_query: str, examples: List[Dict[str, str]]) -> SQLGenerationResponse:
    """
    Generate SQL with example queries for better context
    """
    t0 = time.perf_counter()

    # Get current database connection
    current_db = database_service.get_current_database()
    if current_db is None:
        raise ValueError("No active database connection")

    # Get database engine
    engine = current_db._engine
    
    # Introspect schema
    schema = introspect_schema(engine)
    
    # Retrieval: pick top-K relevant tables
    tables, score_map = select_relevant_tables(schema, nl_query, top_k=_TOP_K_TABLES)
    used_tables = [t.name for t in tables]
    
    # Create schema context
    schema_text = create_schema_context(schema, nl_query, include_relationships=True, max_tables=_TOP_K_TABLES)

    # Format examples
    examples_text = ""
    for i, example in enumerate(examples, 1):
        examples_text += f"Example {i}:\n"
        examples_text += f"Query: {example.get('query', '')}\n"
        examples_text += f"SQL: {example.get('sql', '')}\n\n"

    # Prompts
    sys_p = SYSTEM_PROMPT
    user_p = make_user_prompt(schema.database_type, nl_query, schema_text, examples=examples_text)

    prompt = ChatPromptTemplate.from_messages([
        SystemMessagePromptTemplate.from_template(sys_p),
        HumanMessagePromptTemplate.from_template("{user}"),
    ])

    chain = prompt | ChatOpenAI(
        model=_MODEL,
        temperature=_TEMPERATURE,
        max_tokens=_MAX_TOKENS,
    ) | StrOutputParser()

    try:
        raw = chain.invoke({"user": user_p})
    except Exception as e:
        raise ValueError(f"SQL generation failed: {str(e)}")

    # Post-process: no markdown, single statement
    raw_sql = _single_statement_only(_strip_markdown(raw))

    latency_ms = int((time.perf_counter() - t0) * 1000)
    confidence = _estimate_confidence(raw_sql, used_tables)

    return SQLGenerationResponse(
        sql=raw_sql,
        explanation=f"Generated SQL using {len(used_tables)} relevant tables and {len(examples)} examples",
        confidence=confidence,
        execution_time=latency_ms / 1000.0,
        metadata={
            "dialect": schema.database_type,
            "tables_used": used_tables,
            "model": _MODEL,
            "top_k_tables": _TOP_K_TABLES,
            "schema_tables_total": schema.total_tables,
            "examples_used": len(examples)
        }
    ) 