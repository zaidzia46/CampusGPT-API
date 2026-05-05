from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session
from models.models import ChatMessage


def manage_messages(user_id: int, db: Session):
    last_message = db.query(ChatMessage).filter(
        ChatMessage.user_id == user_id
    ).order_by(ChatMessage.created_at.desc()).first()

    if not last_message:
        return

    # Make both datetimes naive for safe comparison
    last_time = last_message.created_at
    if last_time.tzinfo is not None:
        last_time = last_time.astimezone(timezone.utc).replace(tzinfo=None)

    cutoff = datetime.utcnow() - timedelta(minutes=40)

    if last_time < cutoff:
        db.query(ChatMessage).filter(
            ChatMessage.user_id == user_id
        ).delete()
        db.commit()
        print(f"[CHAT] Session expired — cleared messages for user {user_id}")
    else:
        all_messages = db.query(ChatMessage).filter(
            ChatMessage.user_id == user_id
        ).order_by(ChatMessage.created_at.desc()).all()

        if len(all_messages) > 6:
            for msg in all_messages[6:]:
                db.delete(msg)
            db.commit()
            print(f"[CHAT] Trimmed to 6 messages for user {user_id}")