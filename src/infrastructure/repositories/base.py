from typing import Generic, TypeVar, Type, Optional, List, Union
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.infrastructure.database import Base

ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):
    def __init__(self, model: Type[ModelType], session: AsyncSession):
        self.model = model
        self.session = session

    async def get(self, id: Union[int, str]) -> Optional[ModelType]:
        query = select(self.model).where(self.model.id == id)  # type: ignore
        result = await self.session.execute(query)
        return result.scalars().first()

    async def get_all(self) -> List[ModelType]:
        query = select(self.model)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def create(self, **kwargs) -> ModelType:
        instance = self.model(**kwargs)
        self.session.add(instance)
        await self.session.commit()
        await self.session.refresh(instance)
        return instance

    async def update(self, id: Union[int, str], **kwargs) -> Optional[ModelType]:
        instance = await self.get(id)
        if instance:
            for key, value in kwargs.items():
                setattr(instance, key, value)
            await self.session.commit()
            await self.session.refresh(instance)
        return instance

    async def delete(self, id: Union[int, str]) -> bool:
        instance = await self.get(id)
        if instance:
            await self.session.delete(instance)
            await self.session.commit()
            return True
        return False

    async def get_one_by_filter(self, *filters) -> Optional[ModelType]:
        query = select(self.model).where(*filters)
        result = await self.session.execute(query)
        return result.scalars().first()

    async def get_by_filter(self, *filters) -> List[ModelType]:
        query = select(self.model).where(*filters)
        result = await self.session.execute(query)
        return list(result.scalars().all())
