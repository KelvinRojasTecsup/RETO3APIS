from flask import Flask, render_template, request, make_response, g
from redis import Redis
import os
import socket
import random
import json
import logging
import math
import requests

option_a = os.getenv('OPTION_A', "Manhattan")
option_b = os.getenv('OPTION_B', "Pearson")
hostname = socket.gethostname()

# FUNCIONES

# 1
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


# 2
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


# 3
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


# 4
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

def cargar_datos_desde_api(api_url):
    response = requests.get(api_url)
    if response.status_code == 200:
        datos = {}
        for rating_data in response.json():
            userId = str(rating_data["userId"])
            movieId = str(rating_data["movieId"])
            rating = float(rating_data["rating"])
            if userId not in datos:
                datos[userId] = {}
            datos[userId][movieId] = rating
        return datos
    else:
        raise Exception("Error al obtener datos desde la API")

api_url = 'http://ip172-18-0-43-clf9v9efml8g00e3gglg-5000.direct.labs.play-with-docker.com/ratings'
usuarios = cargar_datos_desde_api(api_url)

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
        operation = request.form['operation']

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

            data = json.dumps({'voter_id': voter_id, 'distancia': distancia})
            redis.rpush('distancias', data)
        else:
            return "Usuarios no encontrados en los datos cargados desde la API"

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
