from pymsfilereader import MSFileReader
import pandas as pd
import xlsxwriter
import numpy as np
import os
import time
from pathlib import Path
# from string import ascii_uppercase
from ..core.raw_file import RawFile


def dir_to_excel(input_path, 
             output_path="data.xlsx", 
             average=True):
    input_path = Path(input_path)
    data = []
    file_names = []
    dirs = os.listdir(input_path.as_posix())
    for ifile in dirs:
        if len(ifile.split(".")) > 1:
            if ifile.split(".")[1].lower() == "raw":
                raw_file = RawFile(input_path.joinpath(ifile).as_posix())
                print("Analyzing {}".format(ifile))
                if not raw_file.has_error:
                    if average:
                        data.append(raw_file.average_spectrum)
                    else:
                        data.append(raw_file.data)
                    file_names.append(ifile)
                else :
                    print("file {} has an error, skipping".format(ifile))
    data = np.array(data)
    if len(data.shape)==3:
        nfiles = data.shape[0]
        nmass = data.shape[1]
        data = data.reshape(nfiles, 1, nmass, -1)
    with xlsxwriter.Workbook(output_path) as workbook:
        nspectrum = data.shape[1]
        for i in range(nspectrum):
            sheet_name = f"spectrum {i+1}"
            worksheet = workbook.add_worksheet(sheet_name)
            worksheet.write(0, 0, "Mass")
            worksheet.write_column(1, 0, data[0, i, :, 0])
            for ifile, fname in enumerate(file_names):
                worksheet.write(0, ifile+1, fname.replace(".raw",""))
                worksheet.write_column(1, ifile+1, data[ifile, i, :, 1])
            
def file_to_excel(input_path, 
                  output_path="data.xlsx", 
                  average=True):
    input_path = Path(input_path)
    data = []
    file_names = []
    dirs = os.listdir(input_path.as_posix())
    for ifile in dirs:
        if len(ifile.split(".")) > 1:
            if ifile.split(".")[1].lower() == "raw":
                raw_file = RawFile(input_path.joinpath(ifile).as_posix())
                print("Analyzing {}".format(ifile))
                if not raw_file.has_error:
                    if average:
                        data.append(raw_file.average_spectrum)
                    else:
                        data.append(raw_file.data)
                    file_names.append(ifile)
                else :
                    print("file {} has an error, skipping".format(ifile))
    data = np.array(data)
    if len(data.shape)==3:
        nfiles = data.shape[0]
        nmass = data.shape[1]
        data = data.reshape(nfiles, 1, nmass, -1)
    with xlsxwriter.Workbook(output_path) as workbook:
        nspectrum = data.shape[1]
        for i in range(nspectrum):
            sheet_name = f"spectrum {i+1}"
            worksheet = workbook.add_worksheet(sheet_name)
            worksheet.write(0, 0, "Mass")
            worksheet.write_column(1, 0, data[0, i, :, 0])
            for ifile, fname in enumerate(file_names):
                worksheet.write(0, ifile+1, fname.replace(".raw",""))
                worksheet.write_column(1, ifile+1, data[ifile, i, :, 1])
            
