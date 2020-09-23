#!/usr/bin/env python3

import setuptools

long_description = """
Benchling uses SQLAlchemy and psycopg2 to talk to PostgreSQL.
To save on round-trip latency, we batch our inserts using this code.

Typically, creating and flushing N models in SQLAlchemy does N roundtrips to the database if the model has an autoincrementing primary key.
This module **improves creating N models to only require 2 roundtrips**, without requiring any other changes to your code.

## Is this for me?
You may find use for this module if:
- You are using SQLAlchemy
- You are using Postgres
- You sometimes need to create several models at once and care about performance

## Usage

```
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy_batch_inserts import enable_batch_inserting

engine = create_engine("postgresql+psycopg2://postgres@localhost", executemany_mode="values")  # SQLAlchemy < 1.3.7 needs use_batch_mode=True instead
Session = sessionmaker(bind=engine)
session = Session()
enable_batch_inserting(session)
```

If you use [Flask-SQLALchemy](https://flask-sqlalchemy.palletsprojects.com/),

```
from flask_sqlalchemy import SignallingSession
from sqlalchemy_batch_inserts import enable_batch_inserting

# Make sure that you've specified executemany_mode or use_batch_mode when creating your engine! Otherwise
# this library will not have any effect.
enable_batch_inserting(SignallingSession)
```

## Acknowledgements

This is all possible thanks to @dvarrazzo's psycopg2 [execute_batch](http://initd.org/psycopg/docs/extras.html#fast-execution-helpers)
and @zzzeek's SQLAlchemy [support for the same](https://docs.sqlalchemy.org/en/13/dialects/postgresql.html#psycopg2-fast-execution-helpers)
and [helpful](https://groups.google.com/forum/#!topic/sqlalchemy/GyAZTThJi2I)
[advice](https://groups.google.com/forum/#!msg/sqlalchemy/l02TH_m1DkU/7PMlF8HzAgAJ) on the mailing list.
"""

setuptools.setup(
    name="sqlalchemy_batch_inserts",
    version="0.0.4",
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
