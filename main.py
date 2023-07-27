import time
import curses
import asyncio
import random
from itertools import cycle

from curses_tools import draw_frame, read_controls
from fire_animation import fire

TIC_TIMEOUT = 0.1
STARS_AMOUNT = 1


async def blink(canvas, row, column, symbol='*'):
    while True:
        for _ in range(20):
            canvas.addstr(row, column, symbol, curses.A_DIM)
            await asyncio.sleep(0)

        for _ in range(random.randint(0, 100)):
            await asyncio.sleep(0)

        for _ in range(3):
            canvas.addstr(row, column, symbol)
            await asyncio.sleep(0)

        for _ in range(5):
            canvas.addstr(row, column, symbol, curses.A_BOLD)
            await asyncio.sleep(0)

        for _ in range(3):
            canvas.addstr(row, column, symbol)
            await asyncio.sleep(0)


async def draw_rocket(canvas, start_row, start_column):
    canvas.nodelay(True)
    with open("animations/rocket_frame_1.txt", "r") as my_file:
        rocket_frame_1 = my_file.read()
    with open("animations/rocket_frame_2.txt", "r") as my_file:
        rocket_frame_2 = my_file.read()
    h, w = start_row, start_column
    for frame in cycle([rocket_frame_1, rocket_frame_2]):
        draw_frame(canvas, h, w, frame, negative=False)
        await asyncio.sleep(0)
        draw_frame(canvas, h, w, frame, negative=True)
        rocket_h, rocket_w, _ = read_controls(canvas)
        h, w = h + rocket_h, w + rocket_w


def draw(canvas):
    canvas.nodelay(True)
    canvas.border()
    h, w = canvas.getmaxyx()
    coroutines = [
        blink(
            canvas,
            random.randint(1, h - 1),
            random.randint(1, w - 1),
            symbol=random.choice(["*", ":", ".", "+"])
        )
        for i in range(STARS_AMOUNT)
    ]
    coroutines.append(draw_rocket(canvas, h / 2, w / 2))
    coroutines.append(fire(canvas, h / 2, w / 2))
    while True:
        for coroutine in coroutines.copy():
            try:
                coroutine.send(None)
            except StopIteration:
                coroutines.remove(coroutine)
        time.sleep(TIC_TIMEOUT)
        canvas.refresh()


if __name__ == '__main__':
    curses.update_lines_cols()
    curses.wrapper(draw)
    curses.curs_set(False)
