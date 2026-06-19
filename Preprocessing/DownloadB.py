# ============================================================
# Download data magnetic field MAVEN L2 SS
# ============================================================

import sys
import os
import requests
from datetime import datetime
from datetime import timedelta
from tqdm import tqdm

#------------------------------------------------------------
# Path for magnetic field data
#------------------------------------------------------------

magneticFieldPath = '/app/magnetic_field_data/raw_data_magnetic_field_ss'

#------------------------------------------------------------
# Functions needed for downloading magnetic field data
#------------------------------------------------------------

def day_of_year(DD: int, MM: int, YYYY: int):
    """
    Converts a date given by day, month, and year into the corresponding day of the year (DOY).
    Parameters
    ----------
    DD : int
        Day of the month (1-31)
    MM : int
        Month of the year (1-12)
    YYYY : int
        Year (e.g., 2020)
    
    Returns
    -------
    str
        Day of the year as a three-digit string
        (e.g., '001' for January 1st, '032' for February 1st).
    """
    date = datetime(YYYY, MM, DD)
    day_of_year = date.timetuple().tm_yday
    return f"{day_of_year:03d}"


def data_is_downloaded(YYYY: str, MM: str, DD: str, path=magneticFieldPath):
    """
    Checks if the magnetic field data file for a given date already exists in the 
    specified directory.

    Parameters
    ----------
    YYYY, MM, DD : str
    date in the format 'YYYY', 'MM', 'DD' to locate the corresponding file.

    Returns
    -------
    bool
        True if the file exists, False otherwise.
    """
    file = os.path.join(path, f"data_{DD}-{MM}-{YYYY}.csv")
    return os.path.exists(file)


#------------------------------------------------------------
# Function to download magnetic field data for a given date 
#------------------------------------------------------------

def downloadFieldData(YYYY: str, MM: str, DD: str):
    """
    Downloads the magnetic field data file for a given date if it doesn't already exist in
    the 'raw_data_magnetic_field_ss' directory.

    Parameters
    ----------
    YYYY, MM, DD : str
        date in the format 'YYYY', 'MM', 'DD' to locate the corresponding files.
    
    Returns
    -------
    None
    """
    if data_is_downloaded(YYYY, MM, DD):
      return
      
    DOY = str(day_of_year(int(DD), int(MM), int(YYYY)))
    url = f"https://pds-ppi.igpp.ucla.edu/data/maven-mag-calibrated/data/ss/highres/{YYYY}/{MM}/mvn_mag_l2_{YYYY}{DOY}ss_{YYYY}{MM}{DD}_v01_r02.sts" 

    response = requests.get(url, stream=True)
    response.raise_for_status()

    total_size = int(response.headers.get("content-length", 0))

    if not os.path.exists(magneticFieldPath):
      os.makedirs(magneticFieldPath)

    targetFile = os.path.join(magneticFieldPath, f"data_{DD}-{MM}-{YYYY}.csv")

    lines = ""

    with tqdm(
        total=total_size,
        unit="B",
        unit_scale=True,
        unit_divisor=1024,
        desc=f"Downloading {DD}-{MM}-{YYYY}"
    ) as progress_bar:

        for chunk in response.iter_content(chunk_size=1024 * 1024):
            if chunk:
                lines += chunk.decode("utf-8", errors="ignore")
                progress_bar.update(len(chunk))

    lines = lines.splitlines()

    with open(targetFile, "w") as archivo:
      for line in lines:
        if line.strip() and line.startswith('  ' + YYYY):
            archivo.write(line + '\n')


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
    print(f"Downloading files in range {initialDate} - {finalDate}")
    actualDate = initialDate
    count = 1
    while actualDate <= finalDate:
      print(f"Downloading day {count} of {finalDate-initialDate+1}")
      downloadFieldData(actualDate.strftime('%Y'),
                          actualDate.strftime('%m'),
                          actualDate.strftime('%d'))
      actualDate += timedelta(days=1)
      count += 1