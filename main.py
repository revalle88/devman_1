import time
import curses
import asyncio
import random
from itertools import cycle

from curses_tools import draw_frame, read_controls, get_frame_size
from fire_animation import fire

TIC_TIMEOUT = 0.1
STARS_AMOUNT = 15
OFFSET_TICS = 10
BORDER_WIDTH = 1

STARS_DIM_DURATION = 20
STARS_NORMAL_DURATION = 3
STARS_BOLD_DURATION = 5


async def blink(canvas, row, column, symbol="*", offset_tics=0):
    while True:
        for _ in range(STARS_DIM_DURATION):
            canvas.addstr(row, column, symbol, curses.A_DIM)
            await asyncio.sleep(0)

        for _ in range(offset_tics):
            await asyncio.sleep(0)

        for _ in range(STARS_NORMAL_DURATION):
            canvas.addstr(row, column, symbol)
            await asyncio.sleep(0)

        for _ in range(STARS_BOLD_DURATION):
            canvas.addstr(row, column, symbol, curses.A_BOLD)
            await asyncio.sleep(0)

        for _ in range(STARS_NORMAL_DURATION):
            canvas.addstr(row, column, symbol)
            await asyncio.sleep(0)


def _get_max_xy(canvas):
    """
    Метод window.getmaxyx(), несмотря на своё название, возвращает
    не координаты крайней ячейке, а ширину и высоту окна. Они всегда будут на единицу больше,
    чем координаты крайней ячейки из-за того, что нумерация начинается с нуля.
    """
    return (i - 1 for i in canvas.getmaxyx())


def validate_coordinates(canvas, frame, row, col):
    max_row, max_col = _get_max_xy(canvas)
    frame_h, frame_w = get_frame_size(frame)
    if (
        row <= 0 + BORDER_WIDTH
        or col <= 0 + BORDER_WIDTH
        or row + frame_h > max_row
        or col + frame_w >= max_col
    ):
        return False
    return True


async def draw_rocket(canvas, start_row, start_column, frames):
    row, col = prev_row, prev_col = start_row, start_column
    for frame in cycle(frames):
        draw_frame(canvas, row, col, frame, negative=False)
        row_offset, col_offset, _ = read_controls(canvas)
        if validate_coordinates(canvas, frame, row + row_offset, col + col_offset):
            prev_row, prev_col = row, col
            row, col = row + row_offset, col + col_offset
        await asyncio.sleep(0)
        draw_frame(canvas, prev_row, prev_col, frame, negative=True)


def draw(canvas):
    canvas.nodelay(True)
    canvas.border()
    max_row, max_col = _get_max_xy(canvas)
    with open("animations/rocket_frame_1.txt", "r") as my_file:
        rocket_frame_1 = my_file.read()
    with open("animations/rocket_frame_2.txt", "r") as my_file:
        rocket_frame_2 = my_file.read()
    rocket_frames = [rocket_frame_1, rocket_frame_1, rocket_frame_2, rocket_frame_2]

    coroutines = [
        blink(
            canvas,
            random.randint(BORDER_WIDTH, max_row - BORDER_WIDTH),
            random.randint(BORDER_WIDTH, max_col - BORDER_WIDTH),
            symbol=random.choice(["*", ":", ".", "+"]),
            offset_tics=random.randint(0, OFFSET_TICS),
        )
        for i in range(STARS_AMOUNT)
    ]
    coroutines.append(draw_rocket(canvas, max_row / 2, max_col / 2, rocket_frames))
    coroutines.append(fire(canvas, max_row / 2, max_col / 2))
    while True:
        for coroutine in coroutines.copy():
            try:
                coroutine.send(None)
            except StopIteration:
                coroutines.remove(coroutine)
        time.sleep(TIC_TIMEOUT)
        canvas.refresh()


if __name__ == "__main__":
    curses.update_lines_cols()
    curses.wrapper(draw)
    curses.curs_set(False)
