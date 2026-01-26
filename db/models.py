from sqlalchemy import Column, Integer, String, create_engine, ForeignKey, Text, Boolean
from sqlalchemy.orm import Mapped, sessionmaker, mapped_column, declarative_base, relationship

from db.database import Base

class Task_Manager(Base):
    __tablename__ = "taskmanager"

    call_id: Mapped[str] = mapped_column(String, primary_key=True, index=True)
    phone: Mapped[str] = mapped_column(String, nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)

    processed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    last_error: Mapped[str] = mapped_column(Text, nullable=True)


     # Audit trail FUTURE IMPLENTATION
    # created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    # processed_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)

    def __repr__(self):
        return f"<TaskManager(call_id={self.call_id}, phone={self.phone}, processed={self.processed})>"

