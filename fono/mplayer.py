import logging
import os
import subprocess
import psutil

logger = logging.getLogger(__name__)
logger.info ('mplayer module started')


# see http://www.mplayerhq.hu/DOCS/tech/slave.txt

class Mplayer(object):

    def __init__(self, filename="", fifo_path='/tmp/mplayer-fifo.sock',
                 binary='mplayer', mock = False):

        self.mock = mock
        self.filename = filename
        self.p = None
        self.fifo_path = fifo_path
        self.ps_process = None
        self.arguments = [
            binary,
            '-really-quiet',
            '-noconsolecontrols',
            '-slave',
            '-input',
            'file=%s' % self.fifo_path,
        ]
        logger.info ("mplayer init done")

    def load_file(self, filename):
        self.filename = filename
        return self

    def check_fifo(self):
        return os.path.exists(self.fifo_path)

    def remove_fifo(self):
        try:
            os.unlink(self.fifo_path)
        except OSError:
            pass

    def start(self, source):
        logger.debug ("mplayer start %s", source)
        if self.mock:
            return self
        self.remove_fifo()
        os.mkfifo(self.fifo_path)

        args = self.arguments
        if source.endswith (".pls"):
            args += ["-playlist"]
        args += [source]

        # print ("ARGS", *args)

        self.p = subprocess.Popen(args)

        self.ps_process = psutil.Process (self.p.pid)

        return self

    def suspend (self):
        if self.mock:
            return self
        # next if is needed to be able to start in muted state
        if self.ps_process is not None:
            self.ps_process.suspend ()
            logger.debug ("status %s", self.ps_process.status ())

    def resume (self):
        if self.mock:
            return self
        # next if is needed to be able to start in muted state
        if self.ps_process is not None:
            self.ps_process.resume ()
            logger.debug ("status %s", self.ps_process.status ())

    # see https://stackoverflow.com/questions/2760652/how-to-kill-or-avoid-zombie-processes-with-subprocess-module
    # see http://psutil.readthedocs.io/en/latest/
    def check_running (self):
        logger.debug ("check running")
        if self.mock:
            return self

        result = True

        try:
            self.ps_child = self.ps_process.children ()[0] # expect one child
            if not self.ps_child.is_running ():
                result = False
            if self.ps_child.status () == psutil.STATUS_ZOMBIE:
                result = False
            if self.ps_process.status () == psutil.STATUS_ZOMBIE:
                result = False
            if not self.ps_process.is_running ():
                result = False
        except:
            result = False

        if result == False:
            self.reap_children ()

        return result

    # from psutil doc
    def reap_children(self, timeout=3):
        "Tries hard to terminate and ultimately kill all the children of this process."
        def on_terminate(proc):
            logger.debug("process {} terminated with exit code {}".format(proc, proc.returncode))

        procs = psutil.Process().children(recursive = True)

        # also include former grandchildren that might have been reparented
        # It appears that mplayer (on OSX) forks a child, so the python process
        # has a child and a grandchild.  Care must be taken to also wait and
        # kill the child process. This doesn't work with
        # subprocess.children(recursive=True) because if the subchild becomes
        # orphan it has 1 as ppid.

        for p in psutil.process_iter():
            if p.name () == 'mplayer' and p.ppid () == 1:
                procs.append(p)
        
        # send SIGTERM
        for p in procs:
            p.terminate()
        gone, alive = psutil.wait_procs(procs, timeout=timeout, callback=on_terminate)
        if alive:
            # send SIGKILL
            for p in alive:
                logger.debug("process {} survived SIGTERM; trying SIGKILL".format (p))
                p.kill()
            gone, alive = psutil.wait_procs(alive, timeout=timeout, callback=on_terminate)
            if alive:
                # give up
                for p in alive:
                    logger.debug("process {} survived SIGKILL; giving up".format (p))

    def play (self, source):
        logger.info ("mplayer play %s", source)
        if self.mock:
            return

        if not self.check_running ():
            self.remove_fifo ()
            self.start (source)
            return

        if source.endswith (".pls"):
            self.send_cmd ("loadlist", source)
        else:
            self.send_cmd ("loadfile", source)


    def send_cmd(self, *args):
        if self.mock:
            return
        with open(self.fifo_path, 'w') as sock:
            cmd = " ".join(args)
            logger.debug ("send_cmd sending: %s", cmd)
            sock.write("%s\n" % cmd)
            sock.flush()
            if cmd == 'quit':
                self.remove_fifo()
        return self

    def kill(self):
        # self.remove_fifo()
        logger.debug ("trying to kill")
        try:
            self.p.kill()
        except:
            logger.debug ("could not kill")
            pass
        return self
