# import os
# from typing import Generator

# from sqlalchemy import create_engine, text
# from sqlalchemy.orm import declarative_base, sessionmaker

# DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./inventory.db")

# connect_args = {}
# if DATABASE_URL.startswith("sqlite"):
#     connect_args = {"check_same_thread": False}

# engine = create_engine(DATABASE_URL, connect_args=connect_args)

# print("DATABASE_URL =", engine.url)

# with engine.connect() as conn:
#     print("Current DB:", conn.execute(text("SELECT current_database()")).scalar())
#     print("Current User:", conn.execute(text("SELECT current_user")).scalar())
    
# SessionLocal = sessionmaker(autocommit=False, autoflush=False, expire_on_commit=False, bind=engine)

# Base = declarative_base()


# def get_db() -> Generator:
#     db = SessionLocal()
#     try:
#         yield db
#     finally:
#         db.close()

import os
from typing import Generator

from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import declarative_base, sessionmaker

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./inventory.db")

connect_args = {}
if DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

engine = create_engine(DATABASE_URL, connect_args=connect_args)

print("DATABASE_URL =", engine.url)

if DATABASE_URL.startswith("sqlite"):
    print("SQLite database is active")
else:
    with engine.connect() as conn:
        print("Current DB:", conn.execute(text("SELECT current_database()")).scalar())
        print("Current User:", conn.execute(text("SELECT current_user")).scalar())

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
    bind=engine,
)

Base = declarative_base()


def get_db() -> Generator:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()