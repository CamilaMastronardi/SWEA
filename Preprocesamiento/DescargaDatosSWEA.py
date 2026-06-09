import cdflib

cdf = cdflib.CDF("archivo.cdf")

print(cdf.cdf_info())

variables = cdf.cdf_info()["zVariables"]
print(variables)

B = cdf.varget("B")