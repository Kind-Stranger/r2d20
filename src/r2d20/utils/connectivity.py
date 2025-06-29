import json
import logging
import os
import requests

logger = logging.getLogger(__name__)

DEFAULT_URL = os.getenv('LLAMA_HOST')
DEFAULT_MODEL = os.getenv('LLAMA_DEFAULT_MODEL')


class LLMSessionHandler:
    def __init__(self, url: str = None, model: str = None):
        self.url = url or DEFAULT_URL
        self.model = model or DEFAULT_MODEL
        self.session: requests.Session = None

    def __enter__(self):
        logger.debug(f"Starting stream with model {self.model}.")
        self.session = requests.Session()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        if exc_type:
            logger.error(f"An error occurred: {exc_value}")
        else:
            self.session.close()

    def init_session(self):
        self.session = requests.Session()

    def send_prompt(self, prompt: str, stream=False):
        logger.debug(f"Sending prompt: {prompt}")
        body = {
            "model": self.model,
            "prompt": prompt,
            "stream": stream,
        }
        with self.session.post(self.url, json=body, stream=stream) as res:
            res.raise_for_status()
            if stream:
                self.stream_output(res)
            else:
                # If not streaming, we expect a single response
                json_response: dict = res.json()
                res = json_response.get('response', 'ERROR: No response field found').strip()
                return res

    def stream_output(self, res: requests.Response):
        for line in res.iter_lines():
            line: bytes
            if not line: 
                continue

            decoded_line = line.decode('utf-8')
            json_line: dict = json.loads(decoded_line)
            yield json_line.get('response', 'ERROR: No response field found')
