import requests as requestsLib
from flask import Flask, request, jsonify
from flask_cors import CORS, cross_origin
import uuid
import scraper_handler
import threading
from pandas import DataFrame
# from prescriber_code import *
from io import StringIO

# import ..database_functions.database as db_func
import database as db_func
from code_pdf_server import *

app = Flask(__name__)
cors = CORS(app)
PORT = 5000
# app.config["CORS_HEADERS"] = "Content-Type"
app.config["DEBUG"] = True  # Restart on changes
app.config["PORT"] = PORT
processing = {}
# https://stackoverflow.com/questions/10434599/get-the-data-received-in-a-flask-request


def generate_id():
    return str(uuid.uuid4())


@app.route("/api/upload", methods=["POST"])
@cross_origin()
def verify():
    print(request.data)
    print(request.files)
    print(request.form)
    print(request.headers)
    file_data = request.files
    if not file_data:
        return {"message": "No file uploaded"}, 400, {"Content-Type": "application/json"}

    file_data = file_data["file"]

    id = generate_id()
    processing[id] = {'file': file_data, 'status': 'pending', 'result': None}

    thread = threading.Thread(
        target=scraper_handler.handle, args=(file_data.read(), id))
    thread.start()

    return {"id": id}, 200, {"Content-Type": "application/json"}


@app.route("/api/status/<id>", methods=["GET"])
@cross_origin()
def status(id):
    if id not in processing:
        return {"message": "No such request"}, 400, {"Content-Type": "application/json"}

    status = scraper_handler.check_status(id)

    # Temporary quick-fix for updating state to completed
    if type(status) is DataFrame:
        processing[id]['status'] = "completed"
        processing[id]['result'] = status
        status = "completed"

    return {"status": status}, 200, {"Content-Type": "application/json"}


@app.route("/api/download/<id>", methods=["GET"])
@cross_origin()
def download(id):
    if id not in processing:
        return {"message": "No such request"}, 400, {"Content-Type": "application/json"}
    if processing[id]['status'] != "completed":
        return {"message": "Request not completed yet"}, 400, {"Content-Type": "application/json"}
    result_data = processing[id]['result']
    del processing[id]
    return result_data.to_json(index=False, orient="records"), 200, {"Content-Type": "text/csv"}

@app.route("/api/cancel/<id>", methods=["POST"])
@cross_origin()
def cancel(id):
    if id not in processing:
        return {"message": "No such request"}, 400, {"Content-Type": "application/json"}
    if processing[id]['status'] == "completed":
        return {"message": "Request already completed"}, 400, {"Content-Type": "application/json"}
    try:
        # Close it in the scraper_handler
        scraper_handler.close_request(id)

        del processing[id]
        return {"message": "Request cancelled"}, 200, {"Content-Type": "application/json"}
    except Exception as e:
        print(e)
        return {"message": "Error cancelling request"}, 400, {"Content-Type": "application/json"}
    
@app.route("/health")
@cross_origin()
def health_check(): # ? API Gateway health check
    return {"message": "OK"}, 200, {"Content-Type": "application/json"}

#############################################
# Prescriptions

# @app.route("/api/getPrescriptions/<username>", methods=["GET"])
# @cross_origin()
# def getPrescriptions(username):
#   prescriptions = database.getAllPrescriptions(username)
#   return prescriptions

##############################################

@app.route('/generatePdf', methods=['POST'])
def generate_pdf():
    code = request.json.get('code')
    output_path = request.json.get('output_path')

    if not code or not output_path:
        return jsonify({'error': 'Invalid code or output path'}), 400

    page = create_pdf(code, output_path)
    # Get page buffer
    pdf = page.getpdfdata()

    return pdf, 200, {"Content-Type": "application/pdf"}


# API endpoint to export the csv file with the new data
@app.route('/export/<id>', methods=['GET'])
def export_file(id):
    file_type = request.args.get('file_type', 'csv')
    if file_type not in ['csv', 'xlsx']:
        return {"message": "Invalid file type. Please specify 'csv' or 'xlsx'."}, 400, {"Content-Type": "application/json"}
    
    status = scraper_handler.check_status(id)
    if type(status) is not DataFrame:
        return {"message": "Invalid data or columns"}, 400, {"Content-Type": "application/json"}
    
    # Set content_type to a default value
    buffer = StringIO()
    if file_type == 'csv':
        new_data_to_csv(buffer, status)
        content_type = "text/csv"
    else:
        new_data_to_csv(buffer, status)
        content_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    
    buffer.seek(0)
    result = status.to_dict(orient='records') 
    db_func.insert_data(collection, result)
    
    return {"json": status.to_json(orient='records'), "file": buffer.read()}, 200, {"Content-Type": content_type}

            
# # API endpoint to generate prescriber codes
# @app.route('/generate/code/export', methods=['POST'])
# def generate_prescriber_codes():    
#     # data = request.json.get('data')
#     # columns = request.json.get('columns')
#     file_data = request.files
#     if not file_data:
#         return {"message": "No file uploaded"}, 400, {"Content-Type": "application/json"}

#     file_data = file_data["file"]
    
#     # if not data or not columns:
#     #     return jsonify({'error': 'Invalid data or columns'}), 400
    
#     df = dataframe_from_csv(file_data)
#     # df = create_dataframe_from_list(data, columns)
#     df = add_codes_to_df(df, collection())
#     # generate_verified_pdfs(df)
#     buffer = StringIO()
    
#     modify_csv_with_new_data(buffer, df)
#     buffer.seek(0)
    
#     result = df.to_dict(orient='records') 
#     db_func.insert_data(collection, result)
    
#     return {"json": df.to_json(orient='records'), "csv": buffer.read()}, 200, {"Content-Type": "application/json"}


def register_service(service_name, service_url):
    print(f"Sending register request | {service_name} at {service_url}")
    return requestsLib.post("http://localhost:3130/service-registry/register", json={"serviceName": service_name, "serviceUrl": service_url})



print("Starting Verification Service on port", app.config["PORT"])
register_service("verification-service", f"http://127.0.0.1:{app.config['PORT']}")


if __name__ == "__main__":
    app.run(port=PORT, debug=True)
