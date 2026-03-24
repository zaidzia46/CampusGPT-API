from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from db.session import get_db
from students.deps import get_current_student
from schemas.students.feedback import Feedback_pd
from schemas.students.query import Query
from schemas.students.query_feedback import QueryFeedback_pd
from schemas.students.update_pwd import UpdatePassword
from models.models import Feedback, QueryFeedback, UserAuth
from core.security import verify_password, password_hashing


router = APIRouter(
    prefix='/student',
    tags=['Student'],
    dependencies=[Depends(get_current_student)]
)

@router.post('/query')
def UserQuery(query: Query):
    #give to RAG pipeline
    #return response to user
    return JSONResponse(status_code=status.HTTP_200_OK, content={'response':'LLM Response for the query', 'query':query.query_text})

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