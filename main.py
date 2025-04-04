import requests
import os
from flask import Flask, request, jsonify

app = Flask(__name__)

# إعداد Orthanc
ORTHANC_URL = "http://localhost:8042"
OHIF_VIEWER_URL = "http://localhost/viewer"

def upload_dicom(dicom_url):
    """ تحميل ورفع DICOM إلى Orthanc وإرجاع StudyInstanceUID """
    try:
        # تحميل الملف
        response = requests.get(dicom_url)
        if response.status_code != 200:
            return None, f"Error downloading file: {response.status_code}"

        # رفع إلى Orthanc
        headers = {"Content-Type": "application/dicom"}
        upload_response = requests.post(f"{ORTHANC_URL}/instances", data=response.content, headers=headers)

        if upload_response.status_code != 200:
            return None, f"Error uploading to Orthanc: {upload_response.text}"

        # استخراج StudyInstanceUID
        instance_id = upload_response.json().get("ID")
        study_response = requests.get(f"{ORTHANC_URL}/instances/{instance_id}/study")

        if study_response.status_code != 200:
            return None, f"Error fetching StudyInstanceUID: {study_response.text}"

        study_instance_uid = study_response.json().get("MainDicomTags", {}).get("StudyInstanceUID")
        return study_instance_uid, None

    except Exception as e:
        return None, str(e)

@app.route("/upload-dicom", methods=["POST"])
def handle_upload():
    """ API لاستقبال رابط DICOM وإرجاع رابط العرض """
    data = request.json
    dicom_url = data.get("dicom_url")

    if not dicom_url:
        return jsonify({"error": "Missing dicom_url"}), 400

    study_instance_uid, error = upload_dicom(dicom_url)
    if error:
        return jsonify({"error": error}), 500

    viewer_url = f"{OHIF_VIEWER_URL}?StudyInstanceUIDs={study_instance_uid}"
    return jsonify({"viewer_url": viewer_url})

if __name__ == "__main__":
    app.run(debug=True, port=5000)
