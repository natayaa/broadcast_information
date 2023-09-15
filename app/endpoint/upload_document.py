from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates

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