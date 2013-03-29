from input.singleton_decorator import singleton

@singleton
class LoggingSystem(object):
    def __init__(self):
        from sys import platform
        from os import environ
        #TODO: Check $TERM

        if platform in ["linux", "linux2", "darwin"]:
            self._debug_template = "\033[95m%s\033[0m" #Purple
            self._notice_template = "\033[94m%s\033[0m" #Blue
            self._warning_template = "\033[91m%s\033[0m" #Red
            self._fatal_error_template = "\033[101m%s\033[0m" #Red on dark gray
            self._error_template = "\033[100m\033[91m%s\033[0m" #White on red
        else:
            self._debug_template = "%s"
            self._notice_template = "%s"
            self._warning_template = "%s"
            self._fatal_error_template = "%s"
            self._error_template = "%s"

        self._debug_template %= "[DEBUG] %s"
        self._notice_template %= "[NOTICE] %s"
        self._warning_template %= "[WARNING] %s"
        self._fatal_error_template %= "[FATAL ERROR] %s"
        self._error_template %= "[ERROR] %s"


    def fatal_error(self, message):
        print self._fatal_error_template % message

    def error(self, message):
        print self._error_template % message

    def warning(self, message):
        print self._warning_template % message

    def notice(self, message):
        print self._notice_template % message

    def debug(self, message):
        print self._debug_template % message

logging = LoggingSystem()