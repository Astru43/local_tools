from io import TextIOWrapper
import sys
import getopt
import re

Time = str
Date = str
Hours = float


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


DayHourTuple = tuple[Time, Hours, Task]
DayHours = tuple[Date, list[DayHourTuple]]


class Week:
    week: str
    days: list[DayHours]
    __currentDate = -1

    def __init__(self, week: str) -> None:
        self.week = week
        self.days = []

    def addDate(self, date: Date):
        self.__currentDate += 1
        self.days.append((date, []))

    def addHours(self, time: Time, hours: float):
        day_hours = self.days[self.__currentDate][1]
        day_hours.append((time, hours, Task()))

    def total(self):
        return sum(hour for _, dayHours in self.days for _, hour, _ in dayHours)

    def __str__(self) -> str:
        def printOddEven(str: str, odd: bool, end: str | None = '\n'):
            return (f"{colors.DIMM if not odd else ''}{str}{colors.ENDC}{end}")

        val = 0.0
        ret = (f"{colors.HEADER}{self.week}:{colors.ENDC}\n")
        for idx, (date, dayHours) in enumerate(self.days):
            odd = idx % 2
            ret += printOddEven(f"{date:}", odd, end='')
            for time, hour, task in dayHours:
                ret += printOddEven(f"\t{time}\t{hour}\t{task}", odd)
                val += hour
        ret += '\n' if (val <= 0) else ''
        ret += f"{colors.CYAN}Total:\t\t{val:g}h{colors.ENDC}\n\n"
        return ret


WeekHours = list[Week]


class colors:
    HEADER = "\033[93m"
    CYAN = "\033[96m"
    RED = "\033[31m"
    ERROR = RED
    ENDC = "\033[0m"
    BOLD = "\033[1m"
    DIMM = "\033[2m"


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


def handleOptions():
    try:
        opts = getopt.getopt(sys.argv[1:], "lw:W:", ["csv", "week=", 'weeks='])
    except getopt.GetoptError as e:
        print(f"{colors.ERROR}{e.msg}{colors.ENDC}")
        raise RuntimeError()

    writeCSV = False
    latestOnly = False
    selWeek = None
    selWeeks = None
    for opt in opts[0]:
        match opt:
            case ("--csv", _):
                writeCSV = True
            case ("-l", _):
                latestOnly = True
            case ("--week" | "-w", w):
                if not re.match("[0123]?\d\.[01]?\d(?:\.\d{2}(?:\d\d)?)?(?!\d)+", w):
                    print(
                        f"{colors.ERROR}{w} is not valid start date of week{colors.ENDC}")
                    raise RuntimeError()
                else:
                    selWeek = next(
                        (week for week in weeks if w in week.week), None)
            case ("--weeks" | "-W", w):
                if not re.match("\d", w):
                    print(f"{colors.ERROR}No valid range given{colors.ENDC}")
                    raise RuntimeError()
                else:
                    selWeeks = weeks[-int(w):]
        if selWeek and selWeeks:
            print(f"{colors.ERROR}Week and weeks can't be used together{colors.ENDC}")
            raise RuntimeError()
    return (writeCSV, latestOnly, selWeek, selWeeks)


week = re.compile(
    "^## (Week +\d\d?\.\d\d?(?:\.\d\d)?)(?: *- *\d\d?\.\d\d?(?:\.\d\d)?)")
dayTime = re.compile(
    "(?:(?:(\d\d?\.\d\d?(?!\d*h)) )?(\d\d?:\d\d?))|(?:\|\s+?(\d+\s*?-\s*?\d+)\s+?\|)")
hours = re.compile("(\d(\.\d*)?)h")
task = re.compile("(^\d\. .*)|\| *(?:(\d)\.|(meet)|(\.{3})) *\|")


if __name__ == "__main__":
    weeks = WeekHours()
    with open(".\TIME_USAGE.md") as file:
        for line in file:
            res = week.search(line)
            if res:
                weeks.append(Week(res.group(1)))
                continue

            curWeek = weeks[len(weeks) - 1] if len(weeks) > 0 else None
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
                        [task.setTask(taskStr[3:]) for _, dayHours in _week.days for _,
                            _, task in dayHours if task.task and taskStr.startswith(task.task)]
                elif taskNum := res.group(2):
                    dayHours = curWeek.days[len(curWeek.days) - 1][1]
                    dayHours[len(dayHours) - 1][2].setTask(taskNum)
                elif taskMeet := res.group(3):
                    dayHours = curWeek.days[len(curWeek.days) - 1][1]
                    dayHours[len(dayHours) - 1][2].setTask("Meeting")
                elif taskCon := res.group(4):
                    dayHours = curWeek.days[len(curWeek.days) - 1][1]
                    dayHours[len(dayHours) - 1][2].setTask(taskCon)

    if len(weeks) > 0:
        writeTotals(weeks)

    writeCSV = None
    latestOnly = None
    selWeek = None
    selWeeks = None
    if len(sys.argv) >= 2:
        try:
            (writeCSV, latestOnly, selWeek, selWeeks) = handleOptions()
        except RuntimeError:
            exit(-1)

    print()
    if latestOnly:
        print(weeks[-1])
    elif selWeeks:
        total = 0
        for week in selWeeks:
            total += week.total()
            print(week)
        print(f"Cycle total:\t{total}h")
    elif selWeek:
        print(selWeek)
    else:
        print("Totals:\n")
        for week in weeks:
            print(week)

    if writeCSV:
        if selWeek:
            writeToCSV([selWeek])
        elif selWeeks:
            writeToCSV(selWeeks)
        else:
            writeToCSV(weeks)
