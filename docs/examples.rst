Runnable Examples
=================

OAuth Flow
----------

.. NOTE::

    The runnable source for this can be found in the `examples/2_shortcode_oauth <https://github.com/mixer/interactive-python/blob/master/examples/2_shortcode_oauth/oauth.py>`_ folder of this repo.

This example shows you how to use the shortcode OAuth flow to get an access token to connect to Interactive. For development you can `manually request a token <interactive.mixer.com/request>`_, but the shortcode flow provides a better experience to users!

.. include:: ../examples/2_shortcode_oauth/oauth.py
    :start-line: 12
    :end-line: 34
    :code: python


Pong
----

.. NOTE::

    The runnable source for this can be found in the `examples/1_viewer_controlled <https://github.com/mixer/interactive-python/blob/master/examples/1_viewer_controlled/pong.py>`_ folder of this repo.

For an initial example, we'll create a small pong game. We already wrote a tiny game engine that can be used to create a two player game like so:

.. include:: ../examples/0_init/pong.py
    :start-line: 15
    :end-line: 33
    :code: python

Let's make it Interactive!

.. include:: ../examples/1_viewer_controlled/pong.py
    :start-line: 22
    :end-line: 86
    :code: python
