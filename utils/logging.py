import datetime

LOGFILE = "console.log"

def log(message, level="INFO"):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{level}] {timestamp} - {message}\n"
    print(line.strip())
    with open(LOGFILE, "a") as f:
        f.write(line)

def get_logs():
    try:
        with open(LOGFILE, "r") as f:
            return f.read()
    except FileNotFoundError:
        return "Console initialized...\n"
