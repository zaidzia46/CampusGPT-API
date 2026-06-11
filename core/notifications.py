from sqlalchemy.orm import Session
from models.models import UserNotification, UserAuth

def notify_all_users(db: Session, announcement_id: int):
    """Insert a notification row for every user when announcement is created."""
    users = db.query(UserAuth).filter(
    UserAuth.role.in_(["student", "faculty"])
    ).all()

    if not users:
        return 0
    
    notifications = [
        UserNotification(
            user_id         = user.id,
            announcement_id = announcement_id,
        )
        for user in users
    ]
    
    db.bulk_save_objects(notifications)
    db.commit()
    return len(notifications)
