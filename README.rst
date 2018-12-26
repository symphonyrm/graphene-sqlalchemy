Please read
`UPGRADE-v2.0.md <https://github.com/graphql-python/graphene/blob/master/UPGRADE-v2.0.md>`__
to learn how to upgrade to Graphene ``2.0``.

--------------

####
|Graphene Logo| Graphene-SQLAlchemy |Build Status| |PyPI version| |Coverage Status|
####

A `SQLAlchemy <http://www.sqlalchemy.org/>`__ integration for
`Graphene <http://graphene-python.org/>`__.

************
Installation
************

For instaling graphene, just run this command in your shell

.. code:: bash

    pip install "graphene-sqlalchemy>=2.0"

********
Examples
********

Here is a simple SQLAlchemy model:

.. code:: python

    from sqlalchemy import Column, Integer, String
    from sqlalchemy.orm import backref, relationship

    from sqlalchemy.ext.declarative import declarative_base

    Base = declarative_base()

    class UserModel(Base):
        __tablename__ = 'department'
        id = Column(Integer, primary_key=True)
        name = Column(String)
        last_name = Column(String)

To create a GraphQL schema for it you simply have to write the
following:

.. code:: python

    from graphene_sqlalchemy import SQLAlchemyObjectType

    class User(SQLAlchemyObjectType):
        class Meta:
            model = UserModel

    class Query(graphene.ObjectType):
        users = graphene.List(User)

        def resolve_users(self, info):
            query = User.get_query(info)  # SQLAlchemy query
            return query.all()

    schema = graphene.Schema(query=Query)

Then you can simply query the schema:

.. code:: python

    query = '''
        query {
          users {
            name,
            lastName
          }
        }
    '''
    result = schema.execute(query, context_value={'session': db_session})

To learn more check out the following `examples <examples/>`__:

-  **Full example**: `Flask SQLAlchemy
   example <examples/flask_sqlalchemy>`__

******************
Extensions to Fork
******************

NOTE: This should be removed or placed into the documentation once we have a further chance to clean it up.
      For now it's easiest for others if it all lives right here.

Extensions to ``graphene-sqlalchemy`` provided by this fork fall into a few major areas:

Generalizing the Registry
=========================

First, the registry_ has been changed from a global object that can only store ``SQLAlchemyObjectType``.

This becomes unwieldy as soon as you start adding other base types that you'd like to all register as a set, for example:

- All ``SQLAlchemyInputObjectType``
- All ``SQLAlchemyCreateInputObjectType``
- etc.

which would require creating a completely different registry class and corresponding global object for each type.

Instead, we change the Registry class to take in a super class at initialization instead of hardcoding ``SQLAlchemyObjectType``.

Further, we create a namespaced dict of ``Registry`` objects in namespace_,
and a function for accessing a specific ``Registry`` object, or creating it if it doesn't exist.

We then partially apply that function with the given namespace, so that it's accessible everywhere
without polluting the global scope.

In short, we turn the global into a partially applied closure in order to implement a Singleton pattern.

Making the Behavior of ``construct_fields`` Extensible
======================================================

Next, we extend the ``construct_fields`` logic considerably. Much of what you would want to do with
this library essentially boils down to, for a given model:

- looping over all fields
- creating a GraphQL field for each given field
- possibly overriding the behavior for fields of a given type in some specific way

The problem is that much of the logic you might want to override lives relatively deeply in the call
structure for this logic, meaning that there would necessarily be a significant amount of code
duplication and boilerplate for a comparatively tiny logical change.

Further, that override logic may not **just** depend on the class itself, for instance
``SQLAlchemyObjectType``, but also potentially on:

- the type of the field on the ``SQLAlchemy`` model (``Column``, ``RelationshipProperty``, etc.)
- the type of the column in the case of a ``Column`` (``types.BigInteger``, ``types.UUID``, etc.)

And even further, we want to be able to use this override logic *across* library boundaries,
extending it arbitrarily based on type.

We get around this by using the multipledispatch_ library to create multimethods dispatched based
on the type of all arguments. We then create what can be described as a public extensible API of
multimethods in api_, and using the same trick we used above for registry_ to create a Singleton
object for the dispatch namespace in namespace_.

We generally define default implementations in api_ for any ``cls`` subclassing ``BaseType``, then
specific types can modify that behavior as necessary.

Design concerns and "Gotchas" with ``multipledispatch``
-------------------------------------------------------

There are a few design concerns and hiccups to be aware of when working with ``multipledispatch``.

First, while we're using ``mypy`` style type constraints to specify how to dispatch, there are a
few areas where this doesn't work well. Specifically, it doesn't have very good support for
``Union[type1, type2, ...]``. Instead, you need to specify ``Union`` types as tuples.

Next, when calling dispatched functions with classes that haven't been fully created yet, the
type of ``cls`` will be ``type``, the type of types, rather then the specific class that you're
creating. You can get around this by redispatching, an example of this is in name_ among other
places. Unfortunately, since we're largely calling these methods ultimately from the initial
``__init_subclass_with_meta__`` method call, this is a pretty large portion of our use case, so we
have to specify this additional dispatch a number of places. Thankfully, it largely only happens at
server startup time when we're creating the classes.

It's also important to remember that, for classes, ``multipledispatch`` uses Python's internal
``issubclass`` function to dispatch on subclasses.

We've also used ``multipledispatch`` in a few places where the goal isn't really to offer an
extensible API, but rather to simplify walking over recursively defined data types, such as over
``Model``, ``Column``, and ``RelationshipProperty`` classes appropriately.

`construct_fields`_
-------------------

TODO: Check this section

The list of extensible API functions, as well as some examples of using them are as below. We'll
walk through them largely in the order that they are called via ``construct_fields``:

`ignore_field`_
^^^^^^^^^^^^^^^

allows overriding whether a field gets ignored. By default just calls ``explicitly_ignored`` which
checks the ``only_fields`` and ``exclude_fields`` parameters that get passed in on an ``ObjectType``
``Meta`` class. An example of overriding this behavior is `SQLAlchemyCreateInputObjectType`_ where
we also ignore any autoincrement primary key fields.

`convert_name`_
^^^^^^^^^^^^^^^

returns the name of the resulting GraphQL from the model field. By default just returns the result
of calling ``get_name``. An example of extending this is `SQLAlchemyCreateInputObjectType`_, which
converts foreign key columns and relationships to be ``attachTo{relationship.key}`` and
``createAndAttachTo{relationship.key}``, respectively.

`get_name`_
^^^^^^^^^^^

simply gets the name of the ``SQLAlchemy`` field type (``column.name`` vs ``relationship.key``, for
example). Generally this is just used internally by ``convert_name``.

`convert_orm_prop`_
^^^^^^^^^^^^^^^^^^^

dispatches based on the ``SQLAlchemy`` field type. The primary two to understand are ``Column`` and
``RelationshipProperty``. For ``Column`` fields, it just calls ``convert_sqlalchemy_type``. For
``RelationshipProperty``, it creates a GraphQL ``Dynamic`` field that calls into the ``Registry`` to
grab the appropriate ``ObjectType``. This doesn't happen until ``Schema`` creation, which gets
around circular dependencies in the ``ObjectType`` classes.

`convert_sqlalchemy_type`_
^^^^^^^^^^^^^^^^^^^^^^^^^^

converts a ``Column`` to a GraphQL ``Scalar`` type based on the column's type. For example,
``types.DateTime`` gets converted to a ``DateTime``. An example of overriding this behavior is
`SQLAlchemyFilterInputObjectType`_ where instead of converting to a ``Scalar`` we convert to some
``FilterInputObjectType``.

`get_doc`_
^^^^^^^^^^

Generally called by ``convert_sqlalchemy_type`` to get the GraphQL field's documentation.
``get_doc`` doesn't currently get overridden by anything.

`is_nullable`_
^^^^^^^^^^^^^^

Generally called by ``convert_sqlalchemy_type`` to determine if a field should be `NonNull`. By
default, this checks for ``column.nullable``. An example of ``is_nullable`` getting overridden is in
`SQLAlchemyEditInputObjectType`_ where we make sure all columns are optional. This is so we don't
have to pass up all required fields if we just want to edit a single field.

This constitutes essentially the entire flow of ``construct_fields``.

Other extension points
----------------------

Note that there are a few other places we use multipledispatch_, not for extensibility, but for
dealing with recursion in a (hopefully) clearer way. That's not to say they can't be extended, but
it wasn't the primary goal.

`convert_to_instance`_
^^^^^^^^^^^^^^^^^^^^^^

Converts an ``InputObjectType`` to a ``SQLAlchemy`` model instance recursively. This is primarily
used for getting an instance appropriate for mutations and passing to ``session.add``,
``session.merge``, and ``session.delete``, for example.

`convert_to_query`_
^^^^^^^^^^^^^^^^^^^

Converts a ``FilterInputObjectType`` to a ``Query`` object recursively. This is primarily used to
recursively build a filtered query for ``SQLAlchemyFilterInputObjectType``.

Contributed types with extended behavior
========================================

Additionally, we add a contrib_ directory of classes that serve as:

- examples of using the extensions provided by api_
- additions to the 'out of the box' functionality provided by this library

We'll walk through these modeling the class hierarchy via header depth.

`SQLAlchemyInputObjectType`_
----------------------------

This largely does the same thing as `SQLAlchemyObjectType`_:

- Setting the registry type if it isn't already specified.
- Calling ``construct_fields`` on the model and setting the GraphQL fields appropriately.

Unfortunately we have to duplicate this code, because the "greatest common denominator" superclass
of ``ObjectType`` and ``InputObjectType`` lives outside this library.

`SQLAlchemyCreateInputObjectType`_
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Alters the default behavior of ``construct_fields`` to:

- ignore primary key autoincrement fields
- ignore any ``created_at`` or ``updated_at`` fields if they have defaults
- make foreign key fields nullable
- rename foreign key and relationship fields

`SQLAlchemyEditInputObjectType`_
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

largely does the same thing as `SQLAlchemyCreateInputObjectType`, but also:

- ensure all fields are nullable. This is largely for developer ergonomics, so we don't have to
  pass up all ``NonNull`` fields even if we're not editing them.

It's possible we should put most of this shared functionality on a superclass between these classes
and ``SQLAlchemyInputObjectType``.

`SQLAlchemyFilterByInputObjectType`_
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Alters the default behavior of ``construct_fields`` to:

- ignore all relationships
- ensure all fields are nullable. This is used to construct an object that can be passed directly
  into ``.filter_by`` on a ``Query`` object.

`SQLAlchemyFilterInputObjectType`_
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Alters the default behavior of ``construct_fields`` to:

- ignore all foreign key columns
- ensure all fields are nullable
- converts all ``Column`` fields to ``FilterInputObjectType`` fields, based on the ``column.type``

`CountableConnection`_
----------------------

Extends the ``relay.Connection`` class to add a ``totalCount`` field to the connection, and then
resolves to the ``length`` field on the returned query connection object. This logic mostly already
existed in the ``SQLAlchemyConnectionField``, but for some reason it wasn't actually surfaced
anywhere. So now we do!

`InstrumentedQuery`_
--------------------

Extends ``SQLAlchemyConnectionField`` and adds simple and complex filtering to a connection:

- automatically creating the relevant ``SQLAlchemyFilterByInputObjectType`` classes for a given
  model and placing it on the connection as the ``filter_by`` field.
- automatically creating the relevant ``SQLAlchemyFilterInputObjectType`` classes for a given
  model and placing it on the connection as the ``filter`` field.
- Adding an ``order_by`` field that takes a list of fields to order by. Takes a list of strings of
  of the form ``"<field_name> <asc|desc>"`` to determine what to order by, and in what direction.
- Builds a query incrementally by calling ``.filter_by``, ``.filter(convert_to_query(...))``, and
  ``.order_by`` on the initial query.

`SQLAlchemyMutation`_
---------------------

This base class does one main thing, it specifies a `Field` method which generates a GraphQL field
with the appropriate arguments and output, provided those have been specified on the
``cls._meta.arguments`` and ``cls._meta.output``, respectively.

`SQLAlchemyCreateMutation`_
^^^^^^^^^^^^^^^^^^^^^^^^^^^

- Defines a ``mutate`` method that converts the ``SQLAlchemyCreateInputObjectType`` to a model
  instance and commits the changes.
- At class creation, automatically creates the necessary ``SQLAlchemyCreateInputObjectType`` and
  ``SQLAlchemyObjectType`` classes as the ``input`` and ``output``, respectively.
- Places those in ``cls._meta.arguments`` ``cls._meta.output`` respectively.

`SQLAlchemyDeleteMutation`_
^^^^^^^^^^^^^^^^^^^^^^^^^^^

- Defines a ``mutate`` method that converts the ``SQLAlchemyDeleteInputObjectType`` to a model
  instance and commits the changes.
- At class creation, automatically creates the necessary ``SQLAlchemyDeleteInputObjectType`` and
  ``SQLAlchemyObjectType`` classes as the ``input`` and ``output``, respectively.
- Places those in ``cls._meta.arguments`` ``cls._meta.output`` respectively.

`SQLAlchemyEditMutation`_
^^^^^^^^^^^^^^^^^^^^^^^^^

- Defines a ``mutate`` method that converts the ``SQLAlchemyEditInputObjectType`` to a model
  instance and commits the changes.
- At class creation, automatically creates the necessary ``SQLAlchemyEditInputObjectType`` and
  ``SQLAlchemyObjectType`` classes as the ``input`` and ``output``, respectively.
- Places those in ``cls._meta.arguments`` ``cls._meta.output`` respectively.

`SQLAlchemyAutogenQuery`_
-------------------------

generates the top-level ``query: ObjectType`` that gets passed to ``graphene.Schema``. Does this by
taking a list of models in its ``Meta`` class, and, similarly to the above ``Mutation`` subclasses,
generates ``ObjectType`` classes as necessary for each model in the list, and then adding those
fields to itself.

`SQLAlchemyAutogenMutation`_
----------------------------

generates the top-level ``mutation: ObjectType`` that gets passed to ``graphene.Schema``. Does this
by taking a list of models in its ``Meta`` class, and, similarly to the above ``SQLAlchemyAutogenQuery``
class, generates ``ObjectType`` and ``InputObjectType`` classes as necessary for each model in the
list, and then adding those fields to itself.

TODO
====

There are still a number of things to accomplish before trying to upstream these changes.

- Move this documentation into the actual Sphinx documentation. For now it makes the most sense for
  it to live here for simplicity's sake, but it needs to be moved.
- Add further examples to the documentation once it's moved, with simple schemas for illustrative
  purposes.
- There are a few code-cleanup issues listed under ``TODO`` strewn around the code.
- Tests need to be cleaned up and committed.
- ``Tox`` tests should be added to ensure we run against Python2 and Python3.
- Need to convert the type annotations to support Python2, unfortunately.
- Add docstrings to all classes/functions/methods. Graphene uses class-level docstrings to build
  documentation for object and input types, so this will be helpful.
- Look into how possible it is to auto-generate said docstrings for generated classes. Would be
  better then using the docstring for the base class.

************
Contributing
************

After cloning this repo, ensure dependencies are installed by running:

.. code:: sh

    python setup.py install

After developing, the full test suite can be evaluated by running:

.. code:: sh

    python setup.py test # Use --pytest-args="-v -s" for verbose mode

.. |Graphene Logo| image:: http://graphene-python.org/favicon.png
.. |Build Status| image:: https://travis-ci.org/graphql-python/graphene-sqlalchemy.svg?branch=master
   :target: https://travis-ci.org/graphql-python/graphene-sqlalchemy
.. |PyPI version| image:: https://badge.fury.io/py/graphene-sqlalchemy.svg
   :target: https://badge.fury.io/py/graphene-sqlalchemy
.. |Coverage Status| image:: https://coveralls.io/repos/graphql-python/graphene-sqlalchemy/badge.svg?branch=master&service=github
   :target: https://coveralls.io/github/graphql-python/graphene-sqlalchemy?branch=master
.. _multipledispatch: https://pypi.org/project/multipledispatch/>
.. _registry: ./graphene_sqlalchemy/registry.py
.. _namespace: ./graphene_sqlalchemy/api/namespace.py
.. _api: ./graphene_sqlalchemy/api/
.. _name: ./graphene_sqlalchemy/api/name.py
.. _construct_fields: ./graphene_sqlalchemy/api/orm.py
.. _ignore_field: ./graphene_sqlalchemy/api/ignore.py
.. _convert_name: ./graphene_sqlalchemy/api/name.py
.. _get_name: ./graphene_sqlalchemy/api/name.py
.. _convert_orm_prop: ./graphene_sqlalchemy/api/orm.py
.. _convert_sqlalchemy_type: ./graphene_sqlalchemy/api/type.py
.. _get_doc: ./graphene_sqlalchemy/api/doc.py
.. _is_nullable: ./graphene_sqlalchemy/api/nullable.py
.. _convert_to_instance: ./graphene_sqlalchemy/api/input.py
.. _convert_to_query: ./graphene_sqlalchemy/api/query.py
.. _contrib: ./graphene_sqlalchemy/contrib/
.. _SQLAlchemyObjectType: ./graphene_sqlalchemy/types.py
.. _SQLAlchemyInputObjectType: ./graphene_sqlalchemy/contrib/input_type.py
.. _SQLAlchemyCreateInputObjectType: ./graphene_sqlalchemy/contrib/create_input_type.py
.. _SQLAlchemyEditInputObjectType: ./graphene_sqlalchemy/contrib/edit_input_type.py
.. _SQLAlchemyFilterInputObjectType: ./graphene_sqlalchemy/contrib/filter_input_type.py
.. _SQLAlchemyFilterByInputObjectType: ./graphene_sqlalchemy/contrib/filter_by_input_type.py
.. _CountableConnection: ./graphene_sqlalchemy/contrib/countable_connection.py
.. _InstrumentedQuery: ./graphene_sqlalchemy/contrib/filter_connection.py
.. _SQLAlchemyMutation: ./graphene_sqlalchemy/contrib/mutation.py
.. _SQLAlchemyCreateMutation: ./graphene_sqlalchemy/contrib/mutation.py
.. _SQLAlchemyDeleteMutation: ./graphene_sqlalchemy/contrib/mutation.py
.. _SQLAlchemyEditMutation: ./graphene_sqlalchemy/contrib/mutation.py
.. _SQLAlchemyAutogenQuery: ./graphene_sqlalchemy/contrib/schema.py
.. _SQLAlchemyAutogenMutation: ./graphene_sqlalchemy/contrib/schema.py
