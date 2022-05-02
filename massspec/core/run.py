from pymsfilereader import MSFileReader
import numpy as np
import matplotlib.pylab as plt
from scipy.interpolate import interp1d
import xlsxwriter
from .raw_file import RawFile, RawFileCollection
from pathlib import Path
import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import os

class Watcher:
    def __init__(self, path, delay=1):
        # Set the directory on watch
        self.path = Path(path)
        self.observer = Observer()
        self.delay = delay
  
    def run(self):
        event_handler = Handler()
        self.observer.schedule(event_handler, self.path.as_posix(), recursive = True)
        self.observer.start()
        try:
            while True:
                time.sleep(self.delay)
        except:
            self.observer.stop()
            print("Observer Stopped")
        self.observer.join()

class Handler(FileSystemEventHandler):

    @staticmethod
    def on_any_event(event):
        if event.is_directory:
            return None
  
        elif event.event_type == 'created':
            # Event is created, you can process it now
            # print("Watchdog received created event - % s." % event.src_path.split(os.sep)[-1])
            print('')
        elif event.event_type == 'modified':
            past_size = -1
            while (past_size != os.path.getsize(event.src_path)):
                past_size = os.path.getsize(event.src_path)
                time.sleep(1)
            # Event is modified, you can process it now
            print("Watchdog received modified event - % s." % event.src_path.split(os.sep)[-1])

class LiveView(Watcher, RawFileCollection):
    
    def __init__(self, path='.', delay=1, interpolation='cubic', factor=2):
        self.path = path
        self.delay = delay
        self.interpolation=interpolation
        self.factor=factor
        super(LiveView, self).__init__(path)


