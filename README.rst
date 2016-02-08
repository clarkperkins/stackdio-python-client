stackdio-python-client
======================

|Travis CI|

The canonical Python client and cli for the stackd.io API


Overview
--------

This is a small set of tools for internal use of stackd.io.  After cloning
this repo, you should be able to quickly get up and running with your own
stacks.  

Advanced usage like creating custom blueprints or writing your own formulas is
beyond the scope of this.

Installation
------------

We recommend using virtualenv via `virtualenvwrapper`_ to install this in a
virtualenv.  If you consider yourself a knowledgeable Pythonista, feel free to
install this however you'd like, but this document will assume that you are 
using virtualenvwrapper.  See the full `virtualenvwrapper`_ docs for details,
but in short you can install it on most systems like:

.. code:: bash

    pip install virtualenvwrapper

Once you've got it, installing this tool goes something like:

.. code:: bash

    mkvirtualenv stackdio-client

    pip install stackdio

You'll see a few things scrolling by, but should be set after this.  To use 
this later, you'll need to re-activate the virtualenv like:

.. code:: bash

    workon stackdio-client

Whenever it's activated, ``stackdio-cli`` should be on your path.

First Use
---------

The first time that you fire up ``stackdio-cli``, you'll need to run the
``configure`` command.  This will prompt you for your LDAP username and
password, and store them securely in your OS keychain for later use.  It will
import some standard formula, and create a few commonly used blueprints.

.. code:: bash

    $ stackdio-cli
    None @ None
    > configure
    # YOU WILL BE WALKED THROUGH A SIMPLE SET OF QUESTIONS

Stack Operations
----------------

All of the following assume that you have run ``initial_setup`` successfully.  To
launch the cli, simply type:

.. code:: bash

    $ stackdio-cli

You can run ``help`` at any point to see available commands.  For details on a
specific command you can run ``help COMMAND``, e.g. ``help stacks``.  The rest of 
these commands assume you have the cli running.

Launching Stacks
~~~~~~~~~~~~~~~~
Stacks are launched from blueprints.  To launch the 3 node HBase stack that's
included with this you do:

.. code:: bash

    > stacks launch cdh450-ipa-3 MYSTACKNAME


.. note::

    To avoid DNS namespace collisions, the stack name needs to be unique.
    An easy way to ensure this is to include your name in the stack name.

Deleting Stacks
~~~~~~~~~~~~~~~

When you are done with a stack you can delete it.  This is destructive and
cannot be recovered from, so think carefully before deleting your stack!

.. code:: bash

    > stacks delete STACK_NAME

Alternatively you can ``terminate`` a stack which will terminate all instances,
but leave the stack definition in place.

Provisioning Stacks
~~~~~~~~~~~~~~~~~~~

Occassionally something will go wrong when launching your stack, e.g. network
connections may flake out causing some package installations to fail.  If this
happens you can manually provision your stack, causing everything to be brought
back up to date:

.. code:: bash

    > stacks provision STACK_NAME

Stack Info
~~~~~~~~~~

Once you have launched a stack, you can then monitor the status of it like:

.. code:: bash

    > stacks history STACK_NAME

This displays the top level information for a stack.  You can supply additional
arguments to pull back additional info about a stack.  For example, to get a
list of FQDNs (aka hostnames) for a stack:

.. code:: bash

    > stacks hostnames STACK_NAME

There are various logs available that you can access with the ``stacks logs``
command.

What's Next?
------------

For anything not covered by this tool, you'll need to use the stackdio-server web UI or 
API directly.  For more information on that, check out http://docs.stackd.io.


.. |Travis CI| image:: https://travis-ci.org/stackdio/stackdio-python-client.svg?branch=master
   :target: https://travis-ci.org/stackdio/stackdio-python-client
   :alt: Build Status

.. _virtualenvwrapper: https://pypi.python.org/pypi/virtualenvwrapper
