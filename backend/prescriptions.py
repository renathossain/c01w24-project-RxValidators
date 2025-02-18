from flask import Flask, request, jsonify
from flask_cors import CORS, cross_origin
import uuid

import database_functions.database as dbfunc

app = Flask(__name__)
cors = CORS(app)
app.config["CORS_HEADERS"] = "Content-Type"
app.config["DEBUG"] = True
PORT = 5000

requests = {}
# https://stackoverflow.com/questions/10434599/get-the-data-received-in-a-flask-request


def generate_id():
    return str(uuid.uuid4())


@app.route("/api/getPrescriptions/<username>", methods=["POST"])
@cross_origin()
def getPrescriptions(username):
    prescriptions = dbfunc.getAllPrescriptions(username)
    print("sending...")
    print(prescriptions)
    return prescriptions


if __name__ == "__main__":
    app.run(port=PORT, debug=True)
