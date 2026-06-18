import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import sys

col_names = ["año","nro_día","hora","minuto", "segundo", "milisegundo", "dia decimal", "Bx", "By", "Bz", "rangoB", "posX", "posY", "posZ", "motorX", "motorY", "motorZ", "rango_motor"]

def acomodarDatos(YYYY: str,MM: str,DD: str, res = 1) -> pd.DataFrame:
  if res == 1:
    df = pd.read_csv(f'/app/DatosCrudos/datos_campo_magnetico_crudos/datos_{DD}-{MM}-{YYYY}.csv', sep='\s+',skiprows=0, header=None, lineterminator='\n', names = col_names, usecols=['año','nro_día', 'hora', 'minuto', 'segundo', 'milisegundo', 'Bx', 'By', 'Bz', 'rangoB', 'posX', 'posY', 'posZ'])
  else:
    df = pd.read_csv(f'/app/DatosCrudos/datos_campo_magnetico_crudos_full/datos_{DD}-{MM}-{YYYY}.csv', sep='\s+',skiprows=0, header=None, lineterminator='\n', names = col_names, usecols=['año','nro_día', 'hora', 'minuto', 'segundo', 'milisegundo', 'Bx', 'By', 'Bz', 'rangoB', 'posX', 'posY', 'posZ'])
  mes = round(df.nro_día/30) + 1
  dia = df.nro_día - (mes-1)
  
  hora = df.hora
  minuto = df.minuto
  seg = df.segundo
  miliseg = df.milisegundo
  
  time = hora + minuto/60 + seg/3600 + miliseg/3600000 #tiempo en horas
  
  B_vector = np.array([df.Bx,df.By,df.Bz]).transpose()
  B_norm = np.zeros(len(B_vector[:,0]))
  for i in range(len(B_vector[:,0])):
      B = np.linalg.norm(B_vector[i])
      B_norm [i] = B
  
  radio_marte_prom = 3389.5
  r_vector= np.array([df.posX,df.posY,df.posZ]).transpose()
  r_sat = np.zeros(len(B_vector[:,0]))
  for i in range(len(B_vector[:,0])):
      r = np.linalg.norm(r_vector[i])
      r_sat [i] = r - radio_marte_prom
  
  return pd.DataFrame({'time': time, 'mod_B': B_norm, 'Bx': df.Bx, 
  'By': df.By, 'Bz': df.Bz, 'r_sat': r_sat, 'posX': df.posX, 'posY': df.posY, 'posZ': df.posZ})[:-1]

if __name__== '__main__' :

  if len(sys.argv) !=2: #se fija que se haya ingresado un parametro despues del nombre del programa (argv[0])
        print("Uso: python acomodarDatosB.py YYYY-MM-DD")
        sys.exit(1) #sale del programa
    # Pide al usuario que ingrese la fecha en formato YYYY-MM-DD
    
  if len(sys.argv) == 2:
    fecha = sys.argv[1] #Usa el argumento indicado para ejecutar el programa
    YYYY, MM, DD = fecha.split('-')
  # Llama a la función para acomodar datos
    acomodarDatos(YYYY,MM,DD)
