from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import String, Float, Date, Text, Index
from datetime import date

class Base(DeclarativeBase):
    pass

class FinancialRecord(Base):
    __tablename__ = "financial_records"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    transaction_date: Mapped[date] = mapped_column(Date)
    description: Mapped[str] = mapped_column(String)
    category: Mapped[str] = mapped_column(String, index=True)
    amount: Mapped[float] = mapped_column(Float) # Signed (+Rev, -Exp)
    record_type: Mapped[str] = mapped_column(String) # 'Revenue', 'Expense'
    source: Mapped[str] = mapped_column(String) 
    raw_metadata: Mapped[str] = mapped_column(Text)

    __table_args__ = (Index('idx_date_cat', 'transaction_date', 'category'),)