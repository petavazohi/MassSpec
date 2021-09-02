# -*- coding: utf-8 -*-

from pymsfilereader import MSFileReader
import numpy as np
import matplotlib.pylab as plt


class RawFile(object):  # need a better name
    def __init__(self, filename):
        self.filename = filename
        self.data = []
        self._get_data()

    def _get_data(self):
        try:
            ms_file = MSFileReader(self.filename)
        except:
            print("Can not open {}".format(self.filename))
            return
        if ms_file.GetNumSpectra() == 0:
            print("{} does not contain data".format(self.filename))
            return
        for ispectra in range(1, ms_file.GetNumSpectra() + 1):
            self.data.append(np.array(ms_file.GetMassListFromScanNum(ispectra)[0]).T)
        self._nspectra = ms_file.GetNumSpectra()
        self._dt = (ms_file.GetEndTime() - ms_file.GetStartTime()) / self._nspectra
        ms_file.Close()

    @property
    def nspectra(self):
        return self._nspectra

    @property
    def dt(self):
        return self._dt

    def plot(self):
        plt.figure(figsize=(13, 9))
        for ispectrum in range(self.nspectra):
            plt.plot(
                self.data[ispectrum][:, 0],
                self.data[ispectrum][:, 1],
                label="{}".format(ispectrum + 1),
            )
        plt.xlim(self.data[ispectrum][:, 0].min(), self.data[ispectrum][:, 0].max())
        plt.ylim(0,)
        plt.legend()
        plt.show()

    @property
    def ndata(self):
        return self.data[0].shape[0]