from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    String,
    BigInteger,
)
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class User(Base):
    __tablename__ = "users"

    tg_id = Column(BigInteger, unique=True, primary_key=True)
    fullname = Column(String(130))
    username = Column(String(35))
    first_start = Column(DateTime(True))
    is_admin = Column(Boolean(False))
    is_blocked = Column(Boolean(False))

    def __init__(
        self,
        tg_id: int,
        fullname: str,
        username: str,
        first_start,
        is_admin: bool,
        is_blocked: bool,
    ) -> None:
        self.tg_id = tg_id
        self.fullname = fullname
        self.username = username
        self.first_start = first_start
        self.is_admin = is_admin
        self.is_blocked = is_blocked

    def __repr__(self) -> str:
        return (
            f"<User(id={self.tg_id!r}, "
            f"username={self.username!r}, "
            f"first_start={self.first_start!r}, "
            f"is_admin={self.is_admin!r}, "
            f"is_blocked={self.is_blocked!r})>"
        )
