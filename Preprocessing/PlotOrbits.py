#=============================================================
# Script to plot MAVEN MAG and SWEA data by orbit
#=============================================================

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.colors import LogNorm

from OrganizeB import organizeDataB
from OrganizeSWEA import organizeDataSWEA


#------------------------------------------------------------
# Function to find local minima in spacecraft altitude
# These minima are used as periapsis candidates
#------------------------------------------------------------

def findLocalMinima(time: np.ndarray, r_sat: np.ndarray) -> np.ndarray:
    minima_indices = []

    for i in range(1, len(r_sat) - 1):
        if r_sat[i] < r_sat[i - 1] and r_sat[i] < r_sat[i + 1]:
            minima_indices.append(i)

    return np.array(minima_indices)


#------------------------------------------------------------
# Function to filter periapsis candidates
# MAVEN orbital period is about 4.5 h
#------------------------------------------------------------

def filterPeriapses(
    time: np.ndarray,
    r_sat: np.ndarray,
    minima_indices: np.ndarray,
    min_separation_hours: float = 3.0
) -> np.ndarray:

    if len(minima_indices) == 0:
        return np.array([])

    selected_indices = [minima_indices[0]]

    for idx in minima_indices[1:]:
        last_idx = selected_indices[-1]
        delta_t = time[idx] - time[last_idx]

        if delta_t >= min_separation_hours:
            selected_indices.append(idx)

        else:
            if r_sat[idx] < r_sat[last_idx]:
                selected_indices[-1] = idx

    return np.array(selected_indices)


#------------------------------------------------------------
# Function to estimate periapsis times from MAG position data
#------------------------------------------------------------

def findPeriapsisTimes(df_B: pd.DataFrame) -> np.ndarray:
    time = df_B["time"].to_numpy()
    r_sat = df_B["r_sat"].to_numpy()

    minima_indices = findLocalMinima(time, r_sat)

    periapsis_indices = filterPeriapses(
        time,
        r_sat,
        minima_indices,
        min_separation_hours=3.0
    )

    periapsis_times = time[periapsis_indices]

    return periapsis_times


#------------------------------------------------------------
# Function to print the detected orbits
#------------------------------------------------------------

def printAvailableOrbits(periapsis_times: np.ndarray):
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

def getOrbitTimeLimits(
    periapsis_times: np.ndarray,
    orbit_number: int
) -> tuple[float, float]:

    n_orbits = len(periapsis_times) - 1

    if n_orbits <= 0:
        raise ValueError("No complete orbits were detected.")

    if orbit_number < 1 or orbit_number > n_orbits:
        raise ValueError(f"Orbit number must be between 1 and {n_orbits}.")

    t_start = periapsis_times[orbit_number - 1]
    t_end = periapsis_times[orbit_number]

    return t_start, t_end


#------------------------------------------------------------
# Function to cut a DataFrame between two times
#------------------------------------------------------------

def cutDataFrameByTime(
    df: pd.DataFrame,
    t_start: float,
    t_end: float
) -> pd.DataFrame:

    mask = (df["time"] >= t_start) & (df["time"] <= t_end)

    return df[mask].reset_index(drop=True)


#------------------------------------------------------------
# Function to cut SWEA flux matrix between two times
#------------------------------------------------------------

def cutFluxByTime(
    df_swea: pd.DataFrame,
    flux_energy_time: np.ndarray,
    t_start: float,
    t_end: float
) -> np.ndarray:

    time_swea = df_swea["time"].to_numpy()

    mask = (time_swea >= t_start) & (time_swea <= t_end)

    return flux_energy_time[mask, :]


#------------------------------------------------------------
# Function to plot Mars in the X-Z plane
# The plane y = 0 corresponds to the X-Z projection
#------------------------------------------------------------

def plotMarsXZ(ax, mars_radius: float = 3389.5):
    theta = np.linspace(0, 2 * np.pi, 400)

    x_mars = mars_radius * np.cos(theta)
    z_mars = mars_radius * np.sin(theta)

    ax.plot(x_mars, z_mars, color="black", linewidth=1.0)
    ax.fill(x_mars, z_mars, alpha=0.2)

    ax.set_aspect("equal", adjustable="box")
    ax.set_xlabel("X [km]")
    ax.set_ylabel("Z [km]")
    ax.set_title("Orbit projection in the y = 0 plane")


#------------------------------------------------------------
# Function to plot one orbit
#------------------------------------------------------------

def plotOneOrbit(
    df_B_orbit: pd.DataFrame,
    df_swea_orbit: pd.DataFrame,
    energy: np.ndarray,
    flux_orbit: np.ndarray,
    YYYY: str,
    MM: str,
    DD: str,
    orbit_number: int,
    save_plot: bool = False,
    output_dir: str = "orbit_plots",
    vmin: float | None = None,
    vmax: float | None = None
):

    if len(df_B_orbit) == 0:
        raise ValueError("MAG dataframe is empty for this orbit.")

    if len(df_swea_orbit) == 0:
        raise ValueError("SWEA dataframe is empty for this orbit.")

    time_B = df_B_orbit["time"].to_numpy()
    time_swea = df_swea_orbit["time"].to_numpy()

    fig, axs = plt.subplots(
        4,
        1,
        figsize=(12, 14),
        constrained_layout=True
    )

    fig.suptitle(
        f"MAVEN orbit {orbit_number} - {YYYY}-{MM}-{DD}",
        fontsize=14
    )

    #--------------------------------------------------------
    # Panel 1: magnetic field modulus
    #--------------------------------------------------------

    axs[0].plot(time_B, df_B_orbit["mod_B"], linewidth=1.0)

    axs[0].set_ylabel("|B| [nT]")
    axs[0].set_xlabel("Time [h]")
    axs[0].set_title("Magnetic field modulus")
    axs[0].grid(True)

    #--------------------------------------------------------
    # Panel 2: magnetic field components
    #--------------------------------------------------------

    axs[1].plot(time_B, df_B_orbit["Bx"], label="Bx", linewidth=1.0)
    axs[1].plot(time_B, df_B_orbit["By"], label="By", linewidth=1.0)
    axs[1].plot(time_B, df_B_orbit["Bz"], label="Bz", linewidth=1.0)

    axs[1].set_ylabel("B [nT]")
    axs[1].set_xlabel("Time [h]")
    axs[1].set_title("Magnetic field components")
    axs[1].legend()
    axs[1].grid(True)

    #--------------------------------------------------------
    # Panel 3: SWEA energy flux spectrogram
    #--------------------------------------------------------

    mesh = axs[2].pcolormesh(
        time_swea,
        energy,
        flux_orbit.T,
        shading="auto",
        norm=LogNorm(vmin=vmin, vmax=vmax)
    )

    axs[2].set_yscale("log")
    axs[2].set_ylabel("Energy [eV]")
    axs[2].set_xlabel("Time [h]")
    axs[2].set_title("SWEA differential energy flux")

    cbar = fig.colorbar(mesh, ax=axs[2])
    cbar.set_label("Differential energy flux")

    #--------------------------------------------------------
    # Panel 4: orbit projection in y = 0 plane
    #--------------------------------------------------------

    plotMarsXZ(axs[3])

    axs[3].plot(
        df_B_orbit["posX"],
        df_B_orbit["posZ"],
        linewidth=1.0
    )

    axs[3].scatter(
        df_B_orbit["posX"].iloc[0],
        df_B_orbit["posZ"].iloc[0],
        s=25,
        label="Start"
    )

    axs[3].scatter(
        df_B_orbit["posX"].iloc[-1],
        df_B_orbit["posZ"].iloc[-1],
        s=25,
        label="End"
    )

    axs[3].legend()
    axs[3].grid(True)

    #--------------------------------------------------------
    # Save or show
    #--------------------------------------------------------

    if save_plot:
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)

        filename = f"MAVEN_{YYYY}{MM}{DD}_orbit_{orbit_number:02d}.png"
        file_path = output_path / filename

        plt.savefig(file_path, dpi=200)
        print(f"Saved plot: {file_path}")

        plt.close(fig)

    else:
        plt.show()


#------------------------------------------------------------
# Function to plot all complete orbits of one date
#------------------------------------------------------------

def plotOrbitsByDate(
    YYYY: str,
    MM: str,
    DD: str,
    save_plot: bool = False,
    output_dir: str = "orbit_plots",
    vmin: float | None = None,
    vmax: float | None = None
):

    df_B = organizeDataB(YYYY, MM, DD)
    df_swea, energy, flux_energy_time = organizeDataSWEA(YYYY, MM, DD)

    periapsis_times = findPeriapsisTimes(df_B)

    printAvailableOrbits(periapsis_times)

    n_orbits = len(periapsis_times) - 1

    if n_orbits <= 0:
        raise ValueError("No complete orbits were detected.")

    for orbit_number in range(1, n_orbits + 1):
        t_start, t_end = getOrbitTimeLimits(periapsis_times, orbit_number)

        print()
        print(f"Plotting orbit {orbit_number}")
        print(f"t_start = {t_start:.4f} h")
        print(f"t_end   = {t_end:.4f} h")

        df_B_orbit = cutDataFrameByTime(df_B, t_start, t_end)
        df_swea_orbit = cutDataFrameByTime(df_swea, t_start, t_end)
        flux_orbit = cutFluxByTime(df_swea, flux_energy_time, t_start, t_end)

        print("MAG orbit dataframe: ", df_B_orbit.shape)
        print("SWEA orbit dataframe:", df_swea_orbit.shape)
        print("SWEA flux matrix:    ", flux_orbit.shape)

        plotOneOrbit(
            df_B_orbit=df_B_orbit,
            df_swea_orbit=df_swea_orbit,
            energy=energy,
            flux_orbit=flux_orbit,
            YYYY=YYYY,
            MM=MM,
            DD=DD,
            orbit_number=orbit_number,
            save_plot=save_plot,
            output_dir=output_dir,
            vmin=vmin,
            vmax=vmax
        )


#------------------------------------------------------------
# Main function to handle command line arguments
#------------------------------------------------------------

if __name__ == "__main__":

    if len(sys.argv) not in (2, 3):
        print("I use: python PlotOrbits.py YYYY-MM-DD save")
        print("The second argument is optional. Use save to save figures.")
        sys.exit(1)

    date = sys.argv[1]
    YYYY, MM, DD = date.split("-")

    save_plot = False

    if len(sys.argv) == 3:
        if sys.argv[2] == "save":
            save_plot = True
        else:
            raise ValueError("The second argument must be 'save'.")

    plotOrbitsByDate(
        YYYY,
        MM,
        DD,
        save_plot=save_plot
    )