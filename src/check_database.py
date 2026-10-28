from sqlalchemy import inspect

from src.database import engine

inspector = inspect(engine)

print("Tables in database:")

for table_name in inspector.get_table_names():
    print("-", table_name)