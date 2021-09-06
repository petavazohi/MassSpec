# -*- coding: utf-8 -*-

from matplotlib.animation import Animation, FuncAnimation
from pymsfilereader import MSFileReader
import matplotlib.pylab as plt
from mpl_toolkits.mplot3d import axes3d
import numpy as np
import os
import time
from pathlib import Path
from .raw_file import RawFile

colors = ['red', 'blue', 'green']

class LiveView(object):
    def __init__(self, path=".", only_new=True, delay=20, run=True, mass_1=None, mass_2=None, spectrum_number=None, nrow=4, ncol=4):
        plt.ion()
        self.path = Path(path)
        self.files = []
        self.ratios = np.zeros(shape=(nrow, ncol))
        self.ratios[:, :] = None
        self.dt = 0.5
        self.delay = delay
        if only_new:
            self.analyzed = os.listdir(self.path.as_posix())
        else:
            self.analyzed = []
        self.count = 0
        self.nrow = nrow
        self.ncol = ncol
        self.mass_1 = mass_1
        self.mass_2 = mass_2
        self.spectrum_number = spectrum_number
        self.init_plot()
        # self.animation = Animation(self.fig, self.run, blit=True)
        if run:
            self.run()

        
    def run(self):
        try:
            while True:
                to_analyze = self.check()
                if len(to_analyze) != 0:
                    for ifile in to_analyze:
                        if ifile != "error":
                            self.update(self.count)
                            self.analyzed.append(ifile)
                        self.count += 1
                
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
                    raw_file = RawFile(self.path.joinpath(ifile).as_posix())
                    print("Analyzing {}".format(ifile))
                    if not raw_file.has_error:
                        to_analyze.append(ifile)
                        self.files.append(raw_file)
                        nfiles = len(self.files)
                        irow = (nfiles-1)//self.ncol
                        icol = (nfiles-1)%self.ncol
                        self.ratios[irow, icol] = raw_file.get_ratio(self.mass_1, self.mass_2, self.spectrum_number)
                    else :
                        print("file {} has an error, skipping".format(ifile))
                        self.analyzed.append(ifile)
                        self.files.append(raw_file)
                        to_analyze.append("error")

        return to_analyze


    def init_plot(self):
        self.fig = plt.figure(figsize=(16, 9))
        self.ax_spectra = self.fig.add_subplot(121, projection="3d")
        self.ax_spectra.view_init(elev=10, azim=60)
        self.ax_spectra.set_xlabel("m/z", fontsize=18)
        self.ax_spectra.set_ylabel("Spectra Number", fontsize=18)
        self.ax_spectra.set_zlabel("Intensity", fontsize=18)

        self.ax_drops = self.fig.add_subplot(122)
        self.ax_drops.set_xlim(-0.5, self.ncol-0.5)
        self.ax_drops.set_ylim(-0.5, self.nrow-0.5)
        self.ax_drops.set_facecolor('red')
        plt.show(block=False)
        plt.draw()

    def update(self, i):
        if (len(self.files)-1)%self.ncol == 0 :
            self.ax_spectra.cla()
        for ispectra in range(self.files[i].nspectra):
            x = self.files[i].interpolated_data[ispectra][:, 0]
            y = [self.files[i].dt * ispectra + self.count * self.dt] * len(x)
            z = self.files[i].interpolated_data[ispectra][:, 1]
            self.ax_spectra.plot(x, y, z, color=colors[ispectra%3])
        self.ax_drops.imshow(self.ratios,cmap='Greys')
        self.fig.canvas.draw()
        self.fig.canvas.flush_events()
        # plt.close(self.fig)
