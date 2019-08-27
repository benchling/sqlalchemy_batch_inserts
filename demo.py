#!/usr/bin/env python3

from contextlib import contextmanager
import os
import sys
import time

from sqlalchemy import create_engine, Column, ForeignKey, Integer, String
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy.ext.declarative import declarative_base

from sqlalchemy_batch_inserts import enable_batch_inserting

Base = declarative_base()

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True)

    def __repr__(self):
       return "<User(name=%r)>" % (self.name)

class Address(Base):
    __tablename__ = "addresses"
    id = Column(Integer, primary_key=True)
    email_address = Column(String, nullable=False, unique=True)
    user_id = Column(Integer, ForeignKey("users.id"))

    user = relationship("User")

    def __repr__(self):
        return "<Address(email_address=%r)>" % self.email_address


def main():
    if len(sys.argv) != 3:
        usage_and_exit()
    if sys.argv[1] == 'yes':
        batch = True
    elif sys.argv[1] == 'no':
        batch = False
    else:
        usage_and_exit()
    try:
        count = int(sys.argv[2])
    except ValueError:
        usage_and_exit()

    engine = create_engine("postgresql+psycopg2://postgres@localhost", executemany_mode="values", echo=count <= 100)
    Base.metadata.create_all(engine)

    Session = sessionmaker(bind=engine)
    session = Session()

    if batch:
        enable_batch_inserting(session)

    prefix = str(int(time.time()))
    for i in range(count):
        name = "%s-%d" % (prefix, i)
        user = User(name=name)
        user.addresses = [
            Address(email_address="%s@gmail.com" % name),
            Address(email_address="%s@yahoo.com" % name),
        ]
        session.add(user)
        session.add_all(user.addresses)

    with Timer() as timer:
        session.commit()
    users = session.query(User).count()
    addresses =session.query(Address).count()
    print("took", timer.duration, "seconds")
    print("have", users, "users")
    print("have", addresses, "addresses")

class Timer:
    def __enter__(self):
        self.start = time.time()
        return self

    def __exit__(self, exc_type, value, tb):
        self.duration = time.time() - self.start

def usage_and_exit():
    sys.stderr.write(sys.argv[0] + " [batch] [count]\n")
    sys.stderr.write(sys.argv[0] + " no 50\n")
    sys.stderr.write(sys.argv[0] + " yes 1000\n")
    sys.exit(1)

if __name__ == "__main__":
    main()
