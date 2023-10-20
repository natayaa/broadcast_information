from fastapi import APIRouter, Request, status, HTTPException, Form
from fastapi.templating import Jinja2Templates
from fastapi.responses import JSONResponse, Response
from decouple import config
import socket

from api.mailing import send_mail_notif
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
    context = {"request": request, "document_type": document_type, "destination": send_to, "title": "TV Engineers App",
               "sharp_relay_server": f"{config('SMTP_SERVER_1')}", "office_relay_server": f"{config('SMTP_SERVER_2')}"}


    return templates.TemplateResponse("main.html", context=context)



@main_page.post("/app/api/function/mailing/broadcast")
async def broadcast_mail(request: Request, document_number: str, server_name: str = Form(...)):
    # get document based on document_number
    
    container = {} 
    document_data = await db_conn.get_detail_record_document(document_number)
    # get recipient list 
    uploaded_filename_hyperlink = f"http://{socket.gethostbyname(socket.gethostname())}:{request.client.port}/serverfile/dynamic/api/{document_number}"
    if document_data:
        departement_list = document_data.get("broadcast_to")
        # get list of all recipient of Direct mail and CC (Carbon Copy)
        direct_recipients_list = ";".join(await get_recipient.get_recipients_category_and_recipient_type(departement_list, "Direct"))
        cc_recipients_list = ";".join(await get_recipient.get_recipients_category_and_recipient_type(departement_list, "CC"))
        container.update({"direct_mail": direct_recipients_list, "carbon_copy_mail": cc_recipients_list,
                          "mail_subject": document_data.get("document_subject"),
                          "document_content": document_data.get("document_description") + f" You can find the file in this link : {uploaded_filename_hyperlink}"})
        
    # tinggal anggeuskeun engke ?
    for item, l in container.items():
        print(l)
    return "OK"

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
    
    data_content = {"content_data": container, "response_server": "", "recipients": None}
    if container:
        
        
        data_content.update({"response_server": "Data obtained", "status_code": status.HTTP_200_OK})
        return JSONResponse(content=data_content, status_code=status.HTTP_200_OK)
    else:
        data_content.update({"response_server": "Not Found", "status_code": status.HTTP_404_NOT_FOUND})
        return JSONResponse(content=data_content, status_code=status.HTTP_404_NOT_FOUND)