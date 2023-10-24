from fastapi import APIRouter, Request, Depends, UploadFile, File, Form, status
from fastapi.templating import Jinja2Templates
from fastapi.responses import JSONResponse
from decouple import config
from typing import List
import mimetypes

from api.mailing import send_mail_notif
from database.api_db import API_DB


upload_endpoint = APIRouter()
templates = Jinja2Templates("templates/")
db_conn = API_DB()

@upload_endpoint.get("/")
async def uploadEndpoint(request: Request):
    document_type = ["New Model Authorization", "New Model Information", "Part Evaluation", "ECN", "Technical report", "Study Report", "Mechanical Part Inspection Report", 
                     "Drop Test Report", "Vibration Test Report", "Part Injection Approval", "General Inspection Report", "TV Check Sheets", "Home Theater Check Sheet", 
                     "MM Part List", "MM Assembly 1", "MM Assembly 2", "MM Alignment/Adjustment", "Trial Run Evaluation", "New Model Trial Review", "FDRM", 
                     "Mopdification Information", "Approval Spec", "Approval Letter", "Other"]
    send_to =  ["Production Engineer", "Production", "QC Line", "PQA", "Procurement", "Service", "QRCC",
                              "Marketing", "Accounting", "Costing", "Promotion", "PPC", "CMC", "Production Planning", "TV Director"]
    context = {"request": request, "document_type": document_type, "destination": send_to}
    return templates.TemplateResponse("upload_document.html", context=context)

@upload_endpoint.post("/upload_report")
async def uploadReportData(documentNo: str = Form(...), documentType: str = Form(...),
                           subjectDocument: str = Form(...), documentDesc: str = Form(...),
                           m_tv_broad: str = Form(...), distributed_to: List[str] = Form(...),
                           filenameUpload: UploadFile = File(...)):

    # check user login
    # if login, grab the necessary information like outlook email and it's password
    # else
    # return some kind of data that user isn't logged in
    file_content = await filenameUpload.read()

    # Detect the file format using magic library
    mime, _ = mimetypes.guess_type(filenameUpload.filename)
    if mime and mime.startswith("text"):
        try:
            # Attempt to decode as UTF-8
            ffUpload = file_content.decode("utf-8")
        except UnicodeDecodeError:
            # If decoding fails, it's not a text file; handle it as binary
            ffUpload = file_content
    else:
        # It's not a text file; handle binary content or other formats
        ffUpload = file_content  # Store binary content as-is or process it as needed

    combined_distribute = ";".join(distributed_to)
    queryPayload = {"document_no": documentNo, "document_type": documentType, "document_subject": subjectDocument, "document_description": documentDesc,
                    "m_tv_name": m_tv_broad, "filename_upload": ffUpload, "distribute_to": combined_distribute,
                    "filename": filenameUpload.filename}
    write_data = await db_conn.write_documentdb(**queryPayload)
    if write_data:
        return JSONResponse(content={'message': 'form data procees successfully'})
    else:
        return JSONResponse(content={"message": "Failed to upload detailed documents"}, status_code=status.HTTP_406_NOT_ACCEPTABLE)