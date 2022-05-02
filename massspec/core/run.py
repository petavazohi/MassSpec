from pymsfilereader import MSFileReader
import numpy as np
import matplotlib.pylab as plt
from scipy.interpolate import interp1d
import xlsxwriter
from .raw_file import RawFile
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
            print("Watchdog received created event - % s." % event.src_path.split(os.sep)[-1])
        elif event.event_type == 'modified':
            # Event is modified, you can process it now
            print("Watchdog received modified event - % s." % event.src_path.split(os.sep)[-1])



    def run(self):
        while True:
            try:
                time.sleep(self.delay)
                to_analyze = self.check()
                if len(to_analyze) != 0:
                    for ifile in to_analyze:
                        if ifile != "error":
                            self.update(self.count)
                            self.analyzed.append(ifile)
                        self.count += 1                
            except KeyboardInterrupt:
                print("Stopping now")
                break


    def check(self):
        dirs = os.listdir(self.path.as_posix())
        new_files = np.setdiff1d(dirs, self.analyzed)
        to_analyze = []
        for ifile in new_files:
            if len(ifile.split(".")) > 1:
                if ifile.split(".")[1] == "raw":
                    raw_file = RawFile(self.path.joinpath(ifile).as_posix())
                    print(f"Analyzing {ifile}")
                    if not raw_file.has_error:
                        to_analyze.append(ifile)
                        self.files.append(raw_file)
                        nfiles = len(self.files)
                        if self.ratio:
                            irow = (nfiles-1)//self.ncol
                            icol = (nfiles-1)%self.ncol
                            self.ratios[irow, icol] = raw_file.get_ratio(self.mass_1, 
                                                                        self.mass_2, 
                                                                        self.spectrum_number)
                    else:
                        print(f"file {ifile} has an error, skipping")
                        self.analyzed.append(ifile)
                        self.files.append(raw_file)
                        to_analyze.append("error")
        return to_analyze


