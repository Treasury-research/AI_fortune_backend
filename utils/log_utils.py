import logging
import os
import json
LOG_FILE = os.path.join(os.path.split(os.path.realpath(__file__))[0],'../logs/run.log')

class JsonFormatter(logging.Formatter):
        def format(self, record):
                message = record.msg
                if not isinstance(message, str):
                        message = str(message)
                try:
                        json.loads(message)
                        return message
                except ValueError:
                        pass

                log_record = {
                        'time': self.formatTime(record),
                        'name': record.name,
                        'levelname': record.levelname,
                        'message': record.getMessage(),
                }
                return json.dumps(log_record,ensure_ascii=False)

handler = logging.FileHandler(LOG_FILE)
handler.setLevel(logging.INFO)
handler.setFormatter(JsonFormatter())

steam_handler = logging.StreamHandler()
steam_handler.setLevel(logging.INFO)
steam_handler.setFormatter(JsonFormatter())


logging.basicConfig(level=logging.INFO, handlers=[handler,steam_handler])
logger = logging.getLogger(__name__)


