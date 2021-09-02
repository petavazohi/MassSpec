# -*- coding: utf-8 -*-

from pymsfilereader import MSFileReader
import numpy as np


class RawFile(object):  # need a better name
    def __init__(self, filename):
        self.filename = filename
        self.data = []
        self._get_data()
        
    def _get_data(self):
        ms_file = MSFileReader(self.filename)
        for ispectra in range(1, self.GetNumSpectra()+1):
            self.data.append(
                np.array(ms_file.GetMassListFromScanNum(ispectra)).reshpae(-1, 2))
        self._nspectra = ms_file.GetNumSpectra()
        self._dt = (ms_file.GetEndTime() -
                    ms_file.GetStartTime())/self._nspectra
        ms_file.Close()
        
    @property
    def nspectra(self):
        return self._nspectra

    @property
    def dt(self):
        return self._dt
