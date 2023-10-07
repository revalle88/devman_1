import time
import curses
import asyncio
import random
from itertools import cycle

from curses_tools import draw_frame, read_controls, get_frame_size
from fire_animation import fire
from garbage_animation import fly_garbage
from obstacles import show_obstacles
from physics import update_speed

TIC_TIMEOUT = 0.1
STARS_AMOUNT = 15
OFFSET_TICS = 10
BORDER_WIDTH = 1
GARBAGE_OFFSET_TICS = 30

STARS_DIM_DURATION = 20
STARS_NORMAL_DURATION = 3
STARS_BOLD_DURATION = 5

coroutines = []
obstacles = []
row_speed = col_speed = 0


async def countdown_tics(tics):
    for _ in range(tics):
        await asyncio.sleep(0)


async def blink(canvas, row, column, symbol="*", offset_tics=0):
    while True:
        canvas.addstr(row, column, symbol, curses.A_DIM)
        await countdown_tics(STARS_DIM_DURATION)
        await countdown_tics(offset_tics)

        canvas.addstr(row, column, symbol)
        await countdown_tics(STARS_NORMAL_DURATION)

        canvas.addstr(row, column, symbol, curses.A_BOLD)
        await countdown_tics(STARS_BOLD_DURATION)

        canvas.addstr(row, column, symbol)
        await countdown_tics(STARS_NORMAL_DURATION)


def _get_max_xy(canvas):
    """
    Метод window.getmaxyx(), несмотря на своё название, возвращает
    не координаты крайней ячейке, а ширину и высоту окна. Они всегда будут на единицу больше,
    чем координаты крайней ячейки из-за того, что нумерация начинается с нуля.
    """
    return (i - 1 for i in canvas.getmaxyx())


def _calculate_next_coordinates(canvas, frame, row, row_offset, col, col_offset):
    global row_speed
    global col_speed
    row_speed, col_speed = update_speed(row_speed, col_speed, row_offset, col_offset)
    row, col = row + row_speed, col + col_speed
    max_row, max_col = _get_max_xy(canvas)
    frame_h, frame_w = get_frame_size(frame)
    row, col = max(row, 0 + BORDER_WIDTH), max(col, 0 + BORDER_WIDTH)
    row, col = min(row, max_row - frame_h), min(col, max_col - frame_w)
    return row, col


async def draw_rocket(canvas, start_row, start_column, frames):
    row, col = start_row, start_column
    for frame in cycle(frames):
        draw_frame(canvas, row, col, frame, negative=False)
        row_offset, col_offset, space_pressed = read_controls(canvas)
        if space_pressed:
            coroutines.append(fire(canvas, row, col))
        prev_row, prev_col = row, col
        row, col = _calculate_next_coordinates(
            canvas, frame, row, row_offset, col, col_offset
        )
        await asyncio.sleep(0)
        draw_frame(canvas, prev_row, prev_col, frame, negative=True)


async def fill_orbit_with_garbage(canvas):
    frames = []
    max_row, max_col = _get_max_xy(canvas)

    with open("animations/garbage/duck.txt", "r") as garbage_file:
        frames.append(garbage_file.read())
    with open("animations/garbage/hubble.txt", "r") as garbage_file:
        frames.append(garbage_file.read())
    with open("animations/garbage/lamp.txt", "r") as garbage_file:
        frames.append(garbage_file.read())
    with open("animations/garbage/trash_large.txt", "r") as garbage_file:
        frames.append(garbage_file.read())
    with open("animations/garbage/trash_small.txt", "r") as garbage_file:
        frames.append(garbage_file.read())
    with open("animations/garbage/trash_x1.txt", "r") as garbage_file:
        frames.append(garbage_file.read())

    while True:
        await countdown_tics(random.randint(0, GARBAGE_OFFSET_TICS))
        coroutines.append(
            fly_garbage(
                canvas,
                column=random.randint(BORDER_WIDTH, max_col - BORDER_WIDTH),
                garbage_frame=frames[random.randint(0, len(frames) - 1)],
                obstacles=obstacles,
            )
        )


def draw(canvas):
    canvas.nodelay(True)
    canvas.border()
    max_row, max_col = _get_max_xy(canvas)
    with open("animations/rocket_frame_1.txt", "r") as my_file:
        rocket_frame_1 = my_file.read()
    with open("animations/rocket_frame_2.txt", "r") as my_file:
        rocket_frame_2 = my_file.read()
    rocket_frames = [rocket_frame_1, rocket_frame_1, rocket_frame_2, rocket_frame_2]

    for i in range(STARS_AMOUNT):
        coroutines.append(
            blink(
                canvas,
                random.randint(BORDER_WIDTH, max_row - BORDER_WIDTH),
                random.randint(BORDER_WIDTH, max_col - BORDER_WIDTH),
                symbol=random.choice(["*", ":", ".", "+"]),
                offset_tics=random.randint(0, OFFSET_TICS),
            )
        )
    coroutines.append(draw_rocket(canvas, max_row / 2, max_col / 2, rocket_frames))
    coroutines.append(fire(canvas, max_row / 2, max_col / 2))
    coroutines.append(fill_orbit_with_garbage(canvas))
    coroutines.append(show_obstacles(canvas, obstacles))
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
