from flask import Flask
import logging
import os
logging.getLogger(__name__).addHandler(logging.NullHandler())
logging.basicConfig(level=os.environ.get("LOGLEVEL", "INFO"))
# logging.basicConfig(filename='/tmp/fono.log', level=logging.INFO)
logger = logging.getLogger(__name__)
logger.info ('Started')


# from fono import config
from flask_bootstrap import Bootstrap

app = Flask(__name__)
# app.config.from_object(Config)

bootstrap = Bootstrap (app)

from . import routes
