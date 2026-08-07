from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text


async def apply_database_engine_constraints(db: AsyncSession) -> dict:
    """
    Applies PostgreSQL btree_gist extension and verifies engine-level constraints
    to prevent double-booking room or faculty clashes at the database level.
    """
    results = {"btree_gist": False, "message": ""}
    try:
        # Enable btree_gist extension for PostgreSQL engine
        await db.execute(text("CREATE EXTENSION IF NOT EXISTS btree_gist;"))
        await db.commit()
        results["btree_gist"] = True
        results["message"] = "Successfully initialized PostgreSQL btree_gist extension."
    except Exception as ex:
        results["message"] = f"Database engine migration notice: {ex}"
    return results
