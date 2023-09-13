from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates

recipient = APIRouter()
templates = Jinja2Templates("templates/")

@recipient.get("/")
async def page_recipient(request: Request):
    recipient_distribution = ["Production Engineer", "Production", "QC Line", "PQA", "Procurement", "Service", "QRCC",
                              "Marketing", "Accounting", "Costing", "Promotion", "PPC", "CMC", "Production Planning", "TV Director"]
    
    retval = {"request": request, "recipient_list": recipient_distribution}
    return templates.TemplateResponse("register_recipient.html", context=retval)