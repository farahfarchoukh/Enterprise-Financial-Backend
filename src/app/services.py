from sqlalchemy.ext.asyncio import AsyncSession
from src.infrastructure.parsers import ParserFactory
from src.domain.models import FinancialRecord

class IngestionService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def ingest(self, source: str, content: bytes):
        parser = ParserFactory.get_parser(source)
        dtos = parser.parse(content)
        
        records = [
            FinancialRecord(
                transaction_date=d.date,
                description=d.description,
                category=d.category,
                amount=d.amount,
                record_type=d.type,
                source=source,
                raw_metadata=d.raw_data
            ) for d in dtos
        ]
        
        self.db.add_all(records)
        await self.db.commit()
        return len(records)