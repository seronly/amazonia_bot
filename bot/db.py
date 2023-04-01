from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from models import Base, User
import datetime
import custom_logging as cl

import os
import dotenv

dotenv.load_dotenv()

logger = cl.logger

db_name = os.getenv("DB_NAME")
db_user = os.getenv("DB_USER")
db_pass = os.getenv("DB_PASS")

engine = create_engine(
    f"mysql+pymysql://{db_user}:" f"{db_pass}@" f"localhost/{db_name}",
    echo=False,
    pool_recycle=1800,
    pool_pre_ping=True,
)

Base.metadata.create_all(engine)
Session = scoped_session(sessionmaker(engine))


# User
def create_or_update_user(tg_user) -> None:
    """Create or update user

    Args:
        tg_user (User): Effective_user or from_user
    """
    session = Session()

    try:
        user = get_user(tg_user.id)
        is_admin = str(tg_user.id) in os.getenv("ADMIN_IDS").split(", ")

        if not user:
            user_db = User(
                tg_id=tg_user.id,
                fullname=tg_user.full_name,
                username=tg_user.username,
                first_start=datetime.datetime.now(),
                is_admin=is_admin,
                is_blocked=False,
            )
            logger.info(f"Added user {user_db}")
            session.add(user_db)
        else:
            update_user(
                user.tg_id,
                {
                    "fullname": tg_user.full_name,
                    "username": tg_user.username,
                    "is_admin": is_admin,
                    "is_blocked": False,
                },
            )
    except:
        session.rollback()
    finally:
        session.commit()


def get_user(user_id: int) -> User | None:
    """Get user from db

    Args:
        user_id (int)

    Returns:
        User | None: Return User or None if the result doesn't contain any row.
    """
    session: scoped_session = Session()
    try:
        user = session.query(User).get({"tg_id": user_id})
    except:
        session.rollback()
    finally:
        session.commit()
    return user


def update_user(user_id: int, values: dict) -> None:
    """Update `values` of user with `user_id`

    Args:
        user_id (int)
        values (dict)
    """
    session: scoped_session = Session()
    session.query(User).filter_by(tg_id=user_id).update(values)
    session.commit()


def get_all_users(inlcude_admin: bool = True) -> list[User]:
    session = Session()
    if inlcude_admin:
        return session.query(User).all()
    else:
        return session.query(User).filter_by(is_admin=False).all()


def get_all_users_wtih_block_status(
    blocked: bool, inlcude_admin: bool = True
) -> list[User]:
    session = Session()
    if inlcude_admin:
        result = session.query(User).filter_by(is_blocked=blocked).all()
    else:
        result = (
            session.query(User)
            .filter_by(is_admin=False, is_blocked=blocked)
            .all()
        )
    return result


def get_blocked_user_count() -> int:
    """Get number of users who block bot

    Returns:
        int: number of users
    """
    session = Session()
    result = session.query(User).filter(User.is_blocked).all()
    return len(result)


def is_admin(user) -> bool:
    return get_user(user.id).is_admin
