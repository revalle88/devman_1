import time
import curses
import asyncio

TIC_TIMEOUT = 0.1


async def blink(canvas, row, column, symbol='*'):
    while True:
        for _ in range(20):
            canvas.addstr(row, column, symbol, curses.A_DIM)
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


def draw(canvas):
    row, column = (5, 20)
    canvas.border()
    coroutines = [blink(canvas, row, column + i) for i in range(5)]
    while True:
        try:
            for coroutine in coroutines:
                coroutine.send(None)
            time.sleep(TIC_TIMEOUT)
            canvas.refresh()
        except StopIteration:
            break


if __name__ == '__main__':
    curses.update_lines_cols()
    curses.wrapper(draw)
    curses.curs_set(False)
