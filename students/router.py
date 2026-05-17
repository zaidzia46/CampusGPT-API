from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from db.session import get_db
from schemas.students.saved_chat import SaveChatRequest
from students.deps import get_current_student
from schemas.students.feedback import Feedback_pd
from schemas.students.query import Query
from schemas.students.query_feedback import QueryFeedback_pd
from schemas.students.update_pwd import UpdatePassword
from models.models import ChatMessage, Feedback, QueryFeedback, SavedChat, UserAuth, UserNotification
from core.security import verify_password, password_hashing
from rag_pipeline.searcher import search
from rag_pipeline.llm import get_answer, rewrite_query
from students.manage_msg import manage_messages


router = APIRouter(
    prefix='/student',
    tags=['Student'],
    dependencies=[Depends(get_current_student)]
)

@router.post('/query')
def UserQuery(
    query:   Query,
    db:      Session = Depends(get_db),
    current_student: dict = Depends(get_current_student),
):
    user_id=current_student['user_id']

    manage_messages(user_id, db)
    recent = db.query(ChatMessage).filter(
        ChatMessage.user_id == user_id
    ).order_by(ChatMessage.created_at.desc()).limit(6).all()

    history = [{"role": m.role, "content": m.content}
               for m in reversed(recent)]

    search_query = rewrite_query(query.query_text, history)

    search_result = search(search_query, top_k=3)
    chunks = search_result.get("results", [])

    llm_result = get_answer(search_query, chunks, history)

    db.add(ChatMessage(user_id=user_id, role="user",
                       content=search_query))
    db.add(ChatMessage(user_id=user_id, role="assistant",
                       content=llm_result["answer"]))
    db.commit()

    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "response":       llm_result["answer"],
            "query":          query.query_text,
            "search_query":   search_query,
            "success":        llm_result["success"],
            "model":          llm_result["model"],
        }
    )

@router.delete('/clear-history')
def ClearHistory(
    db:      Session = Depends(get_db),
    current_student: dict    = Depends(get_current_student),
):
    db.query(ChatMessage).filter(
        ChatMessage.user_id == current_student['user_id']
    ).delete()
    db.commit()
    return {"message": "History cleared"}


@router.post('/saved-chats')
def SaveChat(
    body:    SaveChatRequest,
    db:      Session = Depends(get_db),
    current: dict    = Depends(get_current_student),
):
    saved = SavedChat(
        user_id  = current['user_id'],
        query    = body.query,
        response = body.response,
    )
    db.add(saved)
    db.commit()
    db.refresh(saved)
    return {
        "message":  "Chat saved successfully",
        "saved_id": saved.id,
    }


# Get all saved chats
@router.get('/saved-chats')
def GetSavedChats(
    db:      Session = Depends(get_db),
    current: dict    = Depends(get_current_student),
):
    chats = db.query(SavedChat).filter(
        SavedChat.user_id == current['user_id']
    ).order_by(SavedChat.saved_at.desc()).all()

    return [{
        "id":       c.id,
        "query":    c.query,
        "response": c.response,
        "saved_at": c.saved_at.isoformat(),
    } for c in chats]


# Unsave/delete a saved chat
@router.delete('/saved-chats/{chat_id}')
def UnsaveChat(
    chat_id: int,
    db:      Session = Depends(get_db),
    current: dict    = Depends(get_current_student),
):
    chat = db.query(SavedChat).filter(
        SavedChat.id      == chat_id,
        SavedChat.user_id == current['user_id'],
    ).first()

    if not chat:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"error": "Saved chat not found"}
        )

    db.delete(chat)
    db.commit()
    return {"message": "Chat unsaved successfully"}


# Check if a specific chat is saved
@router.get('/saved-chats/check')
def CheckSaved(
    query:   str,
    db:      Session = Depends(get_db),
    current: dict    = Depends(get_current_student),
):
    chat = db.query(SavedChat).filter(
        SavedChat.user_id == current['user_id'],
        SavedChat.query   == query,
    ).first()

    return {"is_saved": chat is not None, "saved_id": chat.id if chat else None}


@router.post('/query-feedback')
def UserQueryFeedback(queryFeedback: QueryFeedback_pd, current_student = Depends(get_current_student), db = Depends(get_db)):

    if queryFeedback.detail != '':
        new_query_feedback = QueryFeedback(query=queryFeedback.query, llmresponse=queryFeedback.llmresponse, reason=queryFeedback.reason, detail=queryFeedback.detail, user_id=current_student['user_id'])
    else:
        new_query_feedback = QueryFeedback(query=queryFeedback.query, llmresponse=queryFeedback.llmresponse, reason=queryFeedback.reason, detail='nill', user_id=current_student['user_id'])

    db.add(new_query_feedback)
    db.commit()
    db.refresh(new_query_feedback)

    return JSONResponse(status_code=status.HTTP_200_OK, content={'message': 'success'})

@router.post('/feedback')
def UserFeedback(feedback: Feedback_pd, current_student = Depends(get_current_student), db = Depends(get_db)):
    user = current_student
    user_id = user['user_id']
    if feedback.feedback == '':
        new_feedback = Feedback(feedback='NILL', ratings=feedback.rating, user_id=user_id)
    else:
        new_feedback = Feedback(feedback=feedback.feedback, ratings=feedback.rating, user_id=user_id)
    db.add(new_feedback)
    db.commit()
    db.refresh(new_feedback)
    return {'message': 'success'}

@router.post('/update-password')
def UpdatePassword(update_password: UpdatePassword, current_student = Depends(get_current_student), db = Depends(get_db)):
    user = current_student
    user_id = user['user_id']
    existing_user = db.query(UserAuth).filter(UserAuth.id == user_id).first()
    if not existing_user:
        return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content={'message': 'User not found'})
    if not verify_password(update_password.old_password, existing_user.password):
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content={'message': 'Incorrect old password'})
    if update_password.new_password != update_password.confirm_password:
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content={'message': 'New passwords do not match'})
    existing_user.password = password_hashing(update_password.new_password)
    db.commit()
    return JSONResponse(status_code=status.HTTP_200_OK, content={'message': 'Password updated successfully'})

@router.get("/notifications")
def get_notifications(db: Session = Depends(get_db), 
                      current_student: dict = Depends(get_current_student)):
    """Get all notifications for the logged-in student."""
    notifications = (
        db.query(UserNotification)
        .filter(UserNotification.user_id == current_student["user_id"])
        .order_by(UserNotification.created_at.desc())
        .all()
    )

    return [
        {
            "id":          n.id,
            "is_read":     n.is_read,
            "created_at":  n.created_at.isoformat(),
            "announcement": {
                "id":              n.announcement.id,
                "title":           n.announcement.title,
                "description":     n.announcement.description,
                "type":            n.announcement.type,
                "target_audience": n.announcement.target_audience,
                "is_active":       n.announcement.is_active,
                "semester":        n.announcement.semester,
            }
        }
        for n in notifications
    ]


@router.get("/notifications/unread-count")
def unread_count(db: Session = Depends(get_db),
                 current_student: dict = Depends(get_current_student)):
    """Returns unread notification count — for the badge."""
    count = (
        db.query(UserNotification)
        .filter(
            UserNotification.user_id == current_student["user_id"],
            UserNotification.is_read == False
        )
        .count()
    )
    return {"unread_count": count}


@router.patch("/notifications/{notification_id}/read")
def mark_as_read(notification_id: int,
                 db: Session = Depends(get_db),
                 current_student: dict = Depends(get_current_student)):
    """Mark a single notification as read."""
    n = db.query(UserNotification).filter(
        UserNotification.id      == notification_id,
        UserNotification.user_id == current_student["user_id"]
    ).first()

    if n:
        n.is_read = True
        db.commit()

    return {"message": "Marked as read"}


@router.patch("/notifications/mark-all-read")
def mark_all_read(db: Session = Depends(get_db),
                  current_student: dict = Depends(get_current_student)):
    """Mark all notifications as read at once."""
    db.query(UserNotification).filter(
        UserNotification.user_id == current_student["user_id"],
        UserNotification.is_read == False
    ).update({"is_read": True})
    db.commit()
    return {"message": "All notifications marked as read"}
