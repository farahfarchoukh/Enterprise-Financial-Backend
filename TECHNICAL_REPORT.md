# Kudwa Project - Technical Architecture Report

## 1. Architectural Philosophy
We employed **Clean Architecture** (Hexagonal) to ensure separation of concerns.
- **Domain Layer**: Contains Pydantic models and Database entities. Pure Python, no business logic.
- **Infrastructure Layer**: Handles external "dirty" details (OpenAI API, Database Drivers, File Parsers).
- **Application Layer**: Orchestrates data flow. The "Brain" of the operation.
- **Interfaces Layer**: The REST API endpoints.

## 2. Capability: Text-to-SQL (The "Why")
Standard RAG (Retrieval Augmented Generation) fails at math. If you ask an LLM to "Sum the revenue," it often hallucinates numbers.
**Our Solution:** We use a Text-to-SQL agent.
1. User asks natural language question.
2. AI translates this to a precise SQL query.
3. Database executes the math (100% accuracy).
4. AI interprets the result into a business narrative.

## 3. Data Integration Strategy
We utilized the **Strategy Pattern** for ingestors. This adheres to the Open-Closed Principle. To add "Xero" support, we simply add `XeroParser` class without modifying the existing ingestion engine.

## 4. Security
- **Authentication**: API Key middleware protects expensive AI endpoints.
- **Guardrails**: The SQL generation engine has a blocklist for `DROP` and `DELETE` commands.