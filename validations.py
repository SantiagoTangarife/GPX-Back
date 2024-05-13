import json

import pandas as pd
from pathlib import Path
import os
import re
import math
from datetime import datetime, timedelta

class Validations:
    def __init__(self):
        self.penalizacion = timedelta()
        self.progress = -1
        self.pena = False
        self.ruta=[["wpnumber","Coor (Lat)", "Coor (Lon)", "CoorUS (Lat)", "CoorUS (Lon)","Radio"]]
        self.point=[]
        self.matrizPenalizacion = [["wpnumber", "Coor (Lat)", "Coor (Lon)", "CoorUS (Lat)", "CoorUS (Lon)", "Causa",
                                     "Valor Esperado", "Valor Usuario", "Penalizacion", "Penalizacion Total"]]
        self.row = []
        self.radio = 0
        self.totalTime=0

    def validations(self, file_path,rutagpx):
        ##El file_Path es un String con el Json que retorna el Front
        matrizCompleta = self.carga(file_path)
        matrizCompleta['latitude'] = self.dms_to_dd(matrizCompleta['latitude'])
        matrizCompleta['longitude'] = self.dms_to_dd(matrizCompleta['longitude'])
        gpxCorredor = self.gpxUsuario(rutagpx)

        self.matchWp(matrizCompleta, gpxCorredor)

        tiempoCarrera=self.segToHours(self.totalTime)

        df_ruta=pd.DataFrame(self.ruta[1:],columns=self.ruta[0])
        df_penalizacion = pd.DataFrame(self.matrizPenalizacion[1:], columns=self.matrizPenalizacion[0])

        mRuta=df_ruta

        mPenalizacion=df_penalizacion
        total=self.totalTime+self.penalizacion.total_seconds()

        total=self.segToHours(total)

        archivoJson=self.return_to_json(tiempoCarrera,mRuta,mPenalizacion,total)
        print(archivoJson)
        return archivoJson

    def return_to_json(self,tiempoCarrera,mRuta,mPenalizacion,total):
        ruta_json = mRuta.to_json(orient="records")
        penalizacion_json = mPenalizacion.to_json(orient="records")
        my_dict = {
            "tiempoCarrera": tiempoCarrera,
            "ruta": json.loads(ruta_json),
            "penalizacion": json.loads(penalizacion_json),
            "total": total
        }

        json_data = json.dumps(my_dict)


        return (json_data)


    # Función para convertir coordenadas DMS a DD
    def dms_to_dd(self, col):
        list=[]
        for i in col:
            i = re.sub(r'[^0-9NSEW.,°]', '', i)
            c=0
            grad=""
            mins=""
            pos=""
            for j in i:

                if (j=="°"):
                    c=1
                if (j==","):
                    c=2
                if (c==0):
                    grad+=j
                if(c==1):
                    mins+=j
                if(c==2):
                    pos+=j
            grad = float(grad)
            mins = float(mins[1:])
            pos= pos[1:]
            if (pos in ("N", "E")):
                result = grad + (mins / 60)
            else:
                result = (grad + (mins / 60)) * -1
            list.append(result)
        df = pd.DataFrame(list, columns=['latitude'])
        return df


    def carga(self, file_path):
        data = json.loads(file_path)  # Cargar el JSON desde el contenido

        waypoints_data = []

        for item in data:
            if "waypoints" in item:
                waypoints_data.extend(item["waypoints"])


        df = pd.DataFrame(waypoints_data)
        return df

    def gpxUsuario(self, ruta_archivo):
        # Verificar si se proporcionó una ruta de archivo
        if not ruta_archivo:
            print("No se proporcionó una ruta de archivo.")
            return None

        ruta_absoluta = Path(ruta_archivo)
        if not ruta_absoluta.is_file():
            print("El archivo seleccionado no existe.")
            return None

        with open(ruta_absoluta, "r") as archivo:
            contenido = archivo.read()

            # Buscar la primera  "lat="
            indice_inicio = contenido.find("lat=")

            if indice_inicio != -1:
                # Se encontró "lat=", obtener el contenido a partir de esa posición
                inicio = contenido[indice_inicio:]

                # para encontrar latitud, longitud y tiempo
                patron_latitud = r'lat="([^"]+)"'
                patron_longitud = r'lon="([^"]+)"'
                patron_tiempo = r'<time>([^<]+)</time>'

                # Encontrar todas las coincidencias de latitud, longitud y tiempo
                coincidencias_latitud = re.findall(patron_latitud, inicio)
                coincidencias_longitud = re.findall(patron_longitud, inicio)
                coincidencias_tiempo = re.findall(patron_tiempo, inicio)

                # guardo  en una matriz
                matriz_resultante = list(zip(coincidencias_latitud, coincidencias_longitud, coincidencias_tiempo))
                df = pd.DataFrame(matriz_resultante, columns=['lat', 'lon', 'time'])


                return df

            else:
                print("No se encontró 'lat=' en el archivo.")

        return None


    def segToHours(self, time):
        horas = int(time // 3600)  # Obtener la parte entera de la división
        minutos = int((time % 3600) // 60)  # Obtener los minutos
        segundos = int(time % 60)  # Obtener los segundos restantes



        return (f"{horas} horas, {minutos} minutos, {segundos} segundos")
    def totalTime2(self, time1,time2):
        # Strings de fecha y hora
        fecha_hora_str1 = time1
        fecha_hora_str2 = time2

        fecha_hora1 = datetime.fromisoformat(fecha_hora_str1.replace('Z', '+00:00'))
        fecha_hora2 = datetime.fromisoformat(fecha_hora_str2.replace('Z', '+00:00'))

        diferencia = fecha_hora2 - fecha_hora1

        return (diferencia.total_seconds())

    def matchEx(self, tupla,dataUser):

        for i, fila2 in dataUser.iterrows():
            if i < self.progress:
                continue
            tupla2 = (fila2['lat'], fila2['lon'])
            redondeado_tupla = tuple(round(float(coord), 3) for coord in tupla)
            redondeado_tupla2 = tuple(round(float(coord), 3) for coord in tupla2)


            if (redondeado_tupla == redondeado_tupla2 and (i-self.progress)<len(dataUser)/20):
                self.progress=i
                return (True,fila2)


        return (False,fila2)

    def neutral(self, tupla,dataUser,radio,tiempoN):
        mach=True
        while mach:
            c = 0
            for i, fila2 in dataUser.iterrows():
                if i <= self.progress:
                    c += 1
                    time1=fila2['time']

                    continue

                distancia_metros = self.distancia_euclidiana(tupla[0], tupla[1], fila2['lat'], fila2['lon'])
                rango = float(radio/1000)
                if (distancia_metros>rango):
                    time2=fila2['time']
                    timeT= self.totalTime2(time1, time2)
                    timeT=int(timeT/60)
                    timeT = math.floor(timeT)
                    mach=False
                    self.progress=i

                    break
        if(timeT<tiempoN-1):
            t=tiempoN-timeT
            t=math.floor(t*2)

            self.penalizacion+= timedelta(minutes=t)

            self.row.extend(["PENALIZACION NO NEUTRALIZACION", f"00:{tiempoN}:00", f"00:{timeT}:00", f"00:{t}:00", self.penalizacion])
            self.matrizPenalizacion.append( self.row)

    def match(self, tupla,dataUser,radio1,tiempo_str):
        long=len(dataUser)
        matchExatle= self.matchEx(tupla, dataUser)
        mach=matchExatle[0]

        self.pena=False
        while not mach:
            c=0
            min=500
            for i, fila2 in dataUser.iterrows():
                if i<=self.progress:
                    c+=1
                    continue
                distancia_metros = self.distancia_euclidiana(tupla[0], tupla[1], fila2['lat'], fila2['lon'])
                rango = float(radio1)#111320 porque 1 grado de longitud en la superficie de la Tierra equivale a aproximadamente 111320 metros
                if(radio1>radio1+75):
                    self.radio=None
                    return pd.DataFrame() #No hubo match
                if (distancia_metros < rango and self.progress<i ):
                    if (distancia_metros<= min):
                        min=distancia_metros
                        matchExatle = (True, fila2)
                        self.progress=i

                elif (distancia_metros > rango and matchExatle[0]):
                    mach = True
                    if (self.pena and tiempo_str is not None):
                        tiempo_str = datetime.strptime(tiempo_str, '%H:%M:%S')
                        self.penalizacion += timedelta(seconds=tiempo_str.second)
                        self.penalizacion += timedelta(minutes=tiempo_str.minute)
                        self.penalizacion += timedelta(hours=tiempo_str.hour)


                    break

                c+=1
                if (i==long-1):
                    if(min<1):
                        mach = True
                        if (self.pena and tiempo_str is not None):
                            tiempo_str = datetime.strptime(tiempo_str, '%H:%M:%S')
                            self.penalizacion += timedelta(seconds=tiempo_str.second)
                            self.penalizacion += timedelta(minutes=tiempo_str.minute)
                            self.penalizacion += timedelta(hours=tiempo_str.hour)

                        break

                    else:
                        radio1+=25 #aumento el radio para que lo capture
                        self.radio=radio1
                        mach=False
                        self.pena=True

        return (matchExatle[1])


    def matchWp(self, dataFWP,dataUser):

        inicio,final=None, None

        for index,fila1 in dataFWP.iterrows():

            self.row = []
            self.point=[]

            punto1 = (fila1['latitude'], fila1['longitude'])

            if(fila1['type']=='NaN' or fila1['type']==None ):
                continue


            self.row.extend([fila1['wpnumber'],round(fila1['latitude'], 3), round(fila1['longitude'], 3)])
            self.point.extend([fila1['wpnumber'],round(fila1['latitude'], 3), round(fila1['longitude'], 3)])

            MMU= self.match(punto1, dataUser, fila1['ratius'], fila1['penalization'])

            speedProm=0
            if not (MMU.empty):
                if index==0 and inicio is None:
                    inicio = MMU['time']

                final = MMU['time']

                punto2=(MMU['lat'],MMU['lon'])
                self.row.extend([round(float(MMU['lat']), 3), round(float(MMU['lon']), 3)])
                self.point.extend([round(float(MMU['lat']), 3), round(float(MMU['lon']), 3),int(fila1['ratius'])])

                if(fila1['type']=='N'):
                    self.neutral(punto1,dataUser,fila1['ratius'], int(datetime.strptime(fila1['neutralization'],'%H:%M:%S').minute))
                if (fila1['type']=='DZ'):
                    filaanterior=fila1['distance']
                    gti=MMU['time']
                elif (fila1['type']=='FZ'):
                    distancia=fila1['distance']-filaanterior
                    gtf = MMU['time']

                    speedProm=self.speed(distancia,gti,gtf)

                if self.pena:

                    self.row.extend(["PENALIZACION NO MATCH",str(int(fila1['ratius']))+" Mts",str(int(self.radio))+" Mts",fila1['penalization'],self.penalizacion])
                    self.matrizPenalizacion.append( self.row)


                if(speedProm>=float(fila1['speed'])+1 and not self.pena):        #si no se penaliza el NO MATCH
                    t=speedProm-float(fila1['speed'])
                    p=math.floor(t/10)
                    t+=(p*10)
                    t=math.floor(t)

                    self.penalizacion += timedelta(minutes=t)

                    self.row.extend(["PENALIZACION VELOCIDAD", str(int(fila1['speed']))+" Km/h", str(int(speedProm))+" Km/h", f"00:{t}:00", self.penalizacion])
                    self.matrizPenalizacion.append( self.row)



            else:

                if fila1['penalization'] is not None:
                    self.penalizacion += timedelta(seconds=fila1['penalization'].second)
                    self.penalizacion += timedelta(minutes=fila1['penalization'].minute)
                    self.penalizacion += timedelta(hours=fila1['penalization'].hour)
                self.point.extend([None,None,int(fila1['ratius'])])
                self.row.extend(["---","---","PENALIZACION NO MATCH", str(int(fila1['ratius']))+" Mts", None, fila1['penalization'], self.penalizacion])
                self.matrizPenalizacion.append(self.row)

            self.ruta.append(self.point)
        self.totalTime=self.totalTime2(inicio, final)


    def speed(self, distancia,gti,gtf):

        tiempo= self.totalTime2(gti, gtf)
        tiempo=tiempo/3600
        return (distancia/tiempo)

    def distancia_euclidiana(self, x1, y1, x2, y2):
        return math.sqrt(((float(x2) - float(x1))**2 + (float(y2) - float(y1))**2) * 111320)






