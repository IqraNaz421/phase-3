"""Script to test the database connection."""
import asyncio
import os
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import create_async_engine

# Load environment variables from .env file
load_dotenv()

# Get database URL from environment variable
DATABASE_URL = os.getenv("DATABASE_URL")
print(f"Attempting to connect to: {DATABASE_URL}")

async def test_db_connection():
    """Test the database connection."""
    try:
        # Create async engine for Neon PostgreSQL
        async_engine = create_async_engine(
            DATABASE_URL,
            echo=True,  # Set to False in production
            pool_pre_ping=True,  # Verify connections before use
            pool_size=5,  # Base number of connections
            max_overflow=10,  # Max additional connections beyond pool_size
            pool_recycle=300,  # Recycle connections after 5 minutes
        )

        # Test the connection
        async with async_engine.begin() as conn:
            # Execute a simple query to test the connection
            from sqlalchemy import text
            result = await conn.execute(text("SELECT 1"))
            print("Database connection successful!")
            print("Connection test result:", result.fetchone())

        # Close the engine
        await async_engine.dispose()

    except Exception as e:
        print(f"Database connection failed: {e}")
        return False

    return True

if __name__ == "__main__":
    success = asyncio.run(test_db_connection())
    if success:
        print("\nDatabase connection test passed!")
    else:
        print("\nDatabase connection test failed!")