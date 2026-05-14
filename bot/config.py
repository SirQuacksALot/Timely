import os
from dotenv import load_dotenv

load_dotenv()

DISCORD_TOKEN: str = os.environ["DISCORD_TOKEN"]
DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///timely.db")
