#!/usr/bin/env python3

import setuptools

long_description = """
Benchling uses SQLAlchemy and psycopg2 to talk to PostgreSQL.
To save on round-trip latency, we batch our inserts using this code.

In summary, flushing 100 models in SQLAlchemy does 100 roundtrips to the database if the model has an autoincrementing primary key.
This module improves this to 2 roundtrips without requiring any other changes to your code.

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

## Acknowledgements

This is all possible thanks to @dvarrazzo's psycopg2 [execute_batch](http://initd.org/psycopg/docs/extras.html#fast-execution-helpers)
and @zzzeek's SQLAlchemy [support for the same](https://docs.sqlalchemy.org/en/latest/dialects/postgresql.html#psycopg2-batch-mode)
and [helpful](https://groups.google.com/forum/#!topic/sqlalchemy/GyAZTThJi2I)
[advice](https://groups.google.com/forum/#!msg/sqlalchemy/l02TH_m1DkU/7PMlF8HzAgAJ) on the mailing list.
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
