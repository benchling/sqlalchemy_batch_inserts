from itertools import groupby
import warnings

import sqlalchemy


__version__ = "0.0.4"


def _group_models_by_base_mapper(initial_models):
    """Returns a list of (base_mapper, models) tuples"""
    sort_key = lambda model: str(type(model).__mapper__.base_mapper)
    models_sorted_by_class = sorted(initial_models, key=sort_key)
    return groupby(models_sorted_by_class, key=lambda model: type(model).__mapper__.base_mapper)


def _get_column_python_type(column):
    return column.type.python_type


def _has_normal_id_primary_key(base_mapper):
    """Check if the primary key for base_mapper is an auto-incrementing integer `id` column"""
    primary_key_cols = base_mapper.primary_key
    if len(primary_key_cols) != 1:
        return False

    [primary_key_col] = primary_key_cols
    try:
        python_column_type = _get_column_python_type(primary_key_col)
    except NotImplementedError:
        # python_type isn't implemented for e.g. UUIDs, which we don't support yet anyway.
        python_column_type = None

    return (
        primary_key_col.name == "id"
        and python_column_type == int
        and primary_key_col.autoincrement in ("auto", True)
        and primary_key_col.table == base_mapper.local_table
    )


def _get_id_sequence_name(base_mapper):
    assert _has_normal_id_primary_key(base_mapper), "_get_id_sequence_name only supports id primary keys"
    return "%s_id_seq" % base_mapper.entity.__tablename__


def tuples_to_scalar_list(tuples):
    return [scalar for [scalar] in tuples]


def _get_next_sequence_values(session, base_mapper, num_values):
    """Fetches the next `num_values` ids from the `id` sequence on the `base_mapper` table.

    For example, if the next id in the `model_id_seq` sequence is 12, then
    `_get_next_sequence_values(session, Model.__mapper__, 5)` will return [12, 13, 14, 15, 16].
    """
    assert _has_normal_id_primary_key(
        base_mapper
    ), "_get_next_sequence_values assumes that the sequence produces integer values"

    id_seq_name = _get_id_sequence_name(base_mapper)
    # Table.schema is the canonical place to get the name of the schema.
    # See https://docs.sqlalchemy.org/en/13/core/metadata.html#sqlalchemy.schema.Table.params.schema
    schema = base_mapper.entity.__table__.schema
    sequence = sqlalchemy.Sequence(id_seq_name, schema=schema)

    # Select the next num_values from `sequence`
    raw_ids = tuples_to_scalar_list(
        session.connection().execute(
            sqlalchemy.select([sequence.next_value()]).select_from(
                sqlalchemy.text("generate_series(1, :num_values)")
            ),
            {"num_values": num_values},
        )
    )

    assert len(raw_ids) == num_values, u"Expected to get {} new ids, instead got {}".format(
        num_values, len(raw_ids)
    )

    # session.execute returns `long`s since Postgres sequences use `bigint` by default.
    # However, we need ints since the column type for our primary key is `integer`.
    return [int(id_) for id_ in raw_ids]


def _group_insert_orders_by_class(new_models):
    """Change the insert_orders so models of the same class (not database table) are inserted together.

    Example:
      a1 = A()
      b1 = B()
      a2 = A()
      b2 = B()

    Let's define a "query group" as a list of INSERT statements that can be grouped together
    by execute_batch.

    Previously, SQLAlchemy would have performed INSERTs in the order:
        a1, b1, a2, b2 (4 query groups, since INSERTs for a1 and b1 can't be grouped together)
    After resetting the insert orders to group by type, the new order is:
        a1, a2, b1, b2 (2 query groups, since INSERTs for a1, a2 can be grouped together), or
        b1, b2, a1, a2 (2 query groups)

    SQLAlchemy uses state.insert_order to determine the order in which items are inserted into
    the database during a flush. Typically, the insert_order reflects the order in which
    the Python models were actually created. Grouping models by class means that optimizations
    like `psycopg2.extras.execute_batch` will be more useful, since similar INSERT statements
    will actually be grouped together.

    For almost all applications, only the ordering of INSERTs within a given table matters, so
    it's safe to reorder things *across* tables. We already rely on SQLAlchemy reordering
    INSERTs across tables to handle foreign key dependencies.

    However, instead of sorting by database table, we sort by Python class to handle models
    using inheritance. Imagine we have a parent class Base, and two child classes SubBase1
    and SubBase2 (using STI).

    Example:
        a1 = SubBase1()
        b1 = SubBase2()
        a2 = SubBase1()
        b2 = SubBase2()

    Without any changes to insert_order, the order of INSERTS would be:
        a1, b1, a2, b2 (4 query groups)
    If we sort by "table" (or base_mapper), then the order of INSERTS is exactly the same, since they
    all have the same base_mapper (Base):
        a1, b1, a2, b2 (4 query groups)
    Instead, we group by class instead, giving us two possible ordering with two query groups each:
        ((a1, a2), b1, b2) or ((b1, b2), (a1, a2))
    """
    sort_key = lambda model: (str(type(model)), sqlalchemy.inspect(model).insert_order)
    sorted_models = sorted(new_models, key=sort_key)
    for i, model in enumerate(sorted_models):
        sqlalchemy.inspect(model).insert_order = i


def batch_populate_primary_keys(
    session, new_models, skip_unsupported_models=False, skip_if_single_model=False
):
    """Query for and populate the primary keys for all models in new_models with integer `id` primary keys.

    This uses the database id sequence to populate the id field for new_models with an integer `id`
    primary key.

    :param skip_unsupported_models: Skip models that do not have auto-incrementing single `id` primary keys.
                                    Raises an AssertionError for models with other primary keys.
    :param skip_if_single_model: Skips if there's only one model in `new_models`. Useful for avoiding an
                                 additional query from performing the nextval query.
    """
    for base_mapper, models in _group_models_by_base_mapper(new_models):
        if not _has_normal_id_primary_key(base_mapper):
            if skip_unsupported_models:
                continue
            else:
                raise AssertionError("Expected models to have auto-incrementing `id` primary key")

        # In general, batch_populate_primary_keys shouldn't assume anything about how people are creating
        # models - it is possible for models to have their ids already specified.
        models = [model for model in models if model.id is None]

        if skip_if_single_model and len(models) <= 1:
            continue

        new_ids = _get_next_sequence_values(session, base_mapper, len(models))

        models = sorted(models, key=lambda model: sqlalchemy.inspect(model).insert_order)
        for id_, model in zip(new_ids, models):
            model.id = id_


def enable_batch_inserting(sqla_session):
    """Improve general performance when doing lots of inserts

    In summary, enabling this will enable SQLAlchemy to group similar INSERT statements together,
    and reduce the number of back-and-forths required to the database.

    Example:
        for i in xrange(10):
            session.add(A())
        session.commit()

    Previously, this would perform 10 separate INSERT statements and incur the overhead of 10
    separate queries to the database. With execute_batch_mode, psycopg2 will group similar INSERTs
    together and send them to the database together (in groups of 100 by default).

    To actually allow execute_batch_mode to do grouping well, we need to do two things:
    1) Ensure that models already have their primary keys specified, and are not relying on the database
       to specify these with e.g. autoincrement. SQLAlchemy uses `RETURNING id` to get the
       primary key of a newly created model, but cannot use RETURNING when doing batched inserts. See
       https://groups.google.com/d/msg/sqlalchemy/GyAZTThJi2I/x2WJImr-BgAJ for more information.

    2) Order model creation so that models of the same type are inserted together. This should not have
       any application-facing effects.
    """

    @sqlalchemy.event.listens_for(sqla_session, "before_flush")
    def handle_before_flush(session, flush_context, instances):
        if instances is not None:
            warnings.warn("enable_batch_inserting does not support deprecated call to session.flush([models])")
            return

        new_models = list(session.new)

        # First, populate the primary keys using the original insert_orders.
        batch_populate_primary_keys(
            session, new_models, skip_unsupported_models=True, skip_if_single_model=True
        )

        # Then, rewrite the insert_orders so objects of the same type are grouped together.
        _group_insert_orders_by_class(new_models)
