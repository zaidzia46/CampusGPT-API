from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy import create_engine
from config import DATABASE_URL

engine = create_engine(
    DATABASE_URL,
    connect_args={"sslmode": "require"},
    pool_pre_ping=True,    # test connection before using it
    pool_recycle=300,
)
sessionlocal = sessionmaker(autoflush=False, autocommit=False, bind=engine)

base = declarative_base()

def get_db():
    db = sessionlocal()
    try:
        yield db
    finally:
        db.close()