# ============================================================
# Sortering and ploting SWEA MAVEN L2 SVY3D - ventana 03:00–06:00 UTC
# ============================================================

import cdflib
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd

from pathlib import Path
import cdflib
import numpy as np


def inspect_cdf(YYYY: str, MM: str, DD: str):
    
    filepath = f'swea_files/mvn_swe_l2_svy3d_{YYYY}{MM}{DD}_v05_r01.cdf'
    file_path = Path(filepath)

    if not file_path.exists():
        raise FileNotFoundError(f"File doesn't exist: {file_path}")

    cdf = cdflib.CDF(str(file_path))
    info = cdf.cdf_info()

    print("=" * 70)
    print(f"Archivo: {file_path}")
    print("=" * 70)

    print("\nVariables:\n")

    for var in info.zVariables:
        try:
            data = cdf.varget(var)

            shape = data.shape if hasattr(data, "shape") else "scalar"
            dtype = data.dtype if hasattr(data, "dtype") else type(data)

            print(f"{var:35s} shape = {str(shape):20s} dtype = {dtype}")

        except Exception as e:
            print(f"{var:35s} ERROR when reading var: {e}")

    return cdf

from pathlib import Path

import cdflib
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.colors import LogNorm


def organize_swea_data(YYYY: str, MM: str, DD: str):
    
    filepath = f"swea_files/mvn_swe_l2_svy3d_{YYYY}{MM}{DD}_v05_r01.cdf"
    file_path = Path(filepath)

    if not file_path.exists():
        raise FileNotFoundError(f"File doesn't exist: {file_path}")

    cdf = cdflib.CDF(str(file_path))

    # ------------------------------------------------------------
    # Time variables
    # ------------------------------------------------------------
    epoch = cdf.varget("epoch")
    time_met = cdf.varget("time_met")
    time_unix = cdf.varget("time_unix")

    time = cdflib.cdfepoch.to_datetime(epoch)
    time = np.array(time, dtype="datetime64[ns]")

    # ------------------------------------------------------------
    # SWEA variables
    # ------------------------------------------------------------
    energy = cdf.varget("energy")
    quality = cdf.varget("quality")
    binning = cdf.varget("binning")

    diff_en_fluxes = cdf.varget("diff_en_fluxes")
    counts = cdf.varget("counts")

    # ------------------------------------------------------------
    # Angular average
    #
    # diff_en_fluxes[t, elev, azim, energy]
    #          -> flux_energy_time[t, energy]
    # ------------------------------------------------------------
    flux_energy_time = np.nanmean(diff_en_fluxes, axis=(1, 2))
    flux_energy_time = np.array(flux_energy_time, dtype=float)
    flux_energy_time[flux_energy_time <= 0] = np.nan

    counts_energy_time = np.nanmean(counts, axis=(1, 2))
    counts_energy_time = np.array(counts_energy_time, dtype=float)
    counts_energy_time[counts_energy_time <= 0] = np.nan

    # ------------------------------------------------------------
    # Main dataframe: one row per time
    # ------------------------------------------------------------
    df = pd.DataFrame({
        "time": time,
        "epoch": epoch,
        "time_met": time_met,
        "time_unix": time_unix,
        "quality": quality,
        "binning": binning,
    })

    # ------------------------------------------------------------
    # Flux dataframe: one row per time, one column per energy channel
    # ------------------------------------------------------------
    flux_columns = [f"flux_E{i:02d}" for i in range(len(energy))]

    df_flux = pd.DataFrame(
        flux_energy_time,
        columns=flux_columns
    )

    df_flux.insert(0, "time", time)

    # ------------------------------------------------------------
    # Counts dataframe
    # ------------------------------------------------------------
    counts_columns = [f"counts_E{i:02d}" for i in range(len(energy))]

    df_counts = pd.DataFrame(
        counts_energy_time,
        columns=counts_columns
    )

    df_counts.insert(0, "time", time)

    # ------------------------------------------------------------
    # Metadata
    # ------------------------------------------------------------
    metadata = {
        "file_path": str(file_path),
        "YYYY": YYYY,
        "MM": MM,
        "DD": DD,
        "date": f"{YYYY}-{MM}-{DD}",
        "product": "svy3d",
        "N": len(time),
        "Ne": len(energy),
        "Nel": diff_en_fluxes.shape[1],
        "Naz": diff_en_fluxes.shape[2],
    }

    return df, df_flux, df_counts, energy, metadata

def plot_swea_flux(
    df_flux,
    energy,
    metadata,
    hora_inicio=None,
    hora_fin=None,
    vmin=None,
    vmax=None,
    title=None,
):
    """
    Plotea un espectrograma SWEA energía-tiempo a partir de df_flux.

    Parameters
    ----------
    df_flux : pandas.DataFrame
        DataFrame con columna 'time' y columnas 'flux_E00', ..., 'flux_E63'.

    energy : array
        Vector de energías SWEA.

    metadata : dict
        Diccionario con información del archivo.

    hora_inicio : str or None
        Hora inicial en formato 'HH:MM:SS'. Si es None, usa inicio del archivo.

    hora_fin : str or None
        Hora final en formato 'HH:MM:SS'. Si es None, usa fin del archivo.

    vmin, vmax : float or None
        Límites de color para LogNorm.

    title : str or None
        Título del gráfico.
    """

    time = df_flux["time"].values

    flux_columns = [col for col in df_flux.columns if col.startswith("flux_E")]
    flux = df_flux[flux_columns].to_numpy()

    fecha = metadata["date"]

    if hora_inicio is not None:
        t0 = np.datetime64(f"{fecha}T{hora_inicio}")
    else:
        t0 = time[0]

    if hora_fin is not None:
        t1 = np.datetime64(f"{fecha}T{hora_fin}")
    else:
        t1 = time[-1]

    mask = (time >= t0) & (time <= t1)

    time_sel = time[mask]
    flux_sel = flux[mask, :]

    print("Ventana seleccionada:")
    print("t0 =", t0)
    print("t1 =", t1)
    print("Puntos seleccionados:", len(time_sel))
    print("flux_sel shape:", flux_sel.shape)

    if len(time_sel) == 0:
        raise ValueError("No hay datos en la ventana seleccionada.")

    plt.figure(figsize=(10, 5))

    plt.pcolormesh(
        time_sel,
        energy,
        flux_sel.T,
        shading="auto",
        norm=LogNorm(vmin=vmin, vmax=vmax)
    )

    plt.yscale("log")
    plt.colorbar(label="Differential energy flux")
    plt.xlabel("Time [UTC]")
    plt.ylabel("Energy [eV]")

    if title is None:
        if hora_inicio is None and hora_fin is None:
            title = f"MAVEN SWEA SVY3D - {fecha}"
        else:
            title = f"MAVEN SWEA SVY3D - {fecha} {hora_inicio}–{hora_fin} UTC"

    plt.title(title)
    plt.tight_layout()
    plt.savefig('temp.png')


df, df_flux, df_counts, energy, metadata = organize_swea_data("2016", "01", "01")

plot_swea_flux(
    df_flux=df_flux,
    energy=energy,
    metadata=metadata,
    hora_inicio="03:00:00",
    hora_fin="06:00:00"
)