from datetime import datetime
from db.session import base
from sqlalchemy import Boolean, Column, DateTime, Integer, String, ForeignKey, Text
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
    chat_messages = relationship("ChatMessage", back_populates="user")
    saved_chats = relationship("SavedChat", back_populates="user")
    faculty_submissions = relationship("FacultySubmission", back_populates="user")


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


class OTPRecord(base):
    __tablename__ = "otp_records"
    id         = Column(Integer, primary_key=True)
    email      = Column(String, index=True)
    otp_hash   = Column(String)          # store hash, not plain OTP
    expires_at = Column(DateTime)
    attempts   = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)

class ChatMessage(base):
    __tablename__ = 'chat_messages'

    id         = Column(Integer, primary_key=True, index=True)
    user_id    = Column(Integer, ForeignKey('user_auth.id'), nullable=False)
    role       = Column(String, nullable=False)   # 'user' or 'assistant'
    content    = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("UserAuth", back_populates="chat_messages")

class SavedChat(base):
    __tablename__ = 'saved_chats'

    id           = Column(Integer, primary_key=True, index=True)
    user_id      = Column(Integer, ForeignKey('user_auth.id'), nullable=False)
    query        = Column(String, nullable=False)
    response     = Column(String, nullable=False)
    saved_at     = Column(DateTime, default=datetime.utcnow)

    user = relationship("UserAuth", back_populates="saved_chats")

class Announcement(base):
    __tablename__ = 'announcements'

    id              = Column(Integer, primary_key=True, index=True)
    title           = Column(String, nullable=False)
    description     = Column(String, nullable=False)
    type            = Column(String, nullable=False, default='General')
    target_audience = Column(String, nullable=False, default='All')
    is_active       = Column(String, nullable=False, default='Yes')
    semester        = Column(String, nullable=False)
    created_at      = Column(DateTime, default=datetime.utcnow)

class UserNotification(base):
    __tablename__ = "user_notifications"

    id              = Column(Integer, primary_key=True, index=True)
    user_id         = Column(Integer, ForeignKey("user_auth.id", ondelete="CASCADE"))
    announcement_id = Column(Integer, ForeignKey("announcements.id", ondelete="CASCADE"))
    is_read         = Column(Boolean, default=False)
    created_at      = Column(DateTime, default=datetime.utcnow)

    announcement = relationship("Announcement")

class FacultySubmission(base):
    __tablename__ = "faculty_submissions"

    id            = Column(Integer, primary_key=True, index=True)
    user_id       = Column(Integer, ForeignKey("user_auth.id", ondelete="CASCADE"), nullable=False)  # ← add
    faculty_name  = Column(String(100), nullable=False)
    faculty_email = Column(String(100), nullable=False)
    topic         = Column(String(200), nullable=False)
    detail        = Column(Text,        nullable=False)
    tags          = Column(String(300))
    file_url      = Column(String(500))
    status        = Column(String(20),  default="Pending")
    admin_notes   = Column(Text)
    submitted_at  = Column(DateTime,    default=datetime.utcnow)
    reviewed_at   = Column(DateTime)

    user = relationship("UserAuth", back_populates="faculty_submissions")