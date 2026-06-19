#=============================================================
# Script to separate MAVEN MAG and SWEA data by orbit
#=============================================================

import sys
import numpy as np
import pandas as pd

from OrganizeB import organizeData
from OrganizeSWEA import organizeDataSWEA


#------------------------------------------------------------
# Function to find local minima in the spacecraft altitude
# These minima are used as an approximation to periapsis times
#------------------------------------------------------------

def findLocalMinima(time: np.ndarray, r_sat: np.ndarray) -> np.ndarray:
    """
    Finds local minima in the spacecraft altitude (r_sat) as a function of time.
    These minima are used as an approximation to periapsis times.
    
    Parameters
    ----------
    time : np.ndarray
        Time array.
    r_sat : np.ndarray
        Spacecraft altitude array.

    Returns
    -------
    np.ndarray
        Indices of the local minima.
    """
    minima_indices = []

    for i in range(1, len(r_sat) - 1):
        if r_sat[i] < r_sat[i - 1] and r_sat[i] < r_sat[i + 1]:
            minima_indices.append(i)

    return np.array(minima_indices)


#------------------------------------------------------------
# Function to filter periapsis candidates
# MAVEN orbital period is about 4.5 h, so two real periapses
# should not be too close in time
#------------------------------------------------------------

def filterPeriapses(time: np.ndarray, r_sat: np.ndarray, minima_indices: np.ndarray, min_separation_hours: float = 3.0) -> np.ndarray:
    """
    # Filters periapsis candidates based on their time separation and altitude.
    # MAVEN orbital period is about 4.5 h, so two real periapses
    # should not be too close in time. If two minima are closer than
    # min_separation_hours, the one with lower altitude is kept as a periapsis candidate.
    
    # Parameters
    # ----------
    # time : np.ndarray
    #     Time array.
    # r_sat : np.ndarray
    #     Spacecraft altitude array.
    # minima_indices : np.ndarray
    #     Indices of the local minima.
    # min_separation_hours : float, optional
    #     Minimum time separation between periapses (default is 3.0 hours).

    # Returns
    # -------
    # np.ndarray
    #     Indices of the filtered periapses.
    """
    if len(minima_indices) == 0:
        return np.array([])

    selected_indices = [minima_indices[0]]

    for idx in minima_indices[1:]:
        last_idx = selected_indices[-1]

        delta_t = time[idx] - time[last_idx]

        if delta_t >= min_separation_hours:
            selected_indices.append(idx)

        else:
            # If two minima are too close, keep the one with lower altitude
            if r_sat[idx] < r_sat[last_idx]:
                selected_indices[-1] = idx

    return np.array(selected_indices)


#------------------------------------------------------------
# Function to detect periapsis times from magnetic field data
#------------------------------------------------------------

def findPeriapsisTimes(df_B: pd.DataFrame, min_separation_hours: float = 3.0) -> np.ndarray:
    """
    Detects periapsis times from magnetic field data by finding local minima in the spacecraft altitude (r_sat).

    Parameters
    ----------
    df_B : pandas.DataFrame
        DataFrame containing magnetic field and spacecraft position data, with at least 'time' and 'r_sat' columns.
    min_separation_hours : float, optional
        Minimum time separation between periapses in hours (default is 3.0 hours).
    
    Returns
    -------
    np.ndarray
        Array of detected periapsis times.
    """
    time = df_B["time"].to_numpy()
    r_sat = df_B["r_sat"].to_numpy()

    minima_indices = findLocalMinima(time, r_sat)

    periapsis_indices = filterPeriapses(
        time,
        r_sat,
        minima_indices,
        min_separation_hours=min_separation_hours
    )

    periapsis_times = time[periapsis_indices]

    return periapsis_times


#------------------------------------------------------------
# Function to print available orbits for a given date
# Orbit 1 is defined between periapsis 1 and periapsis 2,
# orbit 2 between periapsis 2 and periapsis 3, and so on
#------------------------------------------------------------

def printAvailableOrbits(periapsis_times: np.ndarray):
    """
    Prints the available complete orbits for a given date based on detected periapsis times.
    Orbit 1 is defined between periapsis 1 and periapsis 2, orbit 2 between periapsis 2 and periapsis 3, and so on.

    Parameters
    ----------
    periapsis_times : np.ndarray
        Array of detected periapsis times.
    
    Returns
    -------
    None
    """
    n_orbits = len(periapsis_times) - 1

    if n_orbits <= 0:
        print("No complete orbits were detected.")
        return

    print("Available complete orbits:")
    for i in range(n_orbits):
        print(f"Orbit {i + 1}: {periapsis_times[i]:.4f} h - {periapsis_times[i + 1]:.4f} h")


#------------------------------------------------------------
# Function to get the time limits of one orbit
#------------------------------------------------------------

def getOrbitTimeLimits(periapsis_times: np.ndarray, orbit_number: int) -> tuple[float, float]:
    """Returns the time limits of one orbit based on detected periapsis times.
    
    Parameters
    ----------
    periapsis_times : np.ndarray
        Array of detected periapsis times.
    orbit_number : int
        Orbit number inside the selected day. Orbit 1 is the interval between the first and second detected periapsis.
    
    Returns
    -------
    tuple[float, float]
        Time limits of the selected orbit.
    """
    n_orbits = len(periapsis_times) - 1

    if n_orbits <= 0:
        raise ValueError("No complete orbits were detected.")

    if orbit_number < 1 or orbit_number > n_orbits:
        raise ValueError(f"Orbit number must be between 1 and {n_orbits}.")

    t_start = periapsis_times[orbit_number - 1]
    t_end = periapsis_times[orbit_number]

    return t_start, t_end


#------------------------------------------------------------
# Function to cut a DataFrame using time limits
#------------------------------------------------------------

def cutDataFrameByTime(df: pd.DataFrame, t_start: float, t_end: float) -> pd.DataFrame:
    """
    Cuts a DataFrame using time limits, returning only the rows where the 'time' column is between t_start and t_end.

    Parameters
    ----------
    df : pandas.DataFrame
        DataFrame containing a 'time' column.
    t_start : float
        Start time limit.
    t_end : float
        End time limit.

    Returns
    -------
    pandas.DataFrame
        DataFrame containing only the rows where 'time' is between t_start and t_end, with reset index.
    """

    mask = (df["time"] >= t_start) & (df["time"] <= t_end)

    return df[mask].reset_index(drop=True)


#------------------------------------------------------------
# Function to cut SWEA flux matrix using the SWEA time mask
#------------------------------------------------------------

def cutFluxByTime(df_swea: pd.DataFrame, flux_energy_time: np.ndarray, t_start: float, t_end: float) -> np.ndarray:
    """
    Cuts the SWEA flux matrix using the SWEA time mask, returning only the rows of flux_energy_time where the corresponding time in df_swea is between t_start and t_end.
    
    Parameters
    ----------
    df_swea : pandas.DataFrame
        DataFrame containing a 'time' column corresponding to the time vector of flux_energy_time.
    flux_energy_time : np.ndarray
        SWEA differential energy flux averaged over angles, with shape (time, energy).
    t_start : float
        Start time limit.
    t_end : float
        End time limit.

    Returns
    -------
    np.ndarray
        SWEA flux matrix containing only the rows where the corresponding time in df_swea is between t_start and t_end, with shape (N_orbit, Ne).
    """
    mask = (df_swea["time"].to_numpy() >= t_start) & (df_swea["time"].to_numpy() <= t_end)

    return flux_energy_time[mask, :]


#------------------------------------------------------------
# Main function to get one orbit from MAG and SWEA data
#------------------------------------------------------------

def getOrbitData(YYYY: str, MM: str, DD: str, orbit_number: int) -> tuple[pd.DataFrame, pd.DataFrame, np.ndarray, np.ndarray]:
    """
    Returns MAG and SWEA data for one orbit of a given date.

    The orbit is defined using periapsis times estimated from the spacecraft
    altitude r_sat in the MAG data.

    Parameters
    ----------
    YYYY, MM, DD : str
        Date of the data files.

    orbit_number : int
        Orbit number inside the selected day.
        Orbit 1 is the interval between the first and second detected periapsis.

    Returns
    -------
    df_B_orbit : pandas.DataFrame
        Magnetic field and spacecraft position data for the selected orbit.

    df_swea_orbit : pandas.DataFrame
        SWEA time and quality data for the selected orbit.

    energy : np.ndarray
        SWEA energy vector.

    flux_orbit : np.ndarray
        SWEA differential energy flux averaged over angles for the selected orbit.
        Shape: (N_orbit, Ne).
    """

    df_B = organizeData(YYYY, MM, DD)
    df_swea, energy, flux_energy_time = organizeDataSWEA(YYYY, MM, DD)

    periapsis_times = findPeriapsisTimes(df_B)

    printAvailableOrbits(periapsis_times)

    t_start, t_end = getOrbitTimeLimits(periapsis_times, orbit_number)

    print()
    print(f"Selected orbit: {orbit_number}")
    print(f"t_start = {t_start:.4f} h")
    print(f"t_end   = {t_end:.4f} h")

    df_B_orbit = cutDataFrameByTime(df_B, t_start, t_end)
    df_swea_orbit = cutDataFrameByTime(df_swea, t_start, t_end)
    flux_orbit = cutFluxByTime(df_swea, flux_energy_time, t_start, t_end)

    print()
    print("Output sizes:")
    print("MAG orbit dataframe: ", df_B_orbit.shape)
    print("SWEA orbit dataframe:", df_swea_orbit.shape)
    print("SWEA flux matrix:    ", flux_orbit.shape)
    print("Energy vector:       ", energy.shape)

    return df_B_orbit, df_swea_orbit, energy, flux_orbit


#------------------------------------------------------------
# Main function to handle command line arguments
#------------------------------------------------------------

if __name__ == "__main__":

    if len(sys.argv) != 3:
        print("I use: python SeparateByOrbit.py YYYY-MM-DD orbit_number")
        sys.exit(1)

    date = sys.argv[1]
    orbit_number = int(sys.argv[2])

    YYYY, MM, DD = date.split("-")

    df_B_orbit, df_swea_orbit, energy, flux_orbit = getOrbitData(
        YYYY,
        MM,
        DD,
        orbit_number
    )