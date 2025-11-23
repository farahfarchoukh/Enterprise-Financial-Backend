import json
import os
from openai import AsyncOpenAI
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from src.config import get_settings
from typing import List, Dict

settings = get_settings()

SYSTEM_SQL = """
You are an Elite Financial Data Architect. 
Your goal is to convert natural language into precise SQLite queries.

SCHEMA:
- Table: financial_records
- Columns: transaction_date (Date), description, category, amount (Float), source.

RULES:
1. PROFIT = SUM(amount)
2. REVENUE = SUM(amount) WHERE amount > 0
3. EXPENSES = SUM(amount) WHERE amount < 0
4. MARGIN = (Profit / Revenue) * 100
5. Group by month: strftime('%Y-%m', transaction_date)
6. Output raw SQL only.
"""

SYSTEM_NARRATIVE = """
You are a CFO. Interpret the database results provided.
1. Context: Are the numbers good or bad?
2. Trends: Mention growth.
3. Tone: Professional, data-driven.
"""

class FinancialAgent:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.openai_client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        
        # FIX: Use Pydantic settings
        self.groq_api_key = settings.GROQ_API_KEY 
        
        self.groq_client = AsyncOpenAI(
            base_url="https://api.groq.com/openai/v1",
            api_key=self.groq_api_key
        )

        # PRIORITY LIST: Try these in order. Stops guessing games.
        self.groq_models = [
            "llama-3.3-70b-versatile",  # Flagship
            "llama-3.1-70b-versatile",  # Backup High-End
            "llama-3.1-8b-instant",     # Ultra-Fast/Stable (The "Cockroach" model)
            "gemma2-9b-it"              # Google Backup
        ]

    async def _call_groq_fallback(self, messages: List[Dict], temperature: float):
        """Iterate through models until one works"""
        last_error = None
        for model in self.groq_models:
            try:
                print(f" Attempting Groq Model: {model}...")
                response = await self.groq_client.chat.completions.create(
                    model=model,
                    messages=messages,
                    temperature=temperature
                )
                print(f" Success with {model}")
                return response.choices[0].message.content
            except Exception as e:
                print(f" Failed {model}: {e}")
                last_error = e
                continue # Try next model
        
        raise last_error # All failed

    async def _call_llm(self, messages: List[Dict], temperature: float = 0):
        # 1. Try OpenAI
        try:
            response = await self.openai_client.chat.completions.create(
                model=settings.AI_MODEL,
                messages=messages,
                temperature=temperature
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"⚠️ Primary AI (OpenAI) Failed: {e}")
            
            # 2. Try Groq Loop
            if self.groq_api_key and len(self.groq_api_key) > 5:
                try:
                    return await self._call_groq_fallback(messages, temperature)
                except Exception as groq_e:
                    print(f" All Groq Models Failed.")
                    raise groq_e
            else:
                raise e

    async def run(self, question: str, history: List[Dict]):
        try:
            # 1. Generate SQL
            sql_messages = [{"role": "system", "content": SYSTEM_SQL}]
            for msg in history[-2:]: 
                sql_messages.append({"role": msg["role"], "content": msg["content"]})
            sql_messages.append({"role": "user", "content": question})

            raw_sql = await self._call_llm(sql_messages, temperature=0)
            sql = raw_sql.replace("```sql", "").replace("```", "").strip()
            
            # 2. Guardrails
            if any(x in sql.upper() for x in ["DROP", "DELETE", "UPDATE", "INSERT", "ALTER"]):
                raise ValueError("Security Violation: Unsafe SQL detected.")

            # 3. Execute
            try:
                result = await self.db.execute(text(sql))
                data = [dict(row) for row in result.mappings().all()]
            except Exception as db_err:
                return {"answer": "Database query failed.", "data_points": [], "generated_sql": sql}

            # 4. Narrative
            if not data:
                return {"answer": "No records found.", "data_points": [], "generated_sql": sql}

            insight_messages = [
                {"role": "system", "content": SYSTEM_NARRATIVE},
                {"role": "user", "content": f"Q: {question}\nData: {json.dumps(data)}"}
            ]
            narrative = await self._call_llm(insight_messages, temperature=0.5)

            return {
                "answer": narrative,
                "data_points": data,
                "generated_sql": sql
            }

        except Exception as e:
            print(f" ALL SYSTEMS FAILURE: {e}")
            return {
                "answer": "[DEMO MODE] AI Providers unavailable (Billing/Model Rot). Logic Intact.",
                "data_points": [{"mock_revenue": 50000}],
                "generated_sql": "SELECT SUM(amount) -- Mock"
            }