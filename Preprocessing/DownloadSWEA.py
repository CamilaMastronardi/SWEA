# ============================================================
# Download data SWEA MAVEN L2 SVY3D
# ============================================================

import urllib.request
from pathlib import Path
import sys
from datetime import datetime
from datetime import timedelta

# ------------------------------------------------------------
# Function to download file of a given date
# ------------------------------------------------------------

def downloadSWEAFile(YYYY: str, MM: str, DD: str): 
    """
    Downloads the SWEA data file for a given date from the MAVEN mission website.

    Parameters
    ----------
    YYYY: str
        Year in 'YYYY' format.
    MM: str
        Month in 'MM' format.
    DD: str
        Day in 'DD' format.
    
    Returns
    -------
    None
    """
    data_dir = Path("swea_files")
    data_dir.mkdir(exist_ok=True)

    base_url = f"https://lasp.colorado.edu/maven/sdc/public/data/sci/swe/l2/{YYYY}/{MM}/"

    filename = f"mvn_swe_l2_svy3d_{YYYY}{MM}{DD}_v05_r01.cdf"

    url = base_url + filename
    file_path = data_dir / filename

    if not file_path.exists():
        print("Downloading file...")
        urllib.request.urlretrieve(url, file_path)
        print("Download finished.")
    else:
        print("File already exists.")

#------------------------------------------------------------
# Main function to handle command line arguments and download files
#------------------------------------------------------------

if __name__ == "__main__":
    if len(sys.argv) not in (2,3):
        print("I use: python3 DownloadSWEA.py YYYY_i-MM_i-DD_i YYYY_f-MM_f-DD_f (init_date final_date, final_date is optional)")
        sys.exit(1)
    
    if len(sys.argv) == 2:
        fecha = sys.argv[1]
        YYYY, MM, DD = fecha.split('-')
        downloadSWEAFile(YYYY,MM,DD)
        print('Finished')
    elif len(sys.argv) == 3:
        initial_parameter = sys.argv[1]
        final_parameter = sys.argv[2]
        YYYY_i, MM_i, DD_i = (int(f) for f in initial_parameter.split('-'))
        YYYY_f, MM_f, DD_f = (int(f) for f in final_parameter.split('-'))
        init_date = datetime(YYYY_i,MM_i,DD_i).date()
        final_date = datetime(YYYY_f,MM_f,DD_f).date()
        print(f"Downloading files in range {init_date} - {final_date}")
        actual_date = init_date
        count = 1
        while actual_date <= final_date:
            print(f"Downloading day {count} of {final_date-init_date}")
            downloadSWEAFile(actual_date.strftime('%Y'),
                                actual_date.strftime('%m'),
                                actual_date.strftime('%d'))
            actual_date += timedelta(days=1)
            count += 1    