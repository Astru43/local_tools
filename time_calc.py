from __future__ import annotations

import getopt
import re
import sys
from dataclasses import dataclass
from io import TextIOWrapper
from typing import Any, NamedTuple


class colors:
    HEADER = "\033[93m"
    CYAN = "\033[96m"
    RED = "\033[31m"
    ERROR = RED
    ENDC = "\033[0m"
    BOLD = "\033[1m"
    DIMM = "\033[2m"


def Error(val: str):
    return f"{colors.ERROR}{val}{colors.ENDC}"


class Task:
    task: str | None

    def __init__(self) -> None:
        self.task = None

    def setTask(self, task: str):
        if not task.isnumeric():
            self.task = task
        elif self.task == None:
            self.task = task

    def __str__(self) -> str:
        if self.task:
            return self.task
        else:
            return ""


Date = str
# DayHours = list[tuple[str, float, Task]]


class Hours(NamedTuple):
    time: str
    hours: float
    task: Task


def address(val: Any):
    print(hex(id(val)))


def splitTask(task: Task):
    strTask = str(task)
    if len(strTask) <= 80:
        return strTask
    lastSpace = strTask[:80].rfind(' ')
    if lastSpace != -1:
        return [strTask[:lastSpace], strTask[lastSpace+1:]]
    else:
        return strTask


@dataclass
class Day(tuple[Date, list[Hours]]):

    # __slots__ = 'date', 'hours'
    date: Date
    hours: list[Hours]

    def __init__(self, date: Date, hours: list[Hours] | None = None) -> None:
        self.date = date
        self.hours = hours if hours else []

    def addHours(self, time: str, hours: float, task: Task | None = None):
        self.hours.append(Hours(time, hours, task if task else Task()))

    def __getitem__(self, index):
        return (self.date, self.hours)[index]

    def __iter__(self):
        yield self.date
        yield self.hours
        return


class Week:
    week: str
    days: list[Day]

    def __init__(self, week: str) -> None:
        self.week = week
        self.days = []

    def addDate(self, date: Date):
        self.days.append(Day(date))

    def addHours(self, time: str, hours: float):
        self.days[-1].addHours(time, hours)

    def total(self):
        return sum(hour for _, dayHours in self.days for _, hour, _ in dayHours)

    def __str__(self) -> str:
        def printOddEven(str: str, odd: int | bool, end: str | None = '\n'):
            return (f"{colors.DIMM if not odd else ''}{str}{colors.ENDC}{end}")

        val = 0.0
        ret = (f"{colors.HEADER}{self.week}:{colors.ENDC}\n")
        for idx, (date, dayHours) in enumerate(self.days):
            odd = idx % 2
            ret += printOddEven(f"{date:}", odd, end='')
            for time, hour, task in dayHours:
                sTask = splitTask(task)
                if isinstance(sTask, list):
                    ret += printOddEven(f"\t{time}\t{hour}\t{sTask[0]}", odd)
                    for s in sTask[1:]:
                        ret += printOddEven(
                            f"\t{' ':{len(time)}}\t{' ':{len(str(hour))}}\t{s}", odd)
                else:
                    ret += printOddEven(f"\t{time}\t{hour}\t{sTask}", odd)
                val += hour
        ret += '\n' if (val <= 0) else ''
        ret += f"{colors.CYAN}Total:\t\t{val:g}h{colors.ENDC}\n\n"
        return ret


WeekHours = list[Week]


def writeTotals(weeks: WeekHours):
    def writeWeeks(file: TextIOWrapper):
        file.write(f"| {'Week':10} | Total |\n")
        file.write(f"| {'-'*10} | ----- |\n")
        for week in weeks:
            file.write(f"| {week.week:10} | {week.total():<5g} |\n")

    try:
        with open("TOTAL.md", "x") as file:
            print("Created TOTAL.md")
            writeWeeks(file)
            file.close()
    except FileExistsError:
        with open("TOTAL.md", "w") as file:
            print("File TOTAL.md exists, rewriting")
            writeWeeks(file)
            file.close()


def writeToCSV(weeks: WeekHours):
    def write_to(file):
        for week in weeks:
            file.write(week.week + "\n")
            file.write("Date,Hours,Task\n")
            for (date, dayHours) in week.days:
                for time, hour, task in dayHours:
                    file.write(f"{date} {time}")
                    file.write(f",\"{str(hour).replace('.', ',')}\"")
                    file.write(f",\"{task}\"\n")
            file.write(f"Total, \"{str(week.total()).replace('.', ',')}\"\n")

    try:
        with open("time.csv", "x") as file:
            print("Created time.csv")
            write_to(file)
    except FileExistsError:
        with open("time.csv", "w") as file:
            print("File time.csv exists, rewriting")
            write_to(file)


def cleanFiles():
    import os
    if os.path.isfile("time.csv"):
        os.remove("time.csv")
    if os.path.isfile("TOTAL.md"):
        os.remove("TOTAL.md")
    exit(0)


def handleOptions():
    def checkWeekAndWeeks(opts: dict):
        week = any(val in opts for val in ["-w", "--week"])
        weeks = any(val in opts for val in ["-W", "--weeks"])
        return week and weeks

    try:
        opts = getopt.getopt(sys.argv[1:], "lw:W:", [
                             "clean", "csv", "week=", 'weeks='])
    except getopt.GetoptError as e:
        print(Error(f"{e.msg}"))
        raise RuntimeError()

    writeCSV = False
    latestOnly = False
    selWeeks = None

    if checkWeekAndWeeks(dict(opts[0])):
        print(Error("Week and weeks can't be used together"))
        raise RuntimeError()

    for opt in opts[0]:
        match opt:
            case ("--clean", _):
                return cleanFiles()
            case ("--csv", _):
                writeCSV = True
            case ("-l", _):
                latestOnly = True
            case ("--week" | "-w", w):
                if not re.match(r"[0123]?\d\.[01]?\d(?:\.\d{2}(?:\d\d)?)?(?!\d)+", w):
                    print(Error(f"{w} is not valid start date of week"))
                    raise RuntimeError()
                else:
                    selWeeks = [week for week in weeks if w in week.week]
            case ("--weeks" | "-W", w):
                if not re.match(r"\d", w):
                    print(Error("No valid range given"))
                    raise RuntimeError()
                else:
                    selWeeks = weeks[-int(w):]
    return (writeCSV, latestOnly, selWeeks)


week = re.compile(
    r"^## (Week +\d\d?\.\d\d?(?:\.\d\d)?)(?: *- *\d\d?\.\d\d?(?:\.\d\d)?)")
dayTime = re.compile(
    r"(?:(?:(\d\d?\.\d\d?(?!\d*h)) )?(\d\d?:\d\d?))|(?:\|\s+?(\d+\s*?-\s*?\d+)\s+?\|)")
hours = re.compile(r"(\d(\.\d*)?)h")
task = re.compile(r"(^\d+\. .*)|\| *(?:(\d+)\.|(meet)|(\.{3})) *\|")


if __name__ == "__main__":
    weeks = WeekHours()
    with open("./TIME_USAGE.md") as file:
        for line in file:
            res = week.search(line)
            if res:
                weeks.append(Week(res.group(1)))
                continue

            curWeek = weeks[-1] if weeks else None
            if not curWeek:
                continue
            res = dayTime.search(line)
            time = None
            if res:
                if res.group(1):
                    curWeek.addDate(res.group(1))
                elif res.group(3):
                    curWeek.addDate(res.group(3))
                time = res.group(2) if not res.group(3) else "*"

            res = hours.search(line)
            if res and time:
                curWeek.addHours(time, float(res.group(1)))
            elif time:
                curWeek.addHours(time, 0)
            res = task.search(line)
            if res:
                if taskStr := res.group(1):
                    for _week in weeks:
                        [task.setTask(taskStr[len(task.task) + 2:]) for _, dayHours in _week.days for _,
                            _, task in dayHours if task.task and taskStr.startswith(task.task)]
                elif taskNum := res.group(2):
                    dayHours = curWeek.days[-1].hours
                    dayHours[-1].task.setTask(taskNum)
                elif taskMeet := res.group(3):
                    dayHours = curWeek.days[-1].hours
                    dayHours[-1].task.setTask("Meeting")
                elif taskCon := res.group(4):
                    dayHours = curWeek.days[-1].hours
                    dayHours[-1].task.setTask(taskCon)

    writeCSV = None
    latestOnly = None
    selWeeks = None
    if len(sys.argv) >= 2:
        try:
            (writeCSV, latestOnly, selWeeks) = handleOptions()
        except RuntimeError:
            exit(-1)

    if len(weeks) > 0:
        writeTotals(weeks)

    print()
    if latestOnly:
        print(weeks[-1])
    elif selWeeks:
        total = 0
        for week in selWeeks:
            total += week.total()
            print(week)
        print(f"Cycle total:\t{total}h")
    else:
        print("Totals:\n")
        for week in weeks:
            print(week)

    if writeCSV:
        if latestOnly:
            writeToCSV(weeks[-1:])
        if selWeeks:
            writeToCSV(selWeeks)
        else:
            writeToCSV(weeks)
