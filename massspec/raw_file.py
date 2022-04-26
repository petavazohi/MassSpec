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
            print(f"Can not open {self.filename}")
            return
        if ms_file.GetNumSpectra() == 0:
            print(f"{self.filename} does not contain data")
            return
        for ispectrum in range(1, ms_file.GetNumSpectra() + 1):
            self.data.append(np.array(ms_file.GetMassListFromScanNum(ispectrum)[0]).T)
        self._nspectra = ms_file.GetNumSpectra()
        self._dt = (ms_file.GetEndTime() - ms_file.GetStartTime()) / self._nspectra
        self.mass_resolution = ms_file.MassResolution
        self.data_avg = np.array(ms_file.GetAverageMassList(1,self._nspectra)[0]).T
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
                self.functions.append(interp1d(self.data[ispectrum][:,0], 
                                               self.data[ispectrum][:,1], kind=interpolation))
                x = np.linspace(self.data[ispectrum][:, 0].min(), self.data[ispectrum][:, 0].max(), self.data[ispectrum].shape[0]*factor)
                y = self.functions[ispectrum](x)
                self.interpolated_data.append(np.array([x, y]).T)
        self.interpolated_data = np.array(self.interpolated_data)
        func = interp1d(self.data_avg[:, 0], self.data_avg[:, 1], kind=interpolation)
        x = np.linspace(self.data_avg[:, 0].min(), self.data_avg[:, 0].max(), self.data_avg.shape[0]*factor)
        y = func(x)
        self.interpolated_data_avg = np.array([x, y]).T


    def get_ratio(self, mass_1, mass_2, spectrum_number):
        return self.get_intensity(mass_1, spectrum_number)/self.get_intensity(mass_2, spectrum_number)

    def get_intensity(self, mass, spectrum_number):
        return self.functions[spectrum_number](mass)
    
    def plot(self, average=True):
        plt.figure(figsize=(13, 9))
        ax = plt.subplot(111)
        if not average:
            for ispectrum, spec in enumerate(self.data):
                ax.plot(
                    spec[:, 0],
                    spec[:, 1],
                    label=f"Original Spectrum-{ispectrum + 1}",
                )
                ax.plot(
                    self.interpolated_data[ispectrum][:, 0],
                    self.interpolated_data[ispectrum][:, 1],
                    label=f"Interpolated Spectrum-{ispectrum + 1}",
                )
            xs = np.concatenate([x[:, 0] for x in self.data])
            ax.set_xlim(xs.min(), xs.max())
        else: 
            plt.plot(self.interpolated_data_avg[:, 0], 
                     self.interpolated_data_avg[:, 1], label="Interpolated", color='blue')
            plt.plot(self.data_avg[:, 0], 
                     self.data_avg[:, 1], label="Original", color='red')
            ax.set_title("Averaged Spectra")
            ax.set_xlim(self.data_avg[:, 0].min(), self.data_avg[:, 0].max())
        ax.set_ylim(0, )
        ax.legend()
        plt.show()

    @property
    def ndata(self):
        return self.data[0].shape[0]
    
    
