#!/usr/bin/env python3

import setuptools

long_description = """
Benchling uses SQLAlchemy and psycopg2 to talk to PostgreSQL.
To save on round-trip latency, we batch our inserts using this code.

## Usage

```
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy_batch_inserts import enable_batch_inserting

engine = create_engine("postgresql+psycopg2://postgres@localhost", use_batch_mode=True)
Session = sessionmaker(bind=engine)
session = Session()
enable_batch_inserting(session)
```

If you use [Flask-SQLALchemy](https://flask-sqlalchemy.palletsprojects.com/),

```
from flask_sqlalchemy import SignallingSession

enable_batch_inserting(SignallingSession)
```
"""

setuptools.setup(
    name="sqlalchemy_batch_inserts",
    version="0.0.1",
    author="Vineet Gopal",
    author_email="vineet@benchling.com",
    description="Batch inserts for SQLAlchemy on PostgreSQL with psycopg2",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/benchling/sqlalchemy_batch_inserts",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)
