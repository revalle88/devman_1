import curses_tools
from curses_tools import draw_frame
import asyncio

from obstacles import Obstacle


async def fly_garbage(canvas, column, garbage_frame, obstacles, speed=0.5):
    """Animate garbage, flying from top to bottom. Сolumn position will stay same, as specified on start."""
    rows_number, columns_number = canvas.getmaxyx()
    row_size, col_size = curses_tools.get_frame_size(garbage_frame)
    obstacle = Obstacle(0, column, row_size, col_size)
    obstacles.append(obstacle)

    column = max(column, 0)
    column = min(column, columns_number - 1)

    row = 0

    while row < rows_number:
        draw_frame(canvas, row, column, garbage_frame)
        await asyncio.sleep(0)
        draw_frame(canvas, row, column, garbage_frame, negative=True)
        row += speed
        obstacle.row = row
    del obstacle
