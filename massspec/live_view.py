# -*- coding: utf-8 -*-
from itertools import count
from matplotlib.animation import Animation, FuncAnimation
from pymsfilereader import MSFileReader
import matplotlib.pylab as plt
from mpl_toolkits.mplot3d import axes3d
import numpy as np
import os
import time
from pathlib import Path
from .core.raw_file import RawFile
import dash
from dash import dcc, html
import plotly
import plotly.express as px
from dash.dependencies import Input, Output

colors = ['red', 'blue', 'green', 'cyan', 'magenta']

app = dash.Dash(__name__)
app.layout = html.Div(
        html.Div([
            html.H4('Mass Spec'),
            dcc.Graph(id='live-update-graph'),
            dcc.Interval(
                id='interval-component',
                interval=5*1000, # in milliseconds
                n_intervals=0
            )
        ])
)

class LiveView(object):
    def __init__(self, path=".", 
                #  only_new=True, 
                 delay=20, 
                #  run=True, 
                 ratio=False,
                 mass_1=None, 
                 mass_2=None, 
                 spectrum_number=None, 
                 nrow=4,
                 ncol=4):

        # plt.ion()

        self.path = Path(path)
        self.files = []
        self.ratio = ratio
        if self.ratio:
            self.ratios = np.zeros(shape=(nrow, ncol))
            self.ratios[:, :] = None
            self.nrow = nrow
            self.ncol = ncol
            self.mass_1 = mass_1
            self.mass_2 = mass_2
        self.dt = 0.5
        self.delay = delay
        # if only_new:
        #     self.analyzed = os.listdir(self.path.as_posix())
        # else:
        #     self.analyzed = []
        self.analyzed = []
        self.count = 0
        self.spectrum_number = spectrum_number
        # self.init_plot()
        # self.animation = Animation(self.fig, self.run, blit=True)
        # if run:
        # self.run()
        app.run_server()

        
    def run(self):
        while True:
            try:
                time.sleep(self.delay)
                to_analyze = self.check()
                if len(to_analyze) != 0:
                    for ifile in to_analyze:
                        if ifile != "error":
                            self.update(self.count)
                            self.analyzed.append(ifile)
                        self.count += 1                
            except KeyboardInterrupt:
                print("Stopping now")
                break


    def check(self):
        dirs = os.listdir(self.path.as_posix())
        new_files = np.setdiff1d(dirs, self.analyzed)
        to_analyze = []
        for ifile in new_files:
            if len(ifile.split(".")) > 1:
                if ifile.split(".")[1] == "raw":
                    raw_file = RawFile(self.path.joinpath(ifile).as_posix())
                    print(f"Analyzing {ifile}")
                    if not raw_file.has_error:
                        to_analyze.append(ifile)
                        self.files.append(raw_file)
                        nfiles = len(self.files)
                        if self.ratio:
                            irow = (nfiles-1)//self.ncol
                            icol = (nfiles-1)%self.ncol
                            self.ratios[irow, icol] = raw_file.get_ratio(self.mass_1, 
                                                                        self.mass_2, 
                                                                        self.spectrum_number)
                    else:
                        print(f"file {ifile} has an error, skipping")
                        self.analyzed.append(ifile)
                        self.files.append(raw_file)
                        to_analyze.append("error")
        return to_analyze


    def init_plot(self):
        plt.ion()
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
        plt.show(block=False)
        plt.draw()

    def update(self, i):
        if self.ratio:
            self.ax_drops.imshow(self.ratios,cmap='Greys')
            if (len(self.files)-1)%self.ncol == 0 :
                self.ax_spectra.cla()
        x = self.files[i].data_avg[:, 0]
        y = [self.files[i].dt + self.count * self.dt] * len(x)
        z = self.files[i].data_avg[:, 1]
        self.ax_spectra.plot(x, y, z, color='black')
        self.fig.canvas.draw()
        self.fig.canvas.flush_events()
        # plt.close(self.fig)

    @app.callback(Output('live-update-graph', 'figure'),
                Input('interval-component', 'n_intervals'))
    def update_graph_live(n, self):
        to_analyze = self.check()
        if len(to_analyze) != 0:
            for _, ifile in enumerate(to_analyze):
                if ifile != "error":
                    x = self.files[self.count].data_avg[:, 0]
                    y = [self.files[self.count].dt + self.count * self.dt]*len(x)
                    z = self.files[self.count].data_avg[:, 1]
                    df = {'m/z':x, 'time':y ,"Intensity":z}
                    self.analyzed.append(ifile)
                self.count += 1
        fig = px.line_3d(df, x="m/z", y="time", z="Intensity")
        return fig
