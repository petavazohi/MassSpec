from pymsfilereader import MSFileReader
import pandas as pd
import xlsxwriter
import numpy as np
import os
import time
from pathlib import Path
# from string import ascii_uppercase
from .raw_file import RawFile


def to_excel(input_path, 
             output_path="data.xlsx"):
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
                    data.append(raw_file.data)
                    file_names.append(ifile)
                else :
                    print("file {} has an error, skipping".format(ifile))
    data = np.array(data)
    with xlsxwriter.Workbook(output_path) as workbook:
        nfile = data.shape[0]
        nspectrum = data.shape[1]
        for i in range(nspectrum):
            worksheet = workbook.add_worksheet(f"spectrum {i+1}")
            worksheet.write(0, 0, "Mass")
            worksheet.write_column(1, 0, data[0, i, :, 0])
            for ifile, fname in enumerate(file_names):
                worksheet.write(0, ifile+1, fname.replace(".raw",""))
                worksheet.write_column(1, ifile+1, data[ifile, i, :, 1])
        
