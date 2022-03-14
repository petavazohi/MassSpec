# -*- coding: utf-8 -*-

from pymsfilereader import MSFileReader
import numpy as np
import matplotlib.pylab as plt
from scipy.interpolate import interp1d

class RawFile(object):  # need a better name
    def __init__(self, filename, interpolation='cubic', factor=2):
        self.filename = filename
        self.data = []
        self.functions = []
        self.interpolated_data = []
        self.has_error=True
        self._get_data()
        if not self.has_error:
            self._get_interpolated(interpolation, factor)
        
    def _get_data(self):
        try:
            ms_file = MSFileReader(self.filename)
        except:
            print("Can not open {}".format(self.filename))
            return
        if ms_file.GetNumSpectra() == 0:
            print("{} does not contain data".format(self.filename))
            return
        for ispectrum in range(1, ms_file.GetNumSpectra() + 1):
            self.data.append(np.array(ms_file.GetMassListFromScanNum(ispectrum)[0]).T)
        self._nspectra = ms_file.GetNumSpectra()
        self.average_spectrum = np.array(ms_file.GetAveragedMassSpectrum(
            list(range(1,self._nspectra+1)))[0]).T
        self._dt = (ms_file.GetEndTime() - ms_file.GetStartTime()) / self._nspectra
        ms_file.Close()
        self.data = np.array(self.data)
        self.has_error=False

    @property
    def nspectra(self):
        return self._nspectra

    @property
    def dt(self):
        return self._dt

    def _get_interpolated(self, interpolation=None, factor=2):
        if interpolation is None:
            return 
        else :
            for ispectrum in range(self.nspectra):
                self.functions.append(interp1d(self.data[ispectrum][:,0], self.data[ispectrum][:,1], kind=interpolation))
                x = np.linspace(self.data[ispectrum][:, 0].min(), self.data[ispectrum][:, 0].max(), self.data[ispectrum].shape[0]*factor)
                y = self.functions[ispectrum](x)
                self.interpolated_data.append(np.array([x, y]).T)
        self.interpolated_data = np.array(self.interpolated_data)
                
    def get_ratio(self, mass_1, mass_2, spectrum_number):
        return self.get_intensity(mass_1, spectrum_number)/self.get_intensity(mass_2, spectrum_number)

    def get_intensity(self, mass, spectrum_number):
        return self.functions[spectrum_number](mass)
    
    def plot(self, interpolate=True):
        plt.figure(figsize=(13, 9))
        if interpolate:
            data = self.interpolated_data
        else :
            data = self.data
        for ispectrum in range(self.nspectra):
            plt.plot(
                data[ispectrum][:, 0],
                data[ispectrum][:, 1],
                label="{}".format(ispectrum + 1),
            )
        plt.xlim(data[:, :, 0].min(), data[:, :, 0].max())
        plt.ylim(0,)
        plt.legend()
        plt.show()

    @property
    def ndata(self):
        return self.data[0].shape[0]
    
    
