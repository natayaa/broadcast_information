from fastapi import APIRouter, Request, HTTPException, Query, BackgroundTasks, Depends
from fastapi import status
from fastapi.templating import Jinja2Templates
from fastapi.responses import Response, JSONResponse
from typing_extensions import Annotated
from tempfile import NamedTemporaryFile
import io

from database.api_db import API_DB
from database.auth_db import oauth2_scheme

document_list_ep = APIRouter()
templates = Jinja2Templates("templates/")
db_conn = API_DB()

@document_list_ep.get("/")
async def home_documents(request: Request, security_token: Annotated[str, Depends(oauth2_scheme)], page: int = Query(1, alias='page'), limit: int = Query(25, alias='perpage')):
    contexts = {"request": request, "page": page, "title": "Track Record Documents", "limit": limit}
    offset = (page - 1) * limit
    serve_data = await db_conn.read_documentdb(limit=limit, offset=offset)
    # calculate the total number of records and pages
    total_records = db_conn.count_record_registered_documents()
    total_pages = (total_records + limit -1) // limit ## calculate total pages
    contexts.update({"total_pages": total_pages, "recorded_documents": serve_data})
    return templates.TemplateResponse("documents.html", context=contexts)

## remove selected data
@document_list_ep.delete("/api/data/document/registered/document_no={document_id}")
async def delete_selected_record(document_id: int, security_token: Annotated[str, Depends(oauth2_scheme)]):
    endpoint_retval = {"message": "", "docname": ""}
    delete_data = await db_conn.delete_recorded_document(document_id=document_id)
    if delete_data:
        endpoint_retval.update({"message": "Selected data has been removed from database"})
        return JSONResponse(content=endpoint_retval, status_code=status.HTTP_200_OK)
    else:
        endpoint_retval.update({"message": "Failed to delete selected data", "err_msg": delete_data})
        return JSONResponse(content=endpoint_retval, status_code=status.HTTP_417_EXPECTATION_FAILED)


@document_list_ep.get("/serverfile/dynamic/api/{document_no}")
async def open_file_in_browser(document_no: str, background_task: BackgroundTasks, security_token: Annotated[str, Depends(oauth2_scheme)]):
    document = await db_conn.serve_document_blob(document_no=document_no)
    
    if document:
        # Get the BLOB content
        file_data = document.filename_upload
        fileBuffer = io.BytesIO(file_data)
        background_task.add_task(fileBuffer.close)
        return Response(fileBuffer.getvalue(), headers={"Content-Disposition": f'inline; filename="{document_no}'},
                            media_type="application/pdf")
    
    raise HTTPException(status_code=404, detail="File not found")

