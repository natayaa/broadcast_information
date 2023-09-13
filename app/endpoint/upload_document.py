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
    context = {"request": request, "document_type": document_type}
    return templates.TemplateResponse("upload_document.html", context=context)