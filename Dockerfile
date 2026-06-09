#Empiezo a armar la imagen a partir de la que existe de base para python
FROM python:3.10-slim

#indinco en donde trabajan los pasos de crear la imagen
WORKDIR /app

#copio las cosas que estan en mi pc que necesita el conteiner
COPY ./requirements.txt ./requirements.txt

#instalar las librerias con pip (con comandos de linux)
RUN pip install -r requirements.txt

CMD "/bin/bash" 