import os
from time import sleep, time
import sys
import signal
from datetime import datetime, timedelta
from string import Template

align = 12


class DeltaTemplate(Template):
    delimiter = '%'


def strfdelta(fmt: str, delta: timedelta):
    d = {'D': delta.days}
    hours, rem = divmod(delta.seconds, 3600)
    minutes, seconds = divmod(rem, 60)
    d['H'] = f'{hours:02d}'
    d['M'] = f'{minutes:02d}'
    d['S'] = f'{seconds:02d}'
    return DeltaTemplate(fmt).substitute(**d)


def TimeFormat(time: float):
    return f'{datetime.fromtimestamp(time)}'


def TimeDiference(start: float, end: float):
    dstart = datetime.fromtimestamp(start)
    dend = datetime.fromtimestamp(end)
    return f'{strfdelta("%D days %H:%M:%S", dend - dstart)}'


def cleanLastLine():
    print(f'{"":{columns}}', end='\r')


def exit(signum, frame):
    cleanLastLine()
    end = time()
    print(f'{"End:":{align}}{TimeFormat(end)}')
    print(f'{"Duration:":{align}}{TimeDiference(start, end)}')
    sys.exit(0)


if __name__ == '__main__':
    start = time()
    columns, lines = os.get_terminal_size()
    print(f'{"Start:":{align}}{TimeFormat(start)}')
    signal.signal(signal.SIGINT, exit)
    while True:
        message = f'Current duration {TimeDiference(start, time())}'
        print(
            f'{message:<{columns}}',
            end='\r',
            flush=True
        )
        sleep(1)
