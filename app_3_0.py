from tkinter import Variable
from flask import Flask, request, jsonify, render_template
import os
import pickle
import pandas as pd
import sqlite3
import numpy as np
import json
from sklearn.metrics import accuracy_score
import pymysql 

# Para ingest_data
from flask_wtf import FlaskForm
from wtforms import FileField, SubmitField
from werkzeug.utils import secure_filename
from wtforms.validators import InputRequired


#DB='data/DB_futbol.db'
MODEL='modelos/gbc_model'


os.chdir(os.path.dirname(__file__))


app = Flask(__name__)
app.config['DEBUG'] = True

# Para ingest_data
app.config['UPLOAD_FOLDER'] = 'data'
app.config['SECRET_KEY'] = 'dontcopythis'
class UploadFileForm(FlaskForm):
    file = FileField("File", validators=[InputRequired()])
    submit = SubmitField("Upload File")


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


# --MOSTRAR TODOS LOS DATOS--
@app.route('/mostrar_datos', methods=['GET'])
def all_table():
    username = "admin"
    password = "12345678"
    host = "database-soccer.ckwuwtn1emlt.us-east-1.rds.amazonaws.com" 

    db = pymysql.connect(host = host,
                     user = username,
                     password = password,
                     cursorclass = pymysql.cursors.DictCursor)

    cursor = db.cursor()

    cursor.connection.commit()
    use_db = ''' USE DB_FURBOL'''
    cursor.execute(use_db)


    sql = '''SELECT * FROM DB_FURBOL'''
    cursor.execute(sql)
    result = cursor.fetchall()




#    connection = sqlite3.connect(DB)
#    cursor = connection.cursor()
#    select_all = "SELECT * FROM table_partidos"
#    result = cursor.execute(select_all).fetchall()
    db.close()
    return jsonify(result)


# --INGESTAR DATOS NUEVOS--
@app.route('/ingest_data', methods=['GET',"POST"])
def new_data():
    form = UploadFileForm()
    if form.validate_on_submit():
        # First grab the file
        list = form.file.data 
        # Save the file
        list.save(os.path.join(os.path.abspath(os.path.dirname(__file__)),app.config['UPLOAD_FOLDER'],secure_filename(list.filename))) # Then save the file
        
        # Open file
        with open('data/nuevos_datos.json','r') as f:
            data = json.loads(f.read())
        # Flatten data
        new_data_df = pd.json_normalize(data, record_path =['partidos'])


        username = "admin"
        password = "12345678"
        host = "database-soccer.ckwuwtn1emlt.us-east-1.rds.amazonaws.com" 

        db = pymysql.connect(host = host,
                        user = username,
                        password = password,
                        cursorclass = pymysql.cursors.DictCursor)

        cursor = db.cursor()

        cursor.connection.commit()
        use_db = ''' USE DB_FURBOL'''
        cursor.execute(use_db)


        sql = '''SELECT * FROM DB_FURBOL'''
        cursor.execute(sql)
        result = cursor.fetchall()


        #        sql = sqlite3.connect(DB)
        #        cursor = sql.cursor()

        lista_valores = new_data_df.values.tolist()
        cursor.executemany("INSERT INTO DB_FURBOL VALUES (?,?,?,?,?,?,?,?)", lista_valores)

        db.commit()
        db.close()

        return "File has been uploaded."
    return render_template('index.html', form=form)




# --VER ULTIMOS DATOS--
@app.route('/last_data', methods=["GET"])
def last_data():
    with open('data/nuevos_datos.json','r') as f:
            data = json.loads(f.read())
    
    return data

# --VER MEJOR ACCURACY--
@app.route('/best_acc', methods=["GET"])
def best_acc():
    
    best_accuracy_txt = open("data/best_accuracy.txt") 

    best_accuracy=float(best_accuracy_txt.read())    
    best_accuracy_txt.close()
    return 'La accuracy del mejor modelo es: '+str(best_accuracy)


# --MONITORIZACIÓN DEL MODELO CON NUEVOS DATOS--
@app.route('/monitor_new_dates', methods=["GET","POST"])
def monitor_new_data():

    username = "admin"
    password = "12345678"
    host = "database-soccer.ckwuwtn1emlt.us-east-1.rds.amazonaws.com" 

    db = pymysql.connect(host = host,
                     user = username,
                     password = password,
                     cursorclass = pymysql.cursors.DictCursor)

    cursor = db.cursor()

    cursor.connection.commit()
    use_db = ''' USE DB_FURBOL'''
    cursor.execute(use_db)


    sql = '''SELECT * FROM DB_FURBOL'''
    cursor.execute(sql)
    result = cursor.fetchall()


    # Conexión con DB
#    connection = sqlite3.connect(DB)
#    query = "SELECT * FROM table_partidos"
    # Leemos el JSON para utilizar su longitud
    with open('data/nuevos_datos.json','r') as f:
            data = json.loads(f.read())
    # Aplanamos los datos
    new_data_df = pd.json_normalize(data, record_path =['partidos'])

    # Leemos todos los datos de la tabla partidos
    df_partidos = pd.read_sql(sql, db)
    df_2 = pd.get_dummies(df_partidos[["home_team", "away_team"]])
    df_partidos_dummies=df_partidos.join(df_2)

    # Cogemos los últimos datos para el test
    df_test = df_partidos_dummies.iloc[-(len(new_data_df)):,7:]
    X_test=df_test.drop('result', axis=1)
    y_test=df_test['result']

    # Cargamos el modelo
    model = pickle.load(open(MODEL,'rb'))
    # Hacemos predicción
    y_pred = model.predict(X_test)
    # Sacamos la New Accuracy
    new_accuracy=(round(accuracy_score(y_test, y_pred),4))
    # Leemos la actual Best Accuracy
    best_accuracy_txt = open("data/best_accuracy.txt") 

    best_accuracy=float(best_accuracy_txt.read())    
    best_accuracy_txt.close()

    if new_accuracy >= best_accuracy:
        return 'El modelo sigue funcionando correctamente con los nuevos datos. La anterior accuracy era: '+str(best_accuracy)+' y con los nuevos datos es: '+str(new_accuracy)
    else:
        return 'La Accuracy Score ha disminuido. Se recomienda reentrenar el modelo. La anterior Accuracy era: '+ str(best_accuracy)+' y la nueva es: '+str(new_accuracy)



# --REENTRENAMIENTO--
@app.route('/retrain', methods=['PUT'])
def retrain():

    username = "admin"
    password = "12345678"
    host = "database-soccer.ckwuwtn1emlt.us-east-1.rds.amazonaws.com" 

    db = pymysql.connect(host = host,
                     user = username,
                     password = password,
                     cursorclass = pymysql.cursors.DictCursor)

    cursor = db.cursor()

    cursor.connection.commit()
    use_db = ''' USE DB_FURBOL'''
    cursor.execute(use_db)


    sql = '''SELECT * FROM DB_FURBOL'''
    cursor.execute(sql)
    # result = cursor.fetchall()


#    connection = sqlite3.connect(DB)
#    cursor = connection.cursor()
#    query = "SELECT * FROM table_partidos"
#    result = cursor.execute(query).fetchall()

    # Leemos todos los datos de la tabla partidos
    df_partidos = pd.read_sql(sql, db)
    df_2 = pd.get_dummies(df_partidos[["home_team", "away_team"]])
    df_partidos_dummies=df_partidos.join(df_2)

    db.close()

    # Leemos el JSON para utilizar su longitud
    with open('data/nuevos_datos.json','r') as f:
            data = json.loads(f.read())
    # Flatten data
    new_data_df = pd.json_normalize(data, record_path =['partidos'])

    # Dividimos train y test
    df_train = df_partidos_dummies.iloc[:,7:]
    df_test = df_partidos_dummies.iloc[(-(len(new_data_df)))-500:,7:]


    X_train=df_train.drop('result', axis=1)
    y_train=df_train['result']
    X_test=df_test.drop('result', axis=1)
    y_test=df_test['result']
    
    # Cargamos el modelo
    model = pickle.load(open(MODEL,'rb'))

    # Entrenamos modelo
    model.fit(X_train, y_train)

    # Predicción del nuevo modelo
    y_pred = model.predict(X_test)

    # Sacamos la New Accuracy
    new_accuracy=(round(accuracy_score(y_test, y_pred),4))
    # Leemos la Best Accuracy del anterior modelo
    best_accuracy_txt = open("data/best_accuracy.txt") 
    best_accuracy=float(best_accuracy_txt.read())    
    best_accuracy_txt.close()

    if new_accuracy>best_accuracy:
        # Guardar modelo
        with open('modelos/gbc_model', "wb") as archivo_salida:
            pickle.dump(model, archivo_salida)
        # Guardar Nueva Best Accuracy
        # Podría dar problemas en caso de que la Accuracy fuese 0 (generaría un txt vacío)
        new_accuracy = str(round(accuracy_score(y_test, y_pred),4))
        new_accuracy_txt = open('data/best_accuracy.txt', 'w')
        new_accuracy_txt.write(new_accuracy)
        new_accuracy_txt.close()

        return 'La Accuracy del nuevo modelo ha mejorado. Se han sobreescrito el modelo y la accuracy anteriores. La accuracy del anterior modelo era: '+str(best_accuracy)+' y la del nuevo modelo es: '+str(new_accuracy)
    
    else:
        return 'La Accuracy del nuevo modelo no ha mejorado. No se ejecutará ningún cambio. La accuracy del anterior modelo era: '+str(best_accuracy)+' y la del nuevo modelo es: '+str(new_accuracy)



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
    
    # Nombre de los equipos que jugarán el partido a predecir
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