#=============================================================
# Script to organize SWEA data from MAVEN mission
#=============================================================
import sys
from pathlib import Path

import cdflib
import numpy as np
import pandas as pd

#------------------------------------------------------------
# Function to organize SWEA data for a given date in a pandas DataFrame with
# columns: time, datetime, epoch, time_unix, time_met, quality, binning
# and also returns energy vector and flux_energy_time matrix
#------------------------------------------------------------

def organizeDataSWEA(YYYY: str, MM: str, DD: str) -> tuple[pd.DataFrame, np.ndarray, np.ndarray]:
    """
    Reads and organizes SWEA data from a CDF file for a given date.
    The function extracts the time, energy, and flux information,

    Parameters
    ----------
    YYYY, MM, DD : str
        date in the format 'YYYY', 'MM', 'DD' to locate the corresponding CDF file.
    
    Returns
    -------
    df_swea : pandas.DataFrame
        DataFra with columns: time, datetime, epoch, time_unix, time_met, quality, binning.

    energy : np.ndarray
       vector of energy bins corresponding to the flux measurements.

    flux_energy_time : np.ndarray
        Flux measurements averaged over angles, with shape (time, energy), 
        where time corresponds to the time vector in df_swea and energy 
        corresponds to the energy vector.
    """

    filepath = f"swea_data/mvn_swe_l2_svy3d_{YYYY}{MM}{DD}_v05_r01.cdf"
    file_path = Path(filepath)

    if not file_path.exists():
        raise FileNotFoundError(f"File doesn't exist: {file_path}")

    cdf = cdflib.CDF(str(file_path))

    epoch = cdf.varget("epoch")
    time_unix = cdf.varget("time_unix")
    time_met = cdf.varget("time_met")

    datetime_swea = cdflib.cdfepoch.to_datetime(epoch)
    datetime_swea = np.array(datetime_swea, dtype="datetime64[ns]")

    day_start = datetime_swea.astype("datetime64[D]")
    seconds_from_day_start = (datetime_swea - day_start) / np.timedelta64(1, "s")
    time_hours = seconds_from_day_start / 3600.0

    energy = cdf.varget("energy")
    quality = cdf.varget("quality")
    binning = cdf.varget("binning")

    diff_en_fluxes = cdf.varget("diff_en_fluxes")

    flux_energy_time = np.nanmean(diff_en_fluxes, axis=(1, 2))
    flux_energy_time = np.array(flux_energy_time, dtype=float)

    flux_energy_time[flux_energy_time <= 0] = np.nan

    df_swea = pd.DataFrame({
        "time": time_hours,
        "datetime": datetime_swea,
        "epoch": epoch,
        "time_unix": time_unix,
        "time_met": time_met,
        "quality": quality,
        "binning": binning,
    })

    return df_swea, energy, flux_energy_time

#------------------------------------------------------------
# Main function to handle command line arguments and organize data
#------------------------------------------------------------

if __name__ == "__main__":

    if len(sys.argv) != 2:
        print("I use: python OrganizeSWEA.py YYYY-MM-DD")
        sys.exit(1)

    fecha = sys.argv[1]
    YYYY, MM, DD = fecha.split("-")

    df_swea, energy, flux_energy_time = organizeDataSWEA(YYYY, MM, DD)

    print(df_swea.head())
    print()
    print("energy shape:", energy.shape)
    print("flux_energy_time shape:", flux_energy_time.shape)