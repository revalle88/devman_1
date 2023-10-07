import curses_tools
from curses_tools import draw_frame
import asyncio

from explosion import explode
from obstacles import Obstacle


async def fly_garbage(
    canvas,
    column,
    garbage_frame,
    obstacles,
    obstacles_in_last_collisions,
    coroutines,
    speed=0.5,
):
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
        if obstacle in obstacles_in_last_collisions:
            coroutines.append(
                explode(
                    canvas,
                    row + obstacle.rows_size / 2,
                    column + obstacle.columns_size / 2,
                )
            )
            obstacles.remove(obstacle)
            obstacles_in_last_collisions.remove(obstacle)
            del obstacle
            return
        row += speed
        obstacle.row = row
    del obstacle
