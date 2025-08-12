from __future__ import annotations
from textwrap import dedent

SYSTEM_PROMPT = dedent("""
You are a senior SQL engineer.

RULES:
- Return ONLY executable SQL for the specified dialect. No markdown, no code fences, no comments, no explanations.
- Prefer SELECT queries. Do not write DDL or DML (CREATE/ALTER/INSERT/UPDATE/DELETE/TRUNCATE/DROP) unless explicitly allowed.
- Use only tables/columns that exist in the provided schema context.
- Disambiguate columns with table aliases when necessary.
- When joining, use foreign-key relationships if provided. If none exist, choose reasonable join keys with equality conditions.
- Keep to a single statement.

OUTPUT:
- A single SQL statement as plain text.
""").strip()


def make_user_prompt(dialect: str, task: str, schema_snippet: str, examples: str | None = None) -> str:
    base = f"""DIALECT: {dialect}

TASK:
{task}

SCHEMA CONTEXT (tables, columns, relationships):
{schema_snippet}
"""
    if examples:
        base += f"\nEXAMPLES ({dialect}):\n{examples}\n"
    base += "\nRemember: output ONLY the SQL statement, nothing else."
    return base 