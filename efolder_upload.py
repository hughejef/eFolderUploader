from api_key import get_api_key
import requests
import json
import os
import sys
from flask import Flask, request, jsonify
from waitress import serve


app = Flask(__name__)

@app.route('/upload-file', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({"status": "error", "message": "No file part"}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({"status": "error", "message": "No selected file"}), 400
    file.save(f"/home/ec2-user/uploaded_files/{file.filename}")
    return jsonify({"status": "success", "message": "File uploaded successfully"}), 200




def upload_file_to_encompass(access_token, loan_guid, placeholder_name, path_to_file):
    """
    Takes an access token, loan number, placeholder, and filepath as parameter and uploads
    file found at filepath to the provided loan number in Encompass under the passed placeholder.
    If placeholder exists it adds to placeholder, otherwise new placeholder is created.
    """

    # Check if filename is in an acceptable format. (.doc, .docx, .emf, .html, .jpeg, .jpg, .pdf, .tif, .txt, and .xps)
    comp_check = check_file_compatibility(path_to_file)
    if comp_check:
            document_id = check_for_doc(access_token, loan_guid, placeholder_name)
            upload_attachment(access_token, loan_guid, document_id, path_to_file, placeholder_name)
  


def upload_attachment(access_token, loan_guid, document_id, path_to_file, placeholder_name):
    """
    Uploads attachment to loan at designated placeholder.
    """
    url = f"https://api.elliemae.com/encompass/v3/loans/{loan_guid}/attachmentUploadUrl"
    file_size = os.path.getsize(path_to_file)

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    payload = {
        "assignTo": {
            "entityId": document_id,
            "entityType": "Document"
        },
        "file": {
            "contentType": "application/pdf",
            "name": os.path.basename(path_to_file),
            "size": file_size
        },
        "title": placeholder_name
    }

    response = requests.post(url, headers=headers, json=payload)
    response_data = response.json()
    print(response_data)
    authorization_header = response_data["authorizationHeader"]
    upload_url = response_data["uploadUrl"]

    # Single file upload
    headers = {
        "Authorization": authorization_header,
        "Content-Type": "application/pdf"  # Adjust based on your file type
    }

    with open(path_to_file, "rb") as file:
        response = requests.put(upload_url, headers=headers, data=file)

    if response.status_code == 200:
        print("Attachment uploaded successfully.")
        
    else:
        print(f"Failed to upload attachment. Status Code: {response.status_code}")
        print("Response Text:", response.text)

def check_file_compatibility(file_name):
    """
    Takes a filename as a parameter and checks if the last 4 characters of the filename
    contain a valid extension acceptable by Encompass. Returns True if Valid, else returns False
    """
    acceptable_exts = [".doc", "docx", ".emf", "html", "jpeg", ".jpg", ".pdf", ".tif", ".txt", ".xps"]
    file_ext = file_name[-4:]
    if file_ext in acceptable_exts:
        return True
    
    else:
        print('File is in unnacceptable format.\n Acceptable formats are: ".doc", ".docx", ".emf", ".html", ".jpeg", ".jpg", ".pdf", ".tif", ".txt", ".xps"')
        return False



    # check loan for placeholder in doc names
def check_for_doc(access_token, loan_guid, placeholder_name):
    """
    checks if a document placeholder exists for given loan number. If it does not exist,
    placeholder is created.
    """

    doc_list = get_doc_list(access_token, loan_guid)
    doc_id = None
    # if placeholder does not exist, create it
    for item in doc_list:

        if placeholder_name in item["doc_title"]:
            doc_id = item["doc_id"]
            break
    if doc_id == None:
        doc_id = create_placeholder(access_token, loan_guid, placeholder_name)
        
    return(doc_id)

def create_placeholder(access_token, loan_guid, placeholder_name):
    """
    Creates a new document placeholder in specified loan
    """
    url = f"https://api.elliemae.com/encompass/v1/loans/{loan_guid}/documents"

    payload = {
        "applicationId": "All",
        "title": placeholder_name
    }
    headers = {
        "accept": "application/json",
        "Authorization": f"Bearer {access_token}",
        "content-type": "application/json"
    }

    response = requests.post(url, json=payload, headers=headers)

    if response.status_code == 201:  
        # Retrieve the document ID from the headers
        document_id = response.headers.get("Location")
        if document_id:
            print(f"Document created successfully. Document ID: {document_id}")
            document_id = document_id[-36:]
            return document_id
        else:
            print("Document created, but document ID not found in headers.")
            return None
    else:
        print(f"Failed to create document. Status Code: {response.status_code}")
        print("Response:", response.text)
        return None


def get_doc_list(access_token, loan_guid):
    """
    Takes access token and loan number as a paramter and returns a list of document titles
    representing document placeholders active in the spcified loan
    """
    url = f"https://api.elliemae.com/encompass/v3/loans/{loan_guid}/documents?requireActiveAttachments=false&includeRemoved=false"

    headers = {
        "accept": "application/json",
        "Authorization": f"Bearer {access_token}"
    }

    response = requests.get(url, headers=headers)

    response = response.json()
    doc_list = []

    for piece in response:
        doc_dict = {}
        doc_dict["doc_title"] = piece["title"]
        doc_dict["doc_id"] = piece["id"]
        doc_list.append(doc_dict)
    return doc_list
    

def get_guid(access_token, loan_number):
    """
    Takes a LoanNumber as a parameter and returns the Encompass GUID.
    """
    url = "https://api.elliemae.com/encompass/v1/loanPipeline?limit=1"

    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "Authorization": f"Bearer {access_token}"
    }

    body = {
        "includeArchivedLoans": True,
        "filter": {
            "canonicalName": "Loan.LoanNumber",
            "value": loan_number,
            "matchType": "Exact"
        }
    }

    response = requests.post(url, headers=headers, json=body)
    response_data = response.json()

    if not response_data:
        raise ValueError(f"No loans found for loan number: {loan_number}")

    try:
        return response_data[0]["loanGuid"]
    except IndexError:
        raise ValueError(f"Loan number {loan_number} not found in the pipeline.")

def main():
    app.run(host="0.0.0.0", port=5000, debug=True)


if __name__ == "__main__":
    serve(app, host="0.0.0.0", port=5000)