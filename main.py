import time
import curses
import asyncio
import random
from itertools import cycle

import curses_tools
from curses_tools import draw_frame, read_controls, get_frame_size
from explosion import explode
from fire_animation import fire
import globals

from game_scenario import get_garbage_delay_tics, PHRASES
from garbage_animation import fly_garbage
from physics import update_speed

TIC_TIMEOUT = 0.1
STARS_AMOUNT = 15
OFFSET_TICS = 10
GARBAGE_OFFSET_TICS = 30
TICS_PER_YEAR = 15

STARS_DIM_DURATION = 20
STARS_NORMAL_DURATION = 3
STARS_BOLD_DURATION = 5

GUN_ACQUIRE_YEAR = 1970

TEXT_WINDOW_WIDTH = 25
BORDER_WIDTH = 1


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
    globals.row_speed, globals.col_speed = update_speed(
        globals.row_speed, globals.col_speed, row_offset, col_offset
    )
    row, col = row + globals.row_speed, col + globals.col_speed
    max_row, max_col = _get_max_xy(canvas)
    frame_h, frame_w = get_frame_size(frame)
    row, col = max(row, 0 + BORDER_WIDTH), max(col, 0 + BORDER_WIDTH)
    row, col = min(row, max_row - frame_h), min(col, max_col - frame_w)
    return row, col


async def game_over(canvas):
    max_row, max_col = _get_max_xy(canvas)
    with open("animations/game_over.txt", "r") as my_file:
        game_over_frame_1 = my_file.read()
    row_size, col_size = curses_tools.get_frame_size(game_over_frame_1)
    while True:
        draw_frame(
            canvas,
            (max_row - row_size) / 2,
            (max_col - col_size) / 2,
            game_over_frame_1,
        )
        await asyncio.sleep(0)


async def run_spaceship(canvas, start_row, start_column, frames):
    row, col = start_row, start_column
    row_size, col_size = curses_tools.get_frame_size(frames[0])
    for frame in cycle(frames):
        draw_frame(canvas, row, col, frame, negative=False)
        row_offset, col_offset, space_pressed = read_controls(canvas)
        if space_pressed and globals.year >= GUN_ACQUIRE_YEAR:
            globals.coroutines.append(fire(canvas, row, col))
        prev_row, prev_col = row, col
        row, col = _calculate_next_coordinates(
            canvas, frame, row, row_offset, col, col_offset
        )
        await asyncio.sleep(0)
        draw_frame(canvas, prev_row, prev_col, frame, negative=True)
        for obstacle in globals.obstacles:
            if obstacle.has_collision(row, col):
                globals.obstacles_in_last_collisions.append(obstacle)
                globals.coroutines.append(
                    explode(
                        canvas,
                        row + row_size / 2,
                        col + col_size / 2,
                    )
                )
                globals.coroutines.append(game_over(canvas))
                return


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
        if tics := get_garbage_delay_tics(globals.year):
            await countdown_tics(tics)
            globals.coroutines.append(
                fly_garbage(
                    canvas,
                    column=random.randint(BORDER_WIDTH, max_col - BORDER_WIDTH),
                    garbage_frame=frames[random.randint(0, len(frames) - 1)],
                )
            )
        else:
            await countdown_tics(TICS_PER_YEAR)


async def show_year(canvas):
    """render text"""
    while True:
        text = f"Year: {globals.year} {PHRASES.get(globals.year, '')}"
        draw_frame(canvas, 0, 0, text)
        await countdown_tics(TICS_PER_YEAR)
        draw_frame(canvas, 0, 0, text, negative=True)


def draw(canvas):
    current_tick = 0
    canvas.nodelay(True)
    canvas.border()
    max_row, max_col = _get_max_xy(canvas)

    text_window = canvas.derwin(1, TEXT_WINDOW_WIDTH, max_row - 1, max_col // 2)

    with open("animations/rocket_frame_1.txt", "r") as my_file:
        rocket_frame_1 = my_file.read()
    with open("animations/rocket_frame_2.txt", "r") as my_file:
        rocket_frame_2 = my_file.read()
    rocket_frames = [rocket_frame_1, rocket_frame_1, rocket_frame_2, rocket_frame_2]

    globals.coroutines.append(show_year(text_window))

    for i in range(STARS_AMOUNT):
        globals.coroutines.append(
            blink(
                canvas,
                random.randint(BORDER_WIDTH, max_row - BORDER_WIDTH),
                random.randint(BORDER_WIDTH, max_col - BORDER_WIDTH),
                symbol=random.choice(["*", ":", ".", "+"]),
                offset_tics=random.randint(0, OFFSET_TICS),
            )
        )
    globals.coroutines.append(
        run_spaceship(canvas, max_row / 2, max_col / 2, rocket_frames)
    )
    globals.coroutines.append(fill_orbit_with_garbage(canvas))
    while True:
        for coroutine in globals.coroutines.copy():
            try:
                coroutine.send(None)
            except StopIteration:
                globals.coroutines.remove(coroutine)
        time.sleep(TIC_TIMEOUT)
        current_tick += 1
        if current_tick >= TICS_PER_YEAR:
            globals.year += 1
            current_tick = 0
        canvas.refresh()


if __name__ == "__main__":
    curses.update_lines_cols()
    curses.wrapper(draw)
    curses.curs_set(False)
