"""Run Alembic upgrades outside the app process."""

import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from src.core.database import Base
from src.core.config import settings

# Import all models to ensure they are registered with Base.metadata
from src.models import *

async def main():
    print(f"Connecting to {settings.DATABASE_URL}...")
    engine = create_async_engine(settings.DATABASE_URL)
    async with engine.begin() as conn:
        print("Creating tables...")
        await conn.run_sync(Base.metadata.create_all)
    print("Done!")

if __name__ == "__main__":
    asyncio.run(main())
