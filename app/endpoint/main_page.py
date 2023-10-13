from fastapi import APIRouter, Request, status, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.responses import JSONResponse, Response
from decouple import config

from api.mailing import send_mail_notif
from api.model.MailContainer import MailContainerBody
from database.api_db import API_DB, Recipients

main_page = APIRouter()
templates = Jinja2Templates("templates/")
db_conn = API_DB()
get_recipient = Recipients()

@main_page.get("/")
async def main_homepage(request: Request):
    # call items list from database 
    document_type = ["New Model Authorization", "New Model Information", "Part Evaluation", "ECN", "Technical report", "Study Report", "Mechanical Part Inspection Report", 
                     "Drop Test Report", "Vibration Test Report", "Part Injection Approval", "General Inspection Report", "TV Check Sheets", "Home Theater Check Sheet", 
                     "MM Part List", "MM Assembly 1", "MM Assembly 2", "MM Alignment/Adjustment", "Trial Run Evaluation", "New Model Trial Review", "FDRM", 
                     "Mopdification Information", "Approval Spec", "Approval Letter", "Other"]
    send_to =  ["Production Engineer", "Production", "QC Line", "PQA", "Procurement", "Service", "QRCC",
                              "Marketing", "Accounting", "Costing", "Promotion", "PPC", "CMC", "Production Planning", "TV Director"]
    context = {"request": request, "document_type": document_type, "destination": send_to,
               "sharp_relay_server": f"{config('SMTP_SERVER_1')}", "office_relay_server": f"{config('SMTP_SERVER_2')}"}


    return templates.TemplateResponse("main.html", context=context)

@main_page.post("/app/api/function/mailing/broadcast")
async def broadcast_mail(MailContainer: MailContainerBody):

    sendtest = send_mail_notif(payload=MailContainer, sender_email=config("SMTP_SENDER"), sender_pw=config("SMTP_SENDER_PW"), server_name=MailContainer.server_name)
    return JSONResponse(content=sendtest)

@main_page.get("/app/api/function/data")
async def get_listing_data():
    try:
        registered_documents = await db_conn.get_listing_record()
        if registered_documents:
            return JSONResponse({
                "registered_data": registered_documents,
                "message": "Data Obtained"
            }, status_code=status.HTTP_200_OK)
        else:
            return JSONResponse({
                "registered_data": registered_documents,
                "message": "No data can be found"
            })
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")

@main_page.get("/app/api/function/data/documents")
async def get_documentNumber(document_number: str):
    container = await db_conn.get_documents_detail(document_number=document_number)
    distribute_to = container.get("distributed_to")
    list_recipients_division = distribute_to.split(";")
    
    data_content = {"content_data": container, "response_server": ""}
    if container:
        # get list of recipients based on division from database 
        get_recipients_by_category = await get_recipient.get_recipients_category(filted=list_recipients_division)
        recipients_lists = [x.recipient_mail for x in get_recipients_by_category]
        
        data_content.update({"response_server": "Data obtained", "recipients": recipients_lists, "status_code": status.HTTP_200_OK})
        return JSONResponse(content=data_content, status_code=status.HTTP_200_OK)
    else:
        data_content.update({"response_server": "Not Found", "status_code": status.HTTP_404_NOT_FOUND})
        return JSONResponse(content=data_content, status_code=status.HTTP_404_NOT_FOUND)