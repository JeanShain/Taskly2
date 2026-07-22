from typing import Optional

from sqlalchemy.orm import Session

from models.user import User


def get_user_by_telegram_id(
    db: Session,
    telegram_id: int
) -> Optional[User]:
    return (
        db.query(User)
        .filter(User.telegram_id == telegram_id)
        .first()
    )


def create_user(
    db: Session,
    telegram_id: int,
    username: Optional[str] = None,
    first_name: Optional[str] = None
) -> User:
    user = User(
        telegram_id=telegram_id,
        username=username,
        first_name=first_name
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return user


def get_or_create_user(
    db: Session,
    telegram_id: int,
    username: Optional[str] = None,
    first_name: Optional[str] = None
) -> User:
    user = get_user_by_telegram_id(db, telegram_id)

    if user is None:
        return create_user(
            db=db,
            telegram_id=telegram_id,
            username=username,
            first_name=first_name
        )

    changed = False

    if user.username != username:
        user.username = username
        changed = True

    if user.first_name != first_name:
        user.first_name = first_name
        changed = True

    if changed:
        db.commit()
        db.refresh(user)

    return user


def set_interface_message_id(
    db: Session,
    telegram_id: int,
    message_id: int
) -> None:
    user = get_user_by_telegram_id(db, telegram_id)

    if user is None:
        return

    user.interface_message_id = message_id
    db.commit()


def get_interface_message_id(
    db: Session,
    telegram_id: int
) -> Optional[int]:
    user = get_user_by_telegram_id(db, telegram_id)

    if user is None:
        return None

    return user.interface_message_id
