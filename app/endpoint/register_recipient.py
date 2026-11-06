from fastapi import APIRouter, Request, Query
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from database.api_db import Recipients

recipient = APIRouter()
templates = Jinja2Templates("templates/")
recipient_regist = Recipients()

@recipient.get("/", response_class=HTMLResponse)
@recipient.post("/")
async def page_recipient(request: Request, page: int = Query(1, alias='page'), limit: int = Query(10, alias='perpage')):
    recipient_distribution = ["Production Engineer", "Production", "QC Line", "PQA", "Procurement", "Service", "QRCC",
                              "Marketing", "Accounting", "Costing", "Promotion", "PPC", "CMC", "Production Planning", "TV Director"]
    retval = {"request": request, "recipient_list": recipient_distribution}
    # set for pagination 
    offset = (page - 1) * limit
    # count total data from database 
    ttl_records = recipient_regist.count_recipients()
    total_pages = (ttl_records + limit - 1) // limit     # calculate total page
    registered_recipients = await recipient_regist.get_recipient_list(offset=offset, limit=limit)
    if registered_recipients:
        retval.update({ "registered_recipients": registered_recipients, "page": page, "title": "Register Recipient & Registered Recipients",
                   "limit": limit, "total_pages": total_pages})
    else:
        retval.update({"registered_recipients": ["No Content"], "page": page, "title": "Register Recipient & Registered Recipients",
                   "limit": limit, "total_pages": total_pages})
    
    if request.method == "POST":
        recipientForm = await request.form()
        container_register = {"recipient_mail": recipientForm.get("recipientMail"),
                              "recipient_name": recipientForm.get("recipientName"),
                              "recipient_division": recipientForm.get("rDivision"), 
                              "recipient_category": recipientForm.get("recipient_category")}
        reg_recipient = await recipient_regist.register_recipient(**container_register)
        if reg_recipient:
            retval.update({"message": f"Successfully register {recipientForm.get('recipientName')} to {recipientForm.get('rDivision')}" })
        else:
            retval.update({"message": "Failed to register"})
    return templates.TemplateResponse("register_recipient.html", context=retval)