from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Table
from sqlalchemy.orm import relationship

from app.database import Base

# 할 일과 태그는 다대다 관계입니다.
task_tags = Table(
    "task_tags",
    Base.metadata,
    Column("task_id", ForeignKey("tasks.id"), primary_key=True),
    Column("tag_id", ForeignKey("tags.id"), primary_key=True),
)


class Tag(Base):
    __tablename__ = "tags"

    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)


class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True)
    title = Column(String, nullable=False)
    done = Column(Boolean, default=False, nullable=False)
    created_at = Column(
        DateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )

    # 다대다 태그는 모델 기본값으로 즉시 로딩합니다(N+1 방지).
    # selectin은 별도 IN 쿼리 1회로 태그를 모아오므로 joinedload처럼
    # 태그 개수만큼 행이 중복되지 않습니다.
    tags = relationship("Tag", secondary=task_tags, lazy="selectin")
