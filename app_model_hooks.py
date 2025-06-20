import os
import pickle
import subprocess

import numpy as np
import pandas as pd
from flask import Flask, jsonify, request
from sklearn.linear_model import Lasso
from sklearn.metrics import mean_absolute_percentage_error, mean_squared_error
from sklearn.model_selection import train_test_split

os.chdir(os.path.dirname(__file__))


app = Flask(__name__)
app.config["DEBUG"] = True


# Enruta la landing page (endpoint /)
@app.route("/", methods=["GET"])
def hello():
    return "Bienvenido a mi API del modelo advertising :-)))))))) "


# Enruta la funcion al endpoint /api/v1/predict


"""
La petición de prueba sería:
http://127.0.0.1:5000/api/v1/predict?radio=15&newspaper=60&tv=80
"""


@app.route("/api/v1/predict", methods=["GET"])
def predict():  # Ligado al endpoint '/api/v1/predict', con el método GET
    model = pickle.load(open("ad_model.pkl", "rb"))
    tv = request.args.get("tv", None)
    radio = request.args.get("radio", None)
    newspaper = request.args.get("newspaper", None)

    print(tv, radio, newspaper)
    print(type(tv))

    if tv is None or radio is None or newspaper is None:
        return "Args empty, the data are not enough to predict, STUPID!!!!"
    else:
        prediction = model.predict([[float(tv), float(radio), float(newspaper)]])

    return jsonify({"predictions": prediction[0]})


"""
La petición de prueba sería:
http://127.0.0.1:5000/api/v1/retrain
"""


@app.route("/api/v1/retrain", methods=["GET"])
# Enruta la funcion al endpoint /api/v1/retrain
def retrain():  # Rutarlo al endpoint '/api/v1/retrain/', metodo GET
    if os.path.exists("data/Advertising_new.csv"):
        data = pd.read_csv("data/Advertising_new.csv")

        X_train, X_test, y_train, y_test = train_test_split(
            data.drop(columns=["sales"]), data["sales"], test_size=0.20, random_state=42
        )

        model = Lasso(alpha=6000)
        model.fit(X_train, y_train)
        rmse = np.sqrt(mean_squared_error(y_test, model.predict(X_test)))
        mape = mean_absolute_percentage_error(y_test, model.predict(X_test))
        model.fit(data.drop(columns=["sales"]), data["sales"])
        pickle.dump(model, open("ad_model.pkl", "wb"))

        return f"Model retrained. New evaluation metric RMSE: {str(rmse)}, MAPE: {str(mape)}"
    else:
        return "<h2>New data for retrain NOT FOUND. Nothing done!</h2>"


# cambiado 123!!!


@app.route("/webhook", methods=["POST"])
def webhook():
    # Ruta al repositorio donde se realizará el pull
    # path_repo = "/ruta/a/tu/repositorio/en/PythonAnywhere"
    path_repo = "/home/prueba83/arv-github/myFlaskApp"
    # servidor_web = "/ruta/al/fichero/WSGI/de/configuracion"
    servidor_web = "/var/www/prueba83_pythonanywhere_com_wsgi.py"

    # Comprueba si la solicitud POST contiene datos JSON
    if request.is_json:
        payload = request.json
        # Verifica si la carga útil (payload) contiene información sobre el repositorio
        if "repository" in payload:
            # Extrae el nombre del repositorio y la URL de clonación
            repo_name = payload["repository"]["name"]
            clone_url = payload["repository"]["clone_url"]

            # Cambia al directorio del repositorio
            try:
                os.chdir(path_repo)
            except FileNotFoundError:
                return jsonify(
                    {"message": "El directorio del repositorio no existe"}
                ), 404

            # Realiza un git pull en el repositorio
            try:
                subprocess.run(["git", "pull", clone_url], check=True)
                subprocess.run(
                    ["touch", servidor_web], check=True
                )  # Trick to automatically reload PythonAnywhere WebServer
                return jsonify(
                    {"message": f"Se realizó un git pull en el repositorio {repo_name}"}
                ), 200
            except subprocess.CalledProcessError:
                return jsonify(
                    {
                        "message": f"Error al realizar git pull en el repositorio {repo_name} con clone_url {clone_url} y servidor web {servidor_web}"
                    }
                ), 500
        else:
            return jsonify(
                {
                    "message": "No se encontró información sobre el repositorio en la carga útil (payload)"
                }
            ), 400
    else:
        return jsonify({"message": "La solicitud no contiene datos JSON"}), 400


if __name__ == "__main__":
    app.run()
