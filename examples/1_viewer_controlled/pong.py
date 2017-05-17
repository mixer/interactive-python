"""
We've modified our base pong game to run an interactive where the viewers
control the paddle on the right. Press 'q' to quit.

Run this with::

    python -m examples.0_init.pong
"""

from ..engine import BaseGame, run


class Game(BaseGame):
    def __init__(self):
        super(Game, self).__init__()
        self._player_1 = self._create_paddle(x=0, height=self._screen_height//6)
        self._player_2 = self._create_paddle(x=self._screen_width-1,
                                             height=self._screen_height//6)

    def update(self, pressed_key=None):
        if pressed_key == ord('s'):
            self._player_1.move(1)
        elif pressed_key == ord('w'):
            self._player_1.move(-1)

        if pressed_key == ord('k'):
            self._player_2.move(1)
        elif pressed_key == ord('i'):
            self._player_2.move(-1)

        self._ball.step(self._player_1, self._player_2)


run(Game())
