from typing import Generic, TypeVar, Type, List, Optional, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, func
from app.models.base import BaseModel

ModelType = TypeVar("ModelType", bound=BaseModel)


class BaseRepository(Generic[ModelType]):
    """Generic async database repository providing encapsulated CRUD operations."""
    def __init__(self, model: Type[ModelType], db: AsyncSession):
        self.model = model
        self.db = db

    def _filter_model_attributes(self, attributes: dict) -> dict:
        """Filter attributes dictionary to only include valid SQLAlchemy model columns."""
        valid_keys = {col.key for col in self.model.__table__.columns}
        return {k: v for k, v in attributes.items() if k in valid_keys and v is not None}

    async def get_by_id(self, id: int, lock_for_update: bool = False) -> Optional[ModelType]:
        """Fetch a single record by primary key with optional pessimistic row locking."""
        query = select(self.model).where(self.model.id == id)
        if lock_for_update:
            query = query.with_for_update()
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def list_all(
        self,
        skip: int = 0,
        limit: int = 100,
        order_by_col: Optional[Any] = None
    ) -> List[ModelType]:
        """List records with limit-offset pagination."""
        query = select(self.model).offset(skip).limit(limit)
        if order_by_col is not None:
            query = query.order_by(order_by_col)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def create(self, attributes: dict) -> ModelType:
        """Create a single record from attributes dictionary."""
        filtered_attrs = self._filter_model_attributes(attributes)
        instance = self.model(**filtered_attrs)
        self.db.add(instance)
        await self.db.commit()
        await self.db.refresh(instance)
        return instance

    async def update(self, id: int, attributes: dict) -> Optional[ModelType]:
        """Update a single record by primary key."""
        instance = await self.get_by_id(id, lock_for_update=True)
        if not instance:
            return None
        filtered_attrs = self._filter_model_attributes(attributes)
        for key, value in filtered_attrs.items():
            if hasattr(instance, key):
                setattr(instance, key, value)
        await self.db.commit()
        await self.db.refresh(instance)
        return instance

    async def delete(self, id: int) -> bool:
        """Delete a single record by primary key."""
        instance = await self.get_by_id(id, lock_for_update=True)
        if not instance:
            return False
        await self.db.delete(instance)
        await self.db.commit()
        return True

    async def count(self) -> int:
        """Count total records."""
        result = await self.db.execute(select(func.count()).select_from(self.model))
        return result.scalar() or 0
