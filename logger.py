import datetime

class Logger:
    @staticmethod
    def _log(level, message, **kwargs):
        timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        print(f"{timestamp} {level}: {message}")
        if 'exc_info' in kwargs and kwargs['exc_info']:
            import traceback
            traceback.print_exc()

    @classmethod
    def info(cls, message, **kwargs):
        cls._log('INFO', message, **kwargs)

    @classmethod
    def warning(cls, message, **kwargs):
        cls._log('WARNING', message, **kwargs)

    @classmethod
    def error(cls, message, **kwargs):
        cls._log('ERROR', message, **kwargs)