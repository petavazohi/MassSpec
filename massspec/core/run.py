from pymsfilereader import MSFileReader
import psutil
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


colors = ['red', 'blue', 'green', 'cyan', 'magenta']

class LiveView():
    def __init__(self, path='.', delay=1, interpolation='cubic', factor=2):
        self.path = Path(path)
        self.delay = delay
        self.interpolation=interpolation
        self.factor=factor
        self.observer = Observer()
        self.delay = delay
  
    def run(self):
        event_handler = Handler(self.path, self.interpolation, self.factor)
        self.observer.schedule(event_handler, self.path.as_posix(), recursive = True)
        self.observer.start()
        try:
            while True:
                time.sleep(self.delay)
        except:
            self.observer.stop()
            plt.show()
            print("Observer Stopped")
        self.observer.join()

class Handler(FileSystemEventHandler, RawFileCollection):
    def __init__(self, path, interpolation='cubic', factor=2):
        super(Handler, self).__init__(path, interpolation='cubic', factor=2)
        
        self.count = 0
        self.ratio = False
        # plt.ion()
        self.init_plot()
        self.plot_present_files()
        plt.show(block=False)
        # plt.show()
        plt.draw()
        plt.clf()

        self.sizes = {}
        self.dt = 1


    def plot_present_files(self):
        path = Path(self.path)
        for i, ifile in enumerate(path.iterdir()):
            if ifile.suffix == '.raw':
                raw_file = RawFile(ifile, 
                                interpolation=self.interpolation,
                                factor=self.factor)
                self.add_file(raw_file)
                self.update(self.count)
            # self.fig.canvas.draw()
            # self.fig.canvas.flush_events()
            # plt.pause(0.1)
            self.count += 1


    def on_created(self, event):
        path = Path(event.src_path)
        self.sizes[path.name] = path.stat().st_size

    def on_modified(self, event):
        time.sleep(5)
        path = Path(event.src_path)
        print(f'incoming {path.name}')
        if not path.name in self.sizes:
            self.sizes[path.name] = path.stat().st_size
        else:
            if self.sizes[path.name] != path.stat().st_size:
                self.sizes[path.name] = path.stat().st_size
            else : 
                if path.stat().st_size > 22*1024:
                    print(f'detected file copying finished for {path.name}')
                    if path.suffix == '.raw':
                        raw_file = RawFile(path, 
                                        interpolation=self.interpolation,
                                        factor=self.factor)
                        self.add_file(raw_file)
                        self.update(self.count)
                        self.fig.canvas.draw()
                        self.fig.canvas.flush_events()
                        # plt.pause(0.1)
                        self.count += 1

    def on_deleted(self, event):
        path = Path(event.src_path)
        if path.suffix == '.meth':
            print('done!')
        # plt.close(self.fig)

if __name__ == '__main__':
    watcher = LiveView(path="G:\\.shortcut-targets-by-id\\1V4by3NwNnVNuieDBnX6qekJWvQx5f8MA\\MassSpecPython\\Data\\20210830-Run7-2000ms\\emulate2", delay=0.2)
    watcher.run()