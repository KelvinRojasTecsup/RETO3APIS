from flask import Flask, render_template, request, make_response, g
from redis import Redis
import os
import socket
import random
import json
import logging
import math
from math import sqrt
import csv

option_a = os.getenv('OPTION_A', "Manhattan")
option_b = os.getenv('OPTION_B', "Pearson")
hostname = socket.gethostname()


#FUNCIONES

#1
def manhattan(rating1, rating2):
  distance = 0
  total = 0
  for key in rating1:
      if key in rating2:
          distance += abs(rating1[key] - rating2[key])
          total += 1
  if total > 0:
      return distance / total
  else:
      return -1  # Indica que no hay calificaciones en común


#2
def pearson(rating1, rating2):
  n = len(rating1)
  if n == 0:
      return 0

  sum_x = sum(rating1.values())
  sum_y = sum(rating2.values())
  sum_xy = sum(rating1[movie] * rating2[movie] for movie in rating1 if movie in rating2)
  sum_x2 = sum(pow(rating1[movie], 2) for movie in rating1)
  sum_y2 = sum(pow(rating2[movie], 2) for movie in rating2)

  numerator = sum_xy - (sum_x * sum_y) / n

  denominator = sqrt(abs((sum_x2 - pow(sum_x, 2) / n) * (sum_y2 - pow(sum_y, 2) / n) + 1e-9))

  if denominator == 0:
      return 0

  similarity = numerator / denominator
  return similarity

#3
def euclidean(rating1, rating2):
    distance = 0
    common_ratings = False
    for key in rating1:
        if key in rating2:
            distance += pow(rating1[key] - rating2[key], 2)
            common_ratings = True
    if common_ratings:
        return math.sqrt(distance)
    else:
        return -1  # Indica que no hay calificaciones en común


#4
def cosine_similarity(rating1, rating2):
  dot_product = 0
  magnitude_rating1 = 0
  magnitude_rating2 = 0

  for key in rating1:
      if key in rating2:
          dot_product += rating1[key] * rating2[key]
          magnitude_rating1 += pow(rating1[key], 2)
          magnitude_rating2 += pow(rating2[key], 2)

  magnitude_rating1 = math.sqrt(magnitude_rating1)
  magnitude_rating2 = math.sqrt(magnitude_rating2)

  if magnitude_rating1 == 0 or magnitude_rating2 == 0:
      return 0
  else:
      return dot_product / (magnitude_rating1 * magnitude_rating2)
      
      

app = Flask(__name__)

gunicorn_error_logger = logging.getLogger('gunicorn.error')
app.logger.handlers.extend(gunicorn_error_logger.handlers)
app.logger.setLevel(logging.INFO)

def get_redis():
    if not hasattr(g, 'redis'):
        g.redis = Redis(host="redis", db=0, socket_timeout=5)
    return g.redis

def cargar_datos_desde_dat(ruta_dat):
    datos = {}
    with open(ruta_dat, 'r', encoding='utf-8') as archivo_dat:
        for linea in archivo_dat:
            userId, movieId, rating, timestamp = linea.strip().split('::')
            rating = float(rating)
            if userId not in datos:
                datos[userId] = {}
            datos[userId][movieId] = rating
    return datos

ruta_dat = 'ml-10M100K/ratings.dat'  # Cambia esto a la ubicación real de tu archivo DAT
usuarios = cargar_datos_desde_dat(ruta_dat)

@app.route("/", methods=['POST', 'GET'])
def distancias():
    voter_id = request.cookies.get('voter_id')
    if not voter_id:
        voter_id = hex(random.getrandbits(64))[2:-1]
    vote = None
    if request.method == 'POST':
        redis = get_redis()
        user_1 = request.form['option_a']
        user_2 = request.form['option_b']
        operation = request.form['operation']  # Obtener la operación seleccionada

        if user_1 in usuarios and user_2 in usuarios:
            if operation == 'manhattan':
                distancia = manhattan(usuarios[user_1], usuarios[user_2])
            elif operation == 'pearson':
                distancia = pearson(usuarios[user_1], usuarios[user_2])
            elif operation == 'euclidean':
                distancia = euclidean(usuarios[user_1], usuarios[user_2])
            elif operation == 'cosine':
                distancia = cosine_similarity(usuarios[user_1], usuarios[user_2])
            else:
                return "Operación no válida"

            data = json.dumps({'voter_id': voter_id, 'distancia': distancia})  # Enviar solo la distancia calculada
            redis.rpush('distancias', data)
        else:
            return "Usuarios no encontrados en los datos cargados desde el CSV"

    resp = make_response(render_template(
        'index.html',
        option_a=option_a,
        option_b=option_b,
        hostname=hostname,
    ))
    resp.set_cookie('voter_id', voter_id)
    return resp

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=80, debug=True, threaded=True)
