from fastapi import APIRouter, Request, Depends, UploadFile, File
from fastapi.templating import Jinja2Templates
from fastapi.responses import JSONResponse

from database.schemas import uploadReportBroadcast

upload_endpoint = APIRouter()
templates = Jinja2Templates("templates/")

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
async def uploadReportData(payload: uploadReportBroadcast.BroadcastReport = Depends(), file: UploadFile = File(...)):
    print(payload)
    # check user login
    # if login, grab the necessary information like outlook email and it's password
    # else
    # return some kind of data that user isn't logged in
    if file:
        with open(file.filename, "wb") as f:
            f.write(file.file.read())
    return JSONResponse(content={'message': 'form data procees successfully'})

## Broadcast function
