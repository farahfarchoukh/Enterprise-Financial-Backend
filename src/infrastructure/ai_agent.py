import json
from openai import AsyncOpenAI
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from src.config import get_settings
from typing import List, Dict

settings = get_settings()
client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

# --- PROMPT ENGINEERING ---
SYSTEM_SQL = """
You are a Data Analyst. Convert questions to SQLite SQL.
Table: financial_records
Cols: transaction_date (Date), description, category, amount (Signed Float), record_type, source.

RULES:
1. Output ONLY raw SQL. No markdown.
2. Revenue = SUM(amount) WHERE amount > 0
3. Expense = SUM(amount) WHERE amount < 0
4. Profit = SUM(amount)
5. Use strftime('%Y-%m', transaction_date) for monthly grouping.
"""

SYSTEM_NARRATIVE = """
You are a CFO. Analyze the provided data and answer the user's question.
1. Be concise.
2. Highlight trends (e.g., "up 20%").
3. Use professional tone.
"""

class FinancialAgent:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def _get_sql(self, question: str, history: List[Dict]) -> str:
        messages = [{"role": "system", "content": SYSTEM_SQL}]
        # Add Context
        for msg in history[-3:]: 
            messages.append({"role": msg["role"], "content": msg["content"]})
        messages.append({"role": "user", "content": question})

        resp = await client.chat.completions.create(
            model=settings.AI_MODEL, messages=messages, temperature=0
        )
        sql = resp.choices[0].message.content.strip()
        return sql.replace("```sql", "").replace("```", "").strip()

    async def run(self, question: str, history: List[Dict]):
        # 1. Reason & Generate SQL
        sql = await self._get_sql(question, history)
        
        # 2. Safety Check
        if any(x in sql.upper() for x in ["DROP", "DELETE", "UPDATE", "INSERT", "ALTER"]):
            raise ValueError("Unsafe SQL detected.")

        # 3. Execute
        try:
            res = await self.db.execute(text(sql))
            data = [dict(r) for r in res.mappings().all()]
        except Exception as e:
            return {"answer": f"I couldn't calculate that. Error: {str(e)}", "data": [], "sql": sql}

        # 4. Narrative
        if not data:
            return {"answer": "No data found matching your query.", "data": [], "sql": sql}

        narrative_resp = await client.chat.completions.create(
            model=settings.AI_MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_NARRATIVE},
                {"role": "user", "content": f"Q: {question}\nData: {json.dumps(data)}"}
            ]
        )
        
        return {
            "answer": narrative_resp.choices[0].message.content,
            "data_points": data,
            "generated_sql": sql
        }