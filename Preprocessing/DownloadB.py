# ============================================================
# Download data magnetic field MAVEN L2 SS and z coordinate in PC
# ============================================================

import sys
import os
import requests
from datetime import datetime
from datetime import timedelta

#------------------------------------------------------------
# Paths for magnetic field data
#------------------------------------------------------------

magneticFieldPath = '/app/magnetic_field_data/raw_data_magnetic_field_ss'
magneticFieldPath_pc = '/app/magnetic_field_data/raw_data_magnetic_field_pc'

#------------------------------------------------------------
# Functions needed for downloading magnetic field data
#------------------------------------------------------------

def day_of_year(DD: int, MM: int, YYYY: int):
    date = datetime(YYYY, MM, DD)
    day_of_year = date.timetuple().tm_yday
    return f"{day_of_year:03d}"

def data_is_downloaded(YYYY: str, MM: str, DD: str, path=magneticFieldPath):
    file = os.path.join(path, f"data_{DD}-{MM}-{YYYY}.csv")
    return os.path.exists(file)

#------------------------------------------------------------
# Function to download magnetic field data for a given date 
#------------------------------------------------------------

def downloadFieldData(YYYY: str,MM: str,DD: str):
    if data_is_downloaded(YYYY, MM, DD):
      return
      
    DOY = str(day_of_year(int(DD), int(MM), int(YYYY)))
    url = f"https://lasp.colorado.edu/maven/sdc/public/data/sci/mag/l2/{YYYY}/{MM}/mvn_mag_l2_{YYYY}{DOY}ss_{YYYY}{MM}{DD}_v01_r02.sts" 
    url_pc = f"https://lasp.colorado.edu/maven/sdc/public/data/sci/mag/l2/{YYYY}/{MM}/mvn_mag_l2_{YYYY}{DOY}pc_{YYYY}{MM}{DD}_v01_r02.sts" 

    response = requests.get(url)
    response.raise_for_status()
    lines = response.text.splitlines()

    response_pc = requests.get(url_pc)
    response_pc.raise_for_status()
    lines_pc = response_pc.text.splitlines()

    if not os.path.exists(magneticFieldPath):
      os.makedirs(magneticFieldPath)
    if not os.path.exists(magneticFieldPath):
      os.makedirs(magneticFieldPath)

    targetFile = os.path.join(magneticFieldPath, f"data_{DD}-{MM}-{YYYY}.csv")
    targetFile_pc = os.path.join(magneticFieldPath, f"z_{DD}-{MM}-{YYYY}_pc.csv")

    with open(targetFile, "w") as archivo:
      for line in lines:
        if line.strip() and line.startswith('  ' + YYYY):
            archivo.write(line + '\n')

    with open(targetFile_pc, "w") as archivo:
      for line in lines_pc:
        if line.strip() and line.startswith('  ' + YYYY):
            columns = line.split()
            archivo.write(columns[13] + '\n')

#------------------------------------------------------------
# Main function to handle command line arguments and download files
#------------------------------------------------------------

if __name__== '__main__' :

  if len(sys.argv) not in (2,3): 
        print("I use: python3 DownloadB.py YYYY_i-MM_i-DD_i YYYY_f-MM_f-DD_f (initial_date final_date, final_date is optional)")
        sys.exit(1)
    
  if len(sys.argv) == 2:
    date = sys.argv[1]
    YYYY, MM, DD = date.split('-')
    downloadFieldData(YYYY,MM,DD)
    print('Finished')

  elif len(sys.argv) == 3:
    initial_parameter = sys.argv[1]
    final_parameter = sys.argv[2]
    YYYY_i, MM_i, DD_i = (int(f) for f in initial_parameter.split('-'))
    YYYY_f, MM_f, DD_f = (int(f) for f in final_parameter.split('-'))
    initialDate = datetime(YYYY_i,MM_i,DD_i).date()
    finalDate = datetime(YYYY_f,MM_f,DD_f).date()
    print(f"Downloading files in range {initialDate} - {final_date}")
    actualDate = initialDate
    count = 1
    while actualDate <= finalDate:
      print(f"Downloading day {count} of {finalDate-initialDate}")
      downloadFieldData(actualDate.strftime('%Y'),
                          actualDate.strftime('%m'),
                          actualDate.strftime('%d'))
      actualDate += timedelta(days=1)
      count += 1