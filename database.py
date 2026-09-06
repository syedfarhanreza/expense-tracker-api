import os

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.pool import StaticPool


SQLALCHEMY_DATABASE_URL = os.getenv(
	"DATABASE_URL",
	"postgresql://postgres.rppafrfrtloiblkcpqts:Farhanreza79726858@aws-0-ap-southeast-1.pooler.supabase.com:5432/postgres",
)

engine_options = {}
if SQLALCHEMY_DATABASE_URL.startswith("sqlite"):
	engine_options = {
		"connect_args": {"check_same_thread": False},
	}
	if SQLALCHEMY_DATABASE_URL == "sqlite://":
		engine_options["poolclass"] = StaticPool

engine = create_engine(SQLALCHEMY_DATABASE_URL, **engine_options)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()
