from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import declarative_base, sessionmaker

from config import DATABASE_URL


engine_options = {
    "echo": False,
}

if DATABASE_URL.startswith("sqlite"):
    engine_options["connect_args"] = {"check_same_thread": False}

engine = create_engine(DATABASE_URL, **engine_options)

SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False
)

Base = declarative_base()


def add_column_if_missing(
    table_name: str,
    column_name: str,
    sql_definition: str
) -> None:
    inspector = inspect(engine)

    if table_name not in inspector.get_table_names():
        return

    columns = {
        column["name"]
        for column in inspector.get_columns(table_name)
    }

    if column_name in columns:
        return

    with engine.begin() as connection:
        connection.execute(
            text(
                f"ALTER TABLE {table_name} "
                f"ADD COLUMN {column_name} {sql_definition}"
            )
        )


def run_lightweight_migrations():
    if not DATABASE_URL.startswith("sqlite"):
        return

    add_column_if_missing(
        "users",
        "interface_message_id",
        "INTEGER"
    )
    add_column_if_missing(
        "tasks",
        "reminder_sent",
        "BOOLEAN NOT NULL DEFAULT 0"
    )
    add_column_if_missing(
        "tasks",
        "reminder_preset",
        "VARCHAR(30) NOT NULL DEFAULT 'default'"
    )
    add_column_if_missing(
        "tasks",
        "completed_at",
        "DATETIME"
    )
    add_column_if_missing(
        "tasks",
        "updated_at",
        "DATETIME"
    )


def init_db():
    # iмпорти потрібні щоб sqlalchemy зареєстрував моделі
    from models.reminder import Reminder  # noqa f401
    from models.task import Task  # noqa f401
    from models.user import User  # noqa f401

    Base.metadata.create_all(bind=engine)
    run_lightweight_migrations()
