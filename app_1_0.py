from flask import Flask, request, jsonify
import os
import pickle
from sklearn.model_selection import cross_val_score
import pandas as pd
import sqlite3
import numpy as np

DB='data/DB_futbol.db'
MODEL='modelos/gbc_model'

os.chdir(os.path.dirname(__file__))

app = Flask(__name__)
app.config['DEBUG'] = True

# --HOME--
@app.route("/", methods=['GET'])
def hello():
    return "<h1>Bienvenido a la página principal del modelo predictivo de resultados de fútbol</h1>\
        <p><h2>Ejemplo para introducción de datos:</h2></p>\
        <p><h3>1- season: 2008/2009</h3></p>\
        <p><h3>2- date: 2008-08-30</h3></p>\
        <p><h3>3- country_name: Spain</h3></p>\
        <p><h3>4- home_team: Valencia CF</h3></p>\
        <p><h3>5- away_team: RCD Mallorca</h3></p>\
        <p><h3>6- result: 1</h3></p>\
        <p><h2>RESULTADOS:</h2></p>\
        <p> Gana el local = 1</p>\
        <p> Gana el visitante = 2</p>\
        <p> Empate = 0</p>\
        <p><h2>NOMBRE DE LOS EQUIPOS:</h2></p>\
        <p> Athletic Club de Bilbao || Atlético Madrid || CA Osasuna || CD Numancia || CD Tenerife || Córdoba CF || Elche CF</p>\
        <p>FC Barcelona || Getafe CF || Granada CF || Hércules Club de Fútbol || Levante UD || Málaga CF || RC Celta de Vigo</p>\
        <p>Elche CF || RC Deportivo de La Coruña || RC Recreativo || RCD Espanyol || RCD Mallorca || Racing Santander || Rayo Vallecano,</p>\
        <p>Real Betis Balompié || Real Madrid CF || Real Sociedad || Real Sporting de Gijón || Real Valladolid || Real Zaragoza</p>\
        <p>SD Eibar || Sevilla FC || UD Almería || UD Las Palmas || Valencia CF || Villarreal CF || Xerez Club Deportivo</p>"
            


# --PRUEBA ALL--
@app.route('/mostrar_datos', methods=['GET'])
def all_table():
    connection = sqlite3.connect(DB)
    cursor = connection.cursor()
    select_all = "SELECT * FROM table_partidos"
    result = cursor.execute(select_all).fetchall()
    connection.close()
    return jsonify(result)

# --INGESTAR DATOS NUEVOS--
@app.route('/ingest_data', methods=["POST"])
def new_data():

    season = request.args.get('season', None)
    date = request.args.get('date', None)

    country_name = request.args.get('country_name', None)
    home_team = request.args.get('home_team', None)

    away_team = request.args.get('away_team', None)
    home_team_goal = int(request.args.get('home_team_goal', 0))

    away_team_goal = int(request.args.get('away_team_goal', 0))
    result = int(request.args.get('result', None))

    valores=(season, date, country_name, home_team, away_team, home_team_goal, away_team_goal, result)

    connection = sqlite3.connect(DB)
    cursor = connection.cursor()
    query = "INSERT INTO table_partidos VALUES (?, ?, ?, ?, ?, ?, ?, ?)"
    cursor.execute(query, valores).fetchall()
    query = "SELECT * FROM table_partidos"
    result = cursor.execute(query).fetchall()
    
    # QUITAR COMENTARIO PARA QUE GUARDE LOS NUEVOS DATOS AL CERRAR
    # connection.commit()
    # connection.close()
    return jsonify(result)

# --MONITORIZACIÓN DEL MODELO CON NUEVOS DATOS--

# --REENTRENAMIENTO--


# --PREDICCIÓN--
@app.route('/predict', methods=['GET'])
def predict():
    model = pickle.load(open(MODEL,'rb'))
    lista_equipos = []

    # Leer lista de equipos
    with open(r'data/lista_equipos.txt', 'r') as fp:
        for line in fp:
            # remove linebreak from a current name
            x = line[:-1]
            # add current item to the list
            lista_equipos.append(x)
    
    
    home_team = request.args.get('home_team', None)
    away_team = request.args.get('away_team', None)
    
    if home_team is None or away_team is None:
        return "Faltan argumentos para realizar la predicción"

    elif home_team not in lista_equipos or away_team not in lista_equipos:
        return "El equipo no existe. \nComprueba que esté escrito correctamente.\n"+"LISTA DE EQUIPOS:\n"+str(lista_equipos)

    else:
        lista_columnas_dummies = []

        # Leer lista_columnas_dummies
        with open(r'data/lista_columnas_dummies.txt', 'r') as fp:
            for line in fp:
                # remove linebreak from a current name
                x = line[:-1]
                # add current item to the list
                lista_columnas_dummies.append(x)
        # Crea df de dummies
        df = (pd.DataFrame(np.zeros((1, len(lista_columnas_dummies))),columns=lista_columnas_dummies)).astype(int)
        # Modifica el df de dummies con los equipos de la predicción
        colum_home='home_team_'+str(home_team)
        colum_away='away_team_'+str(away_team)
        df[colum_home]=1
        df[colum_away]=1


        prediction = model.predict(df)
        predict_texto = ''
        if prediction == 0:
            predict_texto = ' Empate'
        elif prediction == 1:
            predict_texto = ' Gana el equipo local: '+ str(home_team)
        else:
            predict_texto = ' Gana el equipo visitante: '+ str(away_team)
        return "La predicción para el partido "+str(home_team)+" vs "+ str(away_team)+ " es :"+str(prediction)+"."+str(predict_texto)


# (--EJECUTAR--)
app.run()
