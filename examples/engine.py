"""This is the core of the pong example. You can read through it if you'd
like, but it's pretty boring. I try to shove as much boring game logic into
here so that the interactive demos can focus on what matters--interactive!
"""

import curses
import random
import math
import asyncio


class Sprite:
    def __init__(self, screen):
        self._screen = screen
        self._screen_height, self._screen_width = screen.getmaxyx()

    def _draw_rect(self, x, y, width, height, char):
        for dx in range(width):
            for dy in range(height):
                self._screen.insch(y + dy, x + dx, char)

    def draw(self):
        raise NotImplementedError()


class Paddle(Sprite):
    def __init__(self, screen, x, height, width=1):
        super(Paddle, self).__init__(screen)
        self.x = x
        self.y = (self._screen_height - height) // 2
        self.height = height
        self.width = width

    def move(self, amount):
        self.y = min(self._screen_height - self.height, max(0, self.y + amount))

    def draw(self):
        self._draw_rect(self.x, self.y, self.width, self.height, 'x')


class Ball(Sprite):
    def __init__(self, screen, speed_per_frame=2, size=1):
        super(Ball, self).__init__(screen)
        self._size = size
        self._speed = speed_per_frame
        self._reset()

    def _reset(self):
        self.x = self._screen_width // 2
        self.y = self._screen_height // 2
        self._angle = 0
        if random.random() > 0.5:
            self._angle = math.pi

    def _try_bounce(self, paddles):
        """Checks if the ball is bouncing against and of the padds and, if so,
        changes the angle to bounce off them.
        """
        for paddle in paddles:
            if self.x > paddle.x + paddle.width or self.x + self._size < paddle.x:
                continue
            if self.y > paddle.y + paddle.height or self.y < paddle.y:
                continue

            # Set the angle to be the angle from the paddle center to the ball
            dy = (self.y + self._size / 2) - (paddle.y + paddle.height / 2)
            dx = (self.x + self._size / 2) - (paddle.x + paddle.width / 2)
            self._angle = math.atan2(dy, dx)

    def step(self, *paddles):
        self._try_bounce(paddles)
        self.x += math.cos(self._angle) * self._speed
        self.y += math.sin(self._angle) * self._speed

        if self.y < 0 or self.y > self._screen_height - 1:
            self.y = max(0, min(self._screen_height - self._size, self.y))
            self._angle = -self._angle

        if self.x < 0 or self.x > self._screen_width - self._size:
            self._reset()

    def draw(self):
        self._draw_rect(round(self.x), round(self.y), self._size, self._size, 'o')


class QuitException(Exception):
    pass


class BaseGame:
    def __init__(self):
        self._screen = curses.initscr()
        self._screen_height, self._screen_width = self._screen.getmaxyx()
        self._ball = Ball(self._screen)
        self._sprites = [self._ball]
        self._fps = 15
        self._running = True

    def _create_paddle(self, **kwargs):
        paddle = Paddle(screen=self._screen, **kwargs)
        self._sprites.append(paddle)
        return paddle

    def update(self, pressed_key=None):
        raise NotImplementedError()

    def fatal_error(self, e):
        self._running = False
        raise e

    async def setup(self):
        pass

    async def loop(self):
        await self.setup()

        while self._running:
            self._screen.timeout(1)
            pressed_key = self._screen.getch()
            if pressed_key == ord('q'):
                raise QuitException()

            self.update(pressed_key)

            self._screen.clear()
            drawees = sorted(self._sprites, key=lambda o: o.x)
            for d in drawees:
                d.draw()
            self._screen.refresh()
            curses.flushinp()

            await asyncio.sleep(1 / self._fps)


def run(game):
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(game.loop())
    except (KeyboardInterrupt, QuitException):
        curses.endwin()
    finally:
        loop.stop()
