from db.session import base
from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship

class UserAuth(base):
    __tablename__ = 'user_auth'
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, nullable=False)
    email = Column(String, nullable=False, unique=True)
    password = Column(String, nullable=False)
    role = Column(String, nullable=False, default='student')

    feedbacks = relationship("Feedback", back_populates="user")
    queryfeedbacks = relationship("QueryFeedback", back_populates="userqueryfeedback")

class Feedback(base):
    __tablename__ = 'feedback'

    feedback_id = Column(Integer, primary_key=True, index=True)
    feedback = Column(String, nullable=False)
    ratings = Column(Integer, nullable=False)
    user_id = Column(Integer, ForeignKey('user_auth.id'), nullable=False)

    user = relationship("UserAuth", back_populates="feedbacks")

class QueryFeedback(base):
    __tablename__ = 'query_feedback'

    id = Column(Integer, primary_key=True, index=True)
    query = Column(String, nullable=False)
    llmresponse = Column(String, nullable=False)
    reason = Column(String, nullable=False)
    detail = Column(String)
    user_id = Column(Integer, ForeignKey('user_auth.id'), nullable=False)

    userqueryfeedback = relationship("UserAuth", back_populates="queryfeedbacks")