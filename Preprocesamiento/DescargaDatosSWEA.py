# ============================================================
# Plot SWEA MAVEN L2 SVY3D - ventana 03:00–06:00 UTC
# ============================================================

import urllib.request
from pathlib import Path

import cdflib
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import LogNorm


# ------------------------------------------------------------
# 1. Configuración del archivo
# ------------------------------------------------------------

data_dir = Path("datos_swea")
data_dir.mkdir(exist_ok=True)

base_url = "https://lasp.colorado.edu/maven/sdc/public/data/sci/swe/l2/2019/06/"

# Cambiar acá el día si querés otro archivo
filename = "mvn_swe_l2_svy3d_20190609_v05_r01.cdf"

url = base_url + filename
file_path = data_dir / filename


# ------------------------------------------------------------
# 2. Descargar archivo si no existe
# ------------------------------------------------------------

if not file_path.exists():
    print("Descargando archivo...")
    urllib.request.urlretrieve(url, file_path)
    print("Descarga terminada.")
else:
    print("El archivo ya existe.")

print("Archivo:", file_path)


# ------------------------------------------------------------
# 3. Abrir archivo CDF
# ------------------------------------------------------------

cdf = cdflib.CDF(str(file_path))


# ------------------------------------------------------------
# 4. Leer variables principales
# ------------------------------------------------------------

epoch = cdf.varget("epoch")
energy = cdf.varget("energy")
flux = cdf.varget("diff_en_fluxes")

print("epoch shape: ", epoch.shape)
print("energy shape:", energy.shape)
print("flux shape:  ", flux.shape)


# ------------------------------------------------------------
# 5. Convertir tiempo CDF a numpy.datetime64
# ------------------------------------------------------------

time = cdflib.cdfepoch.to_datetime(epoch)

# Asegurarse de que sea array de numpy.datetime64
time = np.array(time, dtype="datetime64[ns]")

print("Inicio archivo:", time[0])
print("Fin archivo:   ", time[-1])


# ------------------------------------------------------------
# 6. Promediar sobre ángulos
#
# diff_en_fluxes tiene dimensiones:
#     flux[t, elev, azim, energy]
#
# Queremos:
#     flux_avg[t, energy]
# ------------------------------------------------------------

flux_avg = np.nanmean(flux, axis=(1, 2))

print("flux_avg shape:", flux_avg.shape)


# ------------------------------------------------------------
# 7. Limpiar valores no físicos para escala logarítmica
# ------------------------------------------------------------

flux_avg = np.array(flux_avg, dtype=float)
flux_avg[flux_avg <= 0] = np.nan


# ------------------------------------------------------------
# 8. Seleccionar ventana temporal: 03:00–06:00 UTC
#
# La fecha se toma automáticamente desde el archivo.
# ------------------------------------------------------------

fecha = str(time[0])[:10]

t0 = np.datetime64(fecha + "T03:00:00")
t1 = np.datetime64(fecha + "T06:00:00")

mask = (time >= t0) & (time <= t1)

time_orbit = time[mask]
flux_orbit = flux_avg[mask, :]

print("Ventana seleccionada:")
print("t0 =", t0)
print("t1 =", t1)
print("Puntos seleccionados:", len(time_orbit))
print("flux_orbit shape:", flux_orbit.shape)

if len(time_orbit) == 0:
    raise ValueError("No hay datos en la ventana temporal seleccionada.")


# ------------------------------------------------------------
# 9. Plot espectrograma energía-tiempo
# ------------------------------------------------------------

plt.figure(figsize=(10, 5))

plt.pcolormesh(
    time_orbit,
    energy,
    flux_orbit.T,
    shading="auto",
    norm=LogNorm()
)

plt.yscale("log")
plt.colorbar(label="Differential energy flux")
plt.xlabel("Time [UTC]")
plt.ylabel("Energy [eV]")
plt.title(f"MAVEN SWEA - SVY3D - {fecha} 03:00–06:00 UTC")

plt.tight_layout()
plt.savefig("swea_spectrogram.png", dpi=300)