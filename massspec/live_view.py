# -*- coding: utf-8 -*-

from matplotlib.animation import Animation
from pymsfilereader import MSFileReader
import matplotlib.pylab as plt
from mpl_toolkits.mplot3d import axes3d
import numpy as np
from matplotlib import cm
import os
import time
from pathlib import Path
from .raw_file import RawFile


class LiveView(object):
    def __init__(self, path=".", only_new=True, delay=20):
        self.path = Path(path)
        self.files = []
        self.dt = 0.5
        self.delay = delay
        if only_new:
            self.analyzed = os.listdir(self.path.as_posix())
        else:
            self.analyzed
        self.count = 0
        self.init_plot()
        # self.run()
        # self.animation = Animation(self.fig, blit=True)

    def run(self):
        try:
            while True:
                to_analyze = self.check()
                if len(to_analyze) != 0:
                    for i in range(len(to_analyze), 0, -1):
                        self.update(self.count)
                        self.count += 1
                        self.analyzed.append(to_analyze[i])
        except KeyboardInterrupt:
            print("Stopping now")

    def check(self):
        time.sleep(self.delay)
        dirs = os.listdir(self.path.as_posix())
        new_files = np.setdiff1d(dirs, self.analyzed)
        to_analyze = []
        for ifile in new_files:
            if len(ifile.split(".")) > 1:
                if ifile.split(".")[1] == "raw":
                    to_analyze.append(ifile)
                    self.files.append(
                        RawFile(self.path.joinpath(ifile).as_posix())
                    )
        return to_analyze


    def init_plot(self):
        self.fig = plt.figure(figsize=(9, 7.5))
        self.ax = self.fig.add_subplot(111, projection="3d")
        self.ax.set_xlabel("m/z", fontsize=18)
        self.ax.set_ylabel("Spectra Number", fontsize=18)
        self.ax.set_zlabel("Intensity", fontsize=18)

    def update(self, i):
        for ispectra in range(self.files[i].nspectra):
            x = self.files[i].data[ispectra][:, 0]
            y = [self.files[i].dt * ispectra + self.count * self.dt] * len(x)
            z = self.files[i].data[ispectra][:, 1]
            self.ax.plot(x, y, z)
        plt.show()
