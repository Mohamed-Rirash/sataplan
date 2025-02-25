from app.models import User


async def get_user(user_id, db):

    return db.query(User).filter(User.id == user_id).first()


async def get_user_pass_by_id(user_id, db):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return None
    return user.password
