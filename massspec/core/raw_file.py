# -*- coding: utf-8 -*-
import re
from pymsfilereader import MSFileReader
import numpy as np
import matplotlib.pylab as plt
from scipy.interpolate import interp1d
import xlsxwriter
from pathlib import Path
from datetime import date
from typing import Union
from scipy.signal import find_peaks
from scipy.io import savemat

colors = ['red', 'blue', 'green', 'cyan', 'magenta']
today = date.today()

class RawFile(object):  # need a better name
    def __init__(self, 
                 filename: Union[str, Path],
                 interpolate: bool=False,
                 interpolation_type: str = 'cubic', 
                 factor: int=1):
        self.filename = Path(filename)
        if not self.filename.exists():
            raise Exception(f'File {self.filename} does not exist.')            
        self.data = []
        self.data_avg = None
        self.functions = []
        self.interpolated_data = []
        self.header = []
        self.has_error=False
        self._get_data()
        self.interpolate = interpolate
        if interpolate and not self.has_error:
            self._get_interpolated(interpolation_type, factor)
        
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
            self.header.append(ms_file.GetScanHeaderInfoForScanNum(ispectrum))
        self._nspectra = ms_file.GetNumSpectra()
        self.average_spectrum = np.array(ms_file.GetAveragedMassSpectrum(
            list(range(1,self._nspectra+1)))[0]).T

        self.mass_resolution = ms_file.MassResolution
        self.data_avg = np.array(ms_file.GetAverageMassList(1,self._nspectra)[0]).T
        ms_file.Close()
        # self.data = np.array(self.data)
        self.has_error=False

    @property
    def nspectra(self):
        return self._nspectra

    @property
    def dt(self):
        return self._dt

    def _get_interpolated(self, interpolation=None, factor=1):
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
    
    def plot(self, average=True, show=True):
        plt.figure(figsize=(9, 6))
        ax = plt.subplot(111)
        if not average:
            for ispectrum, spec in enumerate(self.data):
                ax.plot(
                    spec[:, 0],
                    spec[:, 1],
                    label=f"Original Spectrum-{ispectrum + 1}",
                )
                if self.interpolate:
                    ax.plot(
                        self.interpolated_data[ispectrum][:, 0],
                        self.interpolated_data[ispectrum][:, 1],
                        label=f"Interpolated Spectrum-{ispectrum + 1}",
                    )
            xs = np.concatenate([x[:, 0] for x in self.data])
            ax.set_xlim(xs.min(), xs.max())
        else:
            if self.interpolate:
                ax.plot(self.interpolated_data_avg[:, 0], 
                        self.interpolated_data_avg[:, 1], label="Interpolated", color='blue')
            ax.plot(self.data_avg[:, 0], 
                    self.data_avg[:, 1], label="Original", color='red')
            ax.set_title("Averaged Spectra")
            ax.set_xlim(self.data_avg[:, 0].min(), self.data_avg[:, 0].max())
        ax.set_ylim(0,)
        ax.set_xlabel("m/z")
        ax.set_ylabel("Intensity")
        plt.tight_layout()
        if self.nspectra < 5:
            ax.legend()
        if show:
            plt.show()
        return ax

    def reduce(self,
               peak_prominence=500):
        for i_spec, spectrum in enumerate(self.data):        
            peaks, _ = find_peaks(spectrum[:, 1], prominence=peak_prominence)
            self.data[i_spec] = spectrum[peaks]
        peaks, _ = find_peaks(self.data_avg[:, 1], prominence=peak_prominence)
        self.data_avg = self.data_avg[peaks]
        return 

    @property
    def ndata(self):
        return self.data[0].shape[0]
    
    def to_excel(self,
                output_path=f"{today.strftime('%Y%m%d')}.xlsx",
                rounding=False, 
                decimals=2,
                overwrite=False):
        path = Path(output_path)
        c = 1
        while path.exists() and not overwrite:
            mod = f"{path.stem}-Run{c}{path.suffix}"
            path = path.parent / mod
            c += 1
            
        with xlsxwriter.Workbook(path.as_posix()) as workbook:
            if self.filename.stat().st_size//2**20 > 50:
                workbook.use_zip64()
            if rounding:
                num_format = workbook.add_format({'num_format': '0.'+'0'*decimals})
            else:
                num_format = None
            sheet_name = "Spectra"
            worksheet = workbook.add_worksheet(sheet_name)
            for i_spec, spectrum in enumerate(self.data):
                worksheet.write(0, i_spec*2, f"Spectrum {i_spec + 1} m/z")
                worksheet.write(0, i_spec*2+1, 
                                f"Spectrum {i_spec + 1} Intensity")
                worksheet.write(1, i_spec*2, 
                                self.header[i_spec]['StartTime'], 
                                num_format)
                worksheet.write_column(2, i_spec*2, spectrum[:, 0], num_format)
                worksheet.write_column(2, i_spec*2+1, spectrum[:, 1], num_format)
            sheet_name = "Average"
            worksheet = workbook.add_worksheet(sheet_name)
            worksheet.write(0, 0, "m/z")
            worksheet.write(0, 1, "Intensity")
            worksheet.write_column(1, 0, self.data_avg[:, 0])
            worksheet.write_column(1, 1, self.data_avg[:, 1])
        return 

    def to_dict(self):
        ret = {}
        for attr in ['data', 'data_avg', 'header']:
            ret[attr] = getattr(self, attr)
        return ret
    
    def to_matlab(self, filename='matlab_out.mat'):
        savemat(filename, self.to_dict())
        return
        
        

class RawFileCollection(object):
    def __init__(self, path='.', interpolation='cubic', factor=2, track_mass=None, delta_mz=3, dmz=0.2):
        self.path = Path(path)
        self.ratio = False
        self.interpolation = interpolation
        self.factor = factor
        self._data_avg = []
        self._data = []
        self.files = []
        self.track_area = []
        self.total_area = []
        self.nfiles = 0
        self.dt = 1
        self.track_mass = track_mass
        self.delta_mz = delta_mz
        self.dmz = dmz
        self.parse()


    def parse(self):
        files = [x for x in self.path.iterdir()]
        sort_dict = {int(re.findall("([0-9]+)", x.name)[0]):x for x in files if x.suffix.lower() == '.raw'}
        for ix in sorted(sort_dict):
            raw_file = RawFile(sort_dict[ix], interpolation=self.interpolation, factor=self.factor)
            self.add_file(raw_file)
            if not raw_file.has_error:
                self.nfiles += 1

    def add_file(self, raw_file):
        if raw_file.data_avg is not None:
            if self._data_avg is None:
                self._data_avg.append(raw_file.data_avg) 
                self._data.append(raw_file.data)
            else :
                self._data_avg.append(raw_file.data_avg) 
                self._data.append(raw_file.data)
            if self.track_mass is not None:
                cond1 = raw_file.data_avg[:,0] > self.track_mass - self.delta_mz
                cond2 = raw_file.data_avg[:,0] < self.track_mass + self.delta_mz
                cond = np.bitwise_and(cond1, cond2)
                self.track_area.append(np.trapz(raw_file.data_avg[cond, 1], dx=self.dmz))
                self.total_area.append(np.trapz(raw_file.data_avg[:, 1], dx=self.dmz))
            self.files.append(raw_file.filename.name)

    @property
    def data_avg(self):
        return self._data_avg
    
    @property    
    def data(self):
        return self._data

    def to_excel(self,
                 output_path=f"{today.strftime('%Y%m%d')}-Run1.xlsx",
                 reduce=False,
                 peak_prominence=500,
                 n_reduction=0):
        path = Path(output_path)
        c = 2
        while path.exists():
            mod = f"{path.stem[:-1]}{c}{path.suffix}"
            # might need to change :-1 for double digits
            path = path.parent / mod
            c += 1
        with xlsxwriter.Workbook(path.as_posix()) as workbook:
            sheet_name = "Avg spectrum"
            worksheet = workbook.add_worksheet(sheet_name)
            for iscan, d in enumerate(self.data_avg):
                data = d
                if reduce:
                    for i in range(n_reduction):
                        peaks, _ = find_peaks(data[:, 1], prominence=peak_prominence)
                        data = data[peaks]
                worksheet.write(0, iscan*2, f"{self.files[iscan]}")
                worksheet.write(1, iscan*2, "m/z")
                worksheet.write(1, iscan*2 + 1, "Intensity")
                worksheet.write_column(2, iscan*2, data[:, 0])
                worksheet.write_column(2, iscan*2 + 1, data[:, 1])
            if self.track_mass is not None:
                worksheet_track_mass = workbook.add_worksheet(f"Integrated {self.track_mass} m-z ")
                worksheet_track_mass.write(0, 0, "Scan number")
                worksheet_track_mass.write(0, 1, f"{self.track_mass} Count")
                worksheet_track_mass.write(0, 2, "Total Count")
                worksheet_track_mass.write_column(1, 0, np.arange(1, self.nfiles+1))
                worksheet_track_mass.write_column(1, 1, np.array(self.track_area))
                worksheet_track_mass.write_column(1, 2, np.array(self.total_area))
        return

    def init_plot(self):
        self.fig = plt.figure(figsize=(16, 9))
        if self.track_mass:
            self.ax_spectra = self.fig.add_subplot(121, projection="3d")
            self.ax_track_mass = self.fig.add_subplot(122)
            # self.ax_track_mass.set_xlim(0,)
            # self.ax_track_mass.set_ylim(0,)
        elif self.ratio:
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
        self.ax_track_mass.plot(np.arange(1, self.nfiles + 1), 
                                self.track_area, color='blue', 
                                label=f'Inegrated {self.track_mass-self.delta_mz}-{self.track_mass+self.delta_mz}')
        self.ax_track_mass.scatter(np.arange(1, self.nfiles + 1), 
                               self.total_area, facecolors='none', edgecolor='red',
                               label='Total Count', marker='o')
        self.ax_track_mass.set_xticks(np.arange(1, self.nfiles + 1, 2))
        self.ax_track_mass.grid(True)
        self.ax_track_mass.set_ylim(0, )
        self.ax_track_mass.set_xlim(1, self.nfiles)
        self.ax_track_mass.set_xlabel("Scan number")
        plt.legend()
        self.ax_track_mass.set_ylabel("Count")
        plt.show()

    def update(self, i):
        x = self.data_avg[i][:, 0]
        y = [i * self.dt] * len(x)
        z = self.data_avg[i][:, 1]
        self.ax_spectra.plot(x, y, z, color=colors[i % 5])
        # if self.track_mass is not None:
        #     self.ax_track_mass.plot(i, self.track_area[i])
                
        # print(i, 'trying to plot')
        # if self.ratio:
        #     self.ax_drops.imshow(self.ratios, cmap='Greys')
        #     if (len(self.files)-1)%self.ncol == 0 :
        #         self.ax_spectra.cla()
        
        # self.fig.canvas.draw()
        # self.fig.canvas.flush_events()
        # plt.close(self.fig)    
    

        