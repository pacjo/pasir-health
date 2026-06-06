import enum


class LogLevel(enum.Enum):
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


def log(level: LogLevel, message: str):
    print(f"[{level.value}] {message}")


# helpers
def logd(message: str):
    log(LogLevel.DEBUG, message)


def logi(message: str):
    log(LogLevel.INFO, message)


def logw(message: str):
    log(LogLevel.WARNING, message)


def loge(message: str):
    log(LogLevel.ERROR, message)
