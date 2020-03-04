Benchling uses SQLAlchemy and psycopg2 to talk to PostgreSQL.
To save on round-trip latency, we batch our inserts using this code.

Typically, creating and flushing N models in SQLAlchemy does N roundtrips to the database if the model has an autoincrementing primary key.
This module **improves creating N models to only require 2 roundtrips**, without requiring any other changes to your code.

Here's our accompanying blog post that describes how we investigated and improved insert performance:
[`sqlalchemy_batch_inserts`: a module for when you’re inserting thousands of rows and it’s slow](https://benchling.engineering/sqlalchemy-batch-inserts-a-module-for-when-youre-inserting-thousands-of-rows-and-it-s-slow-16ece0ef5bf7)

## Is this for me?
You may find use for this module if:
- You are using SQLAlchemy
- You are using Postgres
- You sometimes need to create several models at once and care about performance

## Usage

```python
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy_batch_inserts import enable_batch_inserting

engine = create_engine("postgresql+psycopg2://postgres@localhost", executemany_mode="values")  # SQLAlchemy < 1.3.7 needs use_batch_mode=True instead
Session = sessionmaker(bind=engine)
session = Session()
enable_batch_inserting(session)
```

If you use [Flask-SQLAlchemy](https://flask-sqlalchemy.palletsprojects.com/),

```python
from flask_sqlalchemy import SignallingSession
from sqlalchemy_batch_inserts import enable_batch_inserting

# Make sure that you've specified executemany_mode or use_batch_mode when creating your engine! Otherwise
# this library will not have any effect.
enable_batch_inserting(SignallingSession)
```

## Demo

```
docker build -t sqla_batch .
docker run --rm -v $PWD:/src --name sqla_batch sqla_batch
# Wait for it to finish spinning up
# Switch to another shell
docker exec -it sqla_batch src/demo.py no 100
docker exec -it sqla_batch src/demo.py yes 100
```

To simulate 100 * 3 inserts with 20 ms latency,
first change the connection string in demo.py from
`postgresql+psycopg2://postgres@localhost` to `postgresql+psycopg2://postgres@db`.
Then,
```
docker network create sqla_batch
docker run --rm --network sqla_batch --network-alias db --name db sqla_batch
# Switch to another shell
docker run -it -v /var/run/docker.sock:/var/run/docker.sock --network sqla_batch gaiaadm/pumba netem --duration 15m --tc-image gaiadocker/iproute2 delay --time 20 --jitter 0 db
# Switch to another shell
# This should take 100 * 3 * 20 ms = 6 seconds
docker run -it --rm -v $PWD:/src --network sqla_batch sqla_batch src/demo.py no 100
# This should take 4 * 20 ms = 0.08 seconds
docker run -it --rm -v $PWD:/src --network sqla_batch sqla_batch src/demo.py yes 100
```

## Acknowledgements

This is all possible thanks to @dvarrazzo's psycopg2 [execute_batch](http://initd.org/psycopg/docs/extras.html#fast-execution-helpers)
and @zzzeek's SQLAlchemy [support for the same](https://docs.sqlalchemy.org/en/13/dialects/postgresql.html#psycopg2-fast-execution-helpers)
and [helpful](https://groups.google.com/forum/#!topic/sqlalchemy/GyAZTThJi2I)
[advice](https://groups.google.com/forum/#!msg/sqlalchemy/l02TH_m1DkU/7PMlF8HzAgAJ) on the mailing list.

## Maintainer notes

After bumping the `version` in `setup.py` and `__version__` in `__init__.py`,

```
$ ./setup.py sdist
$ twine upload --repository-url https://test.pypi.org/legacy/ dist/*
# Check https://test.pypi.org/project/sqlalchemy-batch-inserts/
$ twine upload dist/*
```
