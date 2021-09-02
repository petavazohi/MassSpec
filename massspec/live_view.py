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


class LiveView(object):
    def __init__(self, path='.', only_new=True, delay=20):
        self.path = Path(path)
        self.analyzed = []
        self.to_analyze = []
        self.dt = []
        self.data = []
        self.check_for_new()
        if not only_new:
            self.analyzed = self.to_analyze

    
    def check_for_new(self):
        dirs = os.listdir(self.path.as_posix())
        new_files = np.setdiff1d(self.analyzed, dirs)
        for ifile in new_files:
            if ifile.split(".") == 'raw':
                self.to_analyze.append(ifile)
        return 
    

        