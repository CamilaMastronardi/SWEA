
#=============================================================
# Script to organize magnetic field data from MAVEN mission
#=============================================================

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import sys

#------------------------------------------------------------
# Column names for the magnetic field data
#------------------------------------------------------------
col_names = ["year","day_number","hour","minute", "second", "milisecond", "decimal_day", "Bx", "By", "Bz", "Brange", "posX", "posY", "posZ", "motorX", "motorY", "motorZ", "motor_range"]

#------------------------------------------------------------
# Function to organize magnetic field data for a given date in a pandas DataFrame with
# columns: time, mod_B, Bx, By, Bz, r_sat, posX, posY, posZ
#------------------------------------------------------------

def organizeDataB(YYYY: str,MM: str,DD: str) -> pd.DataFrame:
  """
  Reads and organizes magnetic field data from a CSV file for a given date.
  The function extracts the time, magnetic field components, and position information.

  Parameters
  ----------
  YYYY, MM, DD : str
      date in the format 'YYYY', 'MM', 'DD' to locate the corresponding CSV file.

  Returns
  -------
  df_b : pandas.DataFrame
      DataFrame with columns: time, mod_B, Bx, By, Bz, r_sat, posX, posY, posZ
  """

  df = pd.read_csv(f'/app/magnetic_field_data/raw_data_magnetic_field_ss/data_{DD}-{MM}-{YYYY}.csv', sep='\s+',skiprows=0, header=None, lineterminator='\n', names = col_names, usecols=['year','day_number', 'hour', 'minute', 'second', 'milisecond', 'Bx', 'By', 'Bz', 'Brange', 'posX', 'posY', 'posZ'])
  month = round(df.day_number/30) + 1
  day = df.day_number - (month-1)
  
  hour = df.hour
  minute = df.minute
  second = df.second
  milisecond = df.milisecond
  
  time = hour + minute/60 + second/3600 + milisecond/3600000 #tiempo en horas
  
  B_vector = np.array([df.Bx,df.By,df.Bz]).transpose()
  B_norm = np.zeros(len(B_vector[:,0]))
  for i in range(len(B_vector[:,0])):
      B = np.linalg.norm(B_vector[i])
      B_norm [i] = B
  
  mars_radius = 3389.5
  r_vector= np.array([df.posX,df.posY,df.posZ]).transpose()
  r_sat = np.zeros(len(B_vector[:,0]))
  for i in range(len(B_vector[:,0])):
      r = np.linalg.norm(r_vector[i])
      r_sat [i] = r - mars_radius
  
  return pd.DataFrame({'time': time, 'mod_B': B_norm, 'Bx': df.Bx, 
  'By': df.By, 'Bz': df.Bz, 'r_sat': r_sat, 'posX': df.posX, 'posY': df.posY, 'posZ': df.posZ})[:-1]

#------------------------------------------------------------
# Main function to handle command line arguments and organize data
#------------------------------------------------------------

if __name__== '__main__' :

  if len(sys.argv) !=2: 
        print("I use: python OrganizeB.py YYYY-MM-DD")
        sys.exit(1) 

  if len(sys.argv) == 2:
    fecha = sys.argv[1] 
    YYYY, MM, DD = fecha.split('-')
    organizeDataB(YYYY,MM,DD)
