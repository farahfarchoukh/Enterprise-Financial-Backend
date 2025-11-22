import json
from abc import ABC, abstractmethod
from typing import List
from datetime import datetime
from src.domain.schemas import TransactionDTO

class ParserStrategy(ABC):
    @abstractmethod
    def parse(self, content: bytes) -> List[TransactionDTO]:
        pass

class QuickBooksParser(ParserStrategy):
    def parse(self, content: bytes) -> List[TransactionDTO]:
        data = json.loads(content)
        # Handle list vs dict wrapper
        items = data if isinstance(data, list) else data.get("data", [])
        
        results = []
        for i in items:
            # Flexible Key Matching
            i_low = {k.lower(): v for k, v in i.items()}
            
            # Logic: If type is expense, make amount negative
            amt = float(i_low.get("amount", 0))
            if "expense" in i_low.get("type", "").lower() and amt > 0:
                amt = -amt
                
            results.append(TransactionDTO(
                date=datetime.strptime(i_low.get("date", "2024-01-01"), "%Y-%m-%d").date(),
                description=i_low.get("description", ""),
                amount=amt,
                category=i_low.get("category", "Uncategorized"),
                type=i_low.get("type", "Unknown"),
                raw_data=json.dumps(i)
            ))
        return results

class RootfiParser(ParserStrategy):
    def parse(self, content: bytes) -> List[TransactionDTO]:
        data = json.loads(content)
        txs = data.get("transactions", [])
        results = []
        for t in txs:
            results.append(TransactionDTO(
                date=datetime.strptime(t["timestamp"], "%Y-%m-%d").date(),
                description=t.get("memo", ""),
                amount=float(t.get("value", 0)),
                category=t.get("account", "Uncategorized"),
                type="Unknown", # Rootfi implies type via account usually
                raw_data=json.dumps(t)
            ))
        return results

class ParserFactory:
    @staticmethod
    def get_parser(source: str) -> ParserStrategy:
        if source.lower() == "quickbooks": return QuickBooksParser()
        if source.lower() == "rootfi": return RootfiParser()
        raise ValueError("Unknown source")