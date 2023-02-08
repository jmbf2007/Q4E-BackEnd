# Sistema a ser utilizado
FROM ubuntu:latest
LABEL 'Creador'="Q4E"

# Copiamos todos los archivos que se encuentran en la carpeta actual al directorio /Q4E del contenedor
COPY . /Q4E

# Actualizamos el sistema
RUN apt-get update

# Instalamos las herramientas net-tools y curl
RUN apt-get install -y net-tools

RUN apt-get install -y curl

# Instalamos python3 y pip3
RUN apt-get install -y python3 python3-pip

# Establecemos el directorio de trabajo Q4E
WORKDIR /Q4E

# Instalamos las dependencias de python
RUN pip3 install -r requirements.txt

RUN python3 -m pip install "pymongo[srv]"

# Guardamos la ip en una variable
#ENTRYPOINT ["export", "IP=$(curl -s ifconfig.me)"]

# Imprimimos la ip
#RUN echo $IP

# Arrancamos el servicio uvicorn 
#CMD ["uvicorn", "main:app", "--host", "${IP}", "--port", "80"]

# Exponemos el puerto 80
#EXPOSE 80





