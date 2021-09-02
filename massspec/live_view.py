# -*- coding: utf-8 -*-

import matplotlib.animation as animation
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
        self.analyzed = []
        self.to_analyze = []
        self.files = []
        self.dt = 0.5
        self.check_for_new()
        if not only_new:
            self.analyzed = self.to_analyze

        self.init_plot()
        self.analyze()

    def analyze(self):
        for ifile in self.to_analyze:
            self.files.append(RawFile(self.path.joinpath(ifile).as_posix()))

    def check_for_new(self):
        dirs = os.listdir(self.path.as_posix())
        new_files = np.setdiff1d(dirs, self.analyzed)
        for ifile in new_files:
            if len(ifile.split('.')) > 1:
                if ifile.split(".")[1] == "raw":
                    self.to_analyze.append(ifile)
        return

    def init_plot(self):
        self.fig = plt.figure(figsize=(9, 7.5))
        self.ax = self.fig.add_subplot(111, projection="3d")
        self.ax.set_xlabel("m/z", fontsize=18)
        self.ax.set_ylabel("Spectra Number", fontsize=18)
        self.ax.set_zlabel("Intensity", fontsize=18)

    def update(self, i):
        for ispectra in range(self.files[i].nspectra):
            x = self.files[i].data[ispectra][:, 0]
            y = [self.files[i].dt * ispectra + i * self.dt] * len(x)
            z = self.files[i].data[ispectra][:, 1]
            self.ax.plot(x, y, z)
        plt.show()
