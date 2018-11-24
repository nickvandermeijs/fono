import flask
import logging
from flask import url_for
from fono import app
from fono import mplayer
from time import sleep

import signal, os

logger = logging.getLogger(__name__)
logger.info ('routes started')

# The 'Stations' class will contain the list of selectable stations
# Those are added below. The first station is Spotify Connect, which
# is added in the __init__ method. If spotify connect is not
# available, that line can be commented out.
# 
# For updating the stations list: see below the instantiation of a Stations
# object.

class Stations (object):
    def __init__ (self):
        self.stations = []
        self.urls = {}
        # don't run subprocesses when debugging
        # (because doesn't work correctly since two threads will be started)
        self.mplayer = mplayer.Mplayer (mock=app.debug)
        self.muted = False
        self.selected = "none"
        # uncomment next line if spotify connect (via raspotify) is not available
        self.add ("Spotify Connect", "mute")

    # preparation for adding a physical button interface.
    def handler (self, signum, frame):
        logger.info ("signal: %d" % signum)
        self.play ("Arrow Classic Rock")

    def start (self):
        s = self.stations[1]
        self.selected = s
        self.mplayer.start (self.urls[s])

    def print (self):
        for s in self.stations:
            print (s, self.urls[s])

    def add (self, name, url = None):
        self.stations.append (name)
        self.urls[name] = url

    def load (self, url):
        if url.endswith (".pls"):
            self.mplayer.send_cmd ("loadlist", url)
        else:
            self.mplayer.send_cmd ("loadfile", url)

    def play (self, station):
        logger.debug ("routes play %s", station)

        self.selected = station
        url = self.urls[station]

        logger.info ("selected %s via %s", station, url)

        if url == "mute":
            self.muted = True
            self.mplayer.suspend ()
            return

        if self.muted:
            self.mplayer.resume ()
            self.muted = False

        logger.debug ("should be playing %s via %s", station, url)
        self.mplayer.play (url)


    def send_cmd(self, *args):
        cmd = " ".join(args)
        logger.debug ("send_cmd sending: %s", cmd)
        with open(self.fifo_path, 'w') as sock:
            sock.write("%s\n" % cmd)
            sock.flush()
        if cmd == 'quit':
            self.remove_fifo()
        return self
        


    def list (self):
        for st in self.stations:
            yield (st, st == self.selected)

# for an listing of stream url's, see
# https://www.hendrikjansen.nl/henk/streaming.html

stations = Stations ()

# arrow stream has some delay in starting (you need patience), I guess
# because it waits until the commercial that is played upon connecting
# to the stream is finished.
stations.add ("Arrow Classic Rock", "https://stream.gal.io/arrow")
stations.add ("Studio Brussel", "http://icecast.vrtcdn.be/stubru-high.mp3")
stations.add ("Pinguin Radio", "http://pr128.pinguinradio.com/listen.pls")
stations.add ("Pinguin Classics", "http://pc192.pinguinradio.com/listen.pls")
stations.add ("Pinguin On The Rocks", "http://po192.pinguinradio.com/listen.pls")
# stations.add ("Pinguin Aardschok", "http://as192.pinguinradio.com/listen.pls")
# stations.add ("Radio Paradise", "http://stream-uk1.radioparadise.com/mp3-128")
stations.add ("Radio 1", "http://icecast.omroep.nl/radio1-bb-mp3")
stations.add ("Radio 2", "http://icecast.omroep.nl/radio2-bb-mp3")
stations.add ("Radio 3", "http://icecast.omroep.nl/3fm-bb-mp3")

signal.signal (signal.SIGUSR1, stations.handler)



@app.route('/')
@app.route('/radio')
def radio ():
    urls = [("{:s}".format (url_for ('.select', station=name)), name, ">" if selected else "")
                for (name, selected) in stations.list () ]
    return flask.render_template('radio.html', stations = urls, title='Radio Stations')


@app.route('/select/<station>')
def select (station):
    stations.play (station)
    return radio ()
