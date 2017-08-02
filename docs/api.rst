API
===

This document describes the Python API to connect to Mixer's Interactive service. We assume you're already somewhat familiar with Interactive. If you're not, check our `reference guide <https://dev.mixer.com/reference/interactive/index.html>`_.

To connect to Interactive, you first need to have an Interactive project and some means of authentication. You'll want to `create an Interactive project <https://dev.mixer.com/reference/interactive/index.html#creating-an-interactive-project>`_ on Mixer and register an `OAuth client <https://dev.mixer.com/reference/oauth/index.html#registering>`_ while you're there. For most integrations, you can leave the OAuth "redirect URLs" empty, and you should not request a secret key.

You can now use the OAuthClient class with your OAuth client ID to get an access token.

OAuth
-----

.. autoclass:: interactive_python.OAuthClient
    :members:
    :undoc-members:

.. autoclass:: interactive_python.OAuthShortCode
    :members:
    :undoc-members:

    .. attribute:: code

        The short six-digit code to be displayed to the user. They should be prompted to enter it on `mixer.com/go <https://mixer.com/go>`_.

.. autoclass:: interactive_python.OAuthTokens
    :members:
    :undoc-members:

    .. attribute:: access

        The OAuth access token to use in :func:`~interactive_python.State.connect`.

    .. attribute:: refresh

        The OAuth refresh token that can be used to re-grant the access token.

    .. attribute:: expires_at

        The datetime at which the access token expires.

State
-----

.. autoclass:: interactive_python.State
    :members:
    :undoc-members:
    :show-inheritance:

    .. attribute:: connection

        The underlying :class:`~interactive_python.Connection` to the Interactive service. You should not need to deal with this most of the time.

.. autoclass:: interactive_python.Discovery
    :members:
    :undoc-members:
    :show-inheritance:

Scenes
------

.. autoclass:: interactive_python.Scene
    :members:
    :show-inheritance:

    .. attribute:: controls

        A dict of control IDs to :class:`~interactive_python.Control`s in the scene.


.. autoclass:: interactive_python.Control
    :members:
    :undoc-members:
    :show-inheritance:

.. autoclass:: interactive_python.Button
    :members:
    :undoc-members:
    :show-inheritance:

.. autoclass:: interactive_python.Joystick
    :members:
    :undoc-members:
    :show-inheritance:

Utilities
---------

.. data:: interactive_python.keycode

    Keycode is an instance of a class that helps translate keycodes from their textual representation to their corresponding numeric code, as represented on the protocol. For example::

        from interactive_python import keycode

        print(keycode.up)     # => 38
        print(keycode.a)      # => 65
        getattr(keycode, '⌘') # => 91


.. autoclass:: interactive_python._util.ChangeTracker
    :members:
    :undoc-members:
    :show-inheritance:

.. autoclass:: interactive_python._util.Resource
    :members:
    :undoc-members:
    :show-inheritance:

Errors
------

.. autoclass:: interactive_python.DiscoveryError
    :show-inheritance:

.. autoclass:: interactive_python.NoServersAvailableError
    :show-inheritance:

.. autoclass:: interactive_python.ShortCodeError
    :show-inheritance:

.. autoclass:: interactive_python.UnknownShortCodeError
    :show-inheritance:

.. autoclass:: interactive_python.ShortCodeAccessDeniedError
    :show-inheritance:

.. autoclass:: interactive_python.ShortCodeTimeoutError
    :show-inheritance:

Low-Level Protocol
------------------

.. autoclass:: interactive_python.Connection
    :members:
    :undoc-members:
    :show-inheritance:

.. autoclass:: interactive_python.Call
    :members:
    :undoc-members:
    :show-inheritance:


.. automodule:: interactive_python.encoding
    :members:
    :undoc-members:
    :show-inheritance:
