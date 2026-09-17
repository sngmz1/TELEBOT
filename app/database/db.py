from app.config import DATABASE_URL
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import String, Integer, DateTime, func, text
from datetime import datetime

engine = create_async_engine(DATABASE_URL, echo=False)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    telegram_id: Mapped[int] = mapped_column(Integer, unique=True, nullable=False)
    username: Mapped[str | None] = mapped_column(String, nullable=True)
    full_name: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class Order(Base):
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    order_id: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    user_id: Mapped[int] = mapped_column(Integer, nullable=False)
    username: Mapped[str | None] = mapped_column(String, nullable=True)
    user_name: Mapped[str] = mapped_column(String, nullable=False, default="")
    service: Mapped[str] = mapped_column(String, nullable=False)
    package: Mapped[str] = mapped_column(String, nullable=False)
    amount: Mapped[str] = mapped_column(String, nullable=False)
    info: Mapped[str] = mapped_column(String, nullable=False, default="")
    status: Mapped[str] = mapped_column(String, default="PENDING_PAYMENT")
    payment_status: Mapped[str] = mapped_column(String, default="PENDING")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())


class OrderInformation(Base):
    __tablename__ = "order_information"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    order_id: Mapped[str] = mapped_column(String, nullable=False)
    information_type: Mapped[str] = mapped_column(String, nullable=False)
    information_value: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


OLD_STATUS_MAP = {
    "pending": ("PENDING_PAYMENT", "PENDING"),
    "paid": ("PAYMENT_VERIFICATION", "VERIFIED"),
    "processing": ("PROCESSING", "VERIFIED"),
    "completed": ("COMPLETED", "VERIFIED"),
    "cancelled": ("CANCELLED", "PENDING"),
    "rejected": ("CANCELLED", "REJECTED"),
}


async def _column_names(conn, table: str) -> set[str]:
    result = await conn.execute(text(f"PRAGMA table_info({table})"))
    rows = result.fetchall()
    return {row[1] for row in rows}


async def _migrate_orders(conn) -> None:
    cols = await _column_names(conn, "orders")
    additions = []
    if "username" not in cols:
        additions.append("ALTER TABLE orders ADD COLUMN username VARCHAR DEFAULT ''")
    if "user_name" not in cols:
        additions.append("ALTER TABLE orders ADD COLUMN user_name VARCHAR DEFAULT ''")
    if "payment_status" not in cols:
        additions.append("ALTER TABLE orders ADD COLUMN payment_status VARCHAR DEFAULT 'PENDING'")
    if "updated_at" not in cols:
        additions.append("ALTER TABLE orders ADD COLUMN updated_at DATETIME")
    for stmt in additions:
        await conn.execute(text(stmt))
    await conn.execute(text("UPDATE orders SET updated_at = created_at WHERE updated_at IS NULL"))

    # migrate old status values to the new enum values
    for old, (new_status, new_payment) in OLD_STATUS_MAP.items():
        await conn.execute(text(
            "UPDATE orders SET status = :ns, payment_status = :np WHERE status = :os"
        ), {"ns": new_status, "np": new_payment, "os": old})

    # fill usernames for legacy orders from the users table
    await conn.execute(text(
        "UPDATE orders SET username = COALESCE((SELECT username FROM users WHERE users.telegram_id = orders.user_id), '')"
    ))
    await conn.execute(text(
        "UPDATE orders SET user_name = COALESCE((SELECT full_name FROM users WHERE users.telegram_id = orders.user_id), '')"
    ))

    # prevent NULLs in the legacy NOT NULL info column
    await conn.execute(text("UPDATE orders SET info = '' WHERE info IS NULL"))
    if "info" in cols:
        result = await conn.execute(text(
            "SELECT order_id, info FROM orders WHERE info IS NOT NULL AND info != ''"
        ))
        legacy = result.fetchall()
        for oid, info in legacy:
            existing = await conn.execute(text(
                "SELECT COUNT(*) FROM order_information WHERE order_id = :oid"
            ), {"oid": oid})
            count = existing.scalar_one()
            if count == 0 and info and info.lower() != "n/a":
                await conn.execute(text(
                    "INSERT INTO order_information (order_id, information_type, information_value) VALUES (:oid, 'Info', :info)"
                ), {"oid": oid, "info": info})


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        await _migrate_orders(conn)