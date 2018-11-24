# main.py is for running from the command line,
# rather then as a systemd service
#
# Alternatively: gunicorn --bind 0.0.0.0:8000 fono:app
#
# or: FLASK_APP=fono/__init__.py flask run
# in this case it runs on http://127.0.0.1:5000/
#

# run on the local network
# use hostname -I to find IP address on local network
from fono import *
if __name__ == "__main__":
    app.run (host="0.0.0.0", port=8000)
