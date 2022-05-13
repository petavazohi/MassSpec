# -*- coding: utf-8 -*-
import os
from pymsfilereader import MSFileReader
import numpy as np
import matplotlib.pylab as plt
from scipy.interpolate import interp1d
import xlsxwriter
from pathlib import Path

class RawFile(object):  # need a better name
    def __init__(self, filename, interpolation='cubic', factor=2):
        self.filename = Path(filename)
        self.data = []
        self.data_avg = None
        self.functions = []
        self.interpolated_data = []
        self.has_error=False
        self._get_data()
        if not self.has_error:
            self._get_interpolated(interpolation, factor)
        
    def _get_data(self):
        try:
            ms_file = MSFileReader(self.filename.as_posix())
        except:
            print(f"Can not open {self.filename}")
            self.has_error = True
            return 
        if ms_file.GetNumSpectra() == 0:
            print(f"{self.filename} does not contain data")
            self.has_error = True
            return
        for ispectrum in range(1, ms_file.GetNumSpectra() + 1):
            self.data.append(np.array(ms_file.GetMassListFromScanNum(ispectrum)[0]).T)
        self._nspectra = ms_file.GetNumSpectra()
        self.average_spectrum = np.array(ms_file.GetAveragedMassSpectrum(
            list(range(1,self._nspectra+1)))[0]).T
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
    
    def to_excel(self,
                output_path="data.xlsx", 
                average=True):
        with xlsxwriter.Workbook(output_path) as workbook:
            sheet_name = f"Avg spectrum"
            worksheet = workbook.add_worksheet(sheet_name)
            worksheet.write(0, 0, "m/z")
            worksheet.write(0, 1, "Intensity")
            worksheet.write_column(1, 0, self.data_avg[:, 0])
            worksheet.write_column(1, 1, self.data_avg[:, 1])
        return 


class RawFileCollection(object):
    def __init__(self, path='.', interpolation='cubic', factor=2):
        self.path = Path(path)
        self.ratio = False
        self.interpolation = interpolation
        self.factor = factor
        self._data_avg = []
        self._data = []
        self.files = []
        self.nfiles = 0
        self.dt = 1
        self.parse()
        
    def parse(self):
        files = [self.path.joinpath(x) for x in os.listdir(self.path)]
        for fname in sorted(files, key=lambda x: x.name):
            if fname.suffix == '.raw':
                raw_file = RawFile(fname, interpolation=self.interpolation, factor=self.factor)
                self.add_file(raw_file)
                if not raw_file.has_error:
                    self.nfiles += 1

    def add_file(self, raw_file):
        if raw_file.data_avg is not None:
            if self._data_avg is None:
                self._data_avg.append(raw_file.data_avg) 
                self._data.append(raw_file.data)
            else:
                self._data_avg.append(raw_file.data_avg)
                self._data.append(raw_file.data)
            self.files.append(raw_file.filename.name)

    @property    
    def data_avg(self):
        return self._data_avg
    
    @property    
    def data(self):
        return self._data

    def to_excel(self,
                 output_path="data.xlsx"):
        with xlsxwriter.Workbook(output_path) as workbook:
            sheet_name = "Avg spectrum"
            worksheet = workbook.add_worksheet(sheet_name)
            for iscan, d in enumerate(self.data_avg):
                worksheet.write(0, iscan*2, f"{self.files[iscan]}")
                worksheet.write(1, iscan*2, "m/z")
                worksheet.write(1, iscan*2 + 1, "Intensity")
                worksheet.write_column(2, iscan*2, d[:, 0])
                worksheet.write_column(2, iscan*2 + 1, d[:, 1])
        return

    def init_plot(self):
        self.fig = plt.figure(figsize=(16, 9))
        if self.ratio:
            self.ax_spectra = self.fig.add_subplot(121, projection="3d")
            self.ax_drops = self.fig.add_subplot(122)   
            self.ax_drops.set_xlim(-0.5, self.ncol-0.5)
            self.ax_drops.set_ylim(-0.5, self.nrow-0.5)
            self.ax_drops.set_facecolor('red')
        else:
            self.ax_spectra = self.fig.add_subplot(111, projection="3d")
        self.ax_spectra.view_init(elev=10, azim=60)
        self.ax_spectra.set_xlabel("m/z", fontsize=18)
        self.ax_spectra.set_ylabel("Spectra Number", fontsize=18)
        self.ax_spectra.set_zlabel("Intensity", fontsize=18)

    def plot(self):
        self.init_plot()
        for i in range(self.nfiles):
            self.update(i)
        plt.show()

    def update(self, i):
        for i in range(self.nfiles):
            x = self.data_avg[i][:, 0]
            y = [i * self.dt] * len(x)
            z = self.data_avg[i][:, 1]
            self.ax_spectra.plot(x, y, z, color='black')
        # print(i, 'trying to plot')
        # if self.ratio:
        #     self.ax_drops.imshow(self.ratios, cmap='Greys')
        #     if (len(self.files)-1)%self.ncol == 0 :
        #         self.ax_spectra.cla()
        
        # self.fig.canvas.draw()
        # self.fig.canvas.flush_events()
        # plt.close(self.fig)    
