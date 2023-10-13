from fastapi import APIRouter, Request, HTTPException, Query, BackgroundTasks
from fastapi.templating import Jinja2Templates
from fastapi.responses import FileResponse, Response, StreamingResponse
from tempfile import NamedTemporaryFile

import io, tempfile, mimetypes
import urllib.parse

from database.api_db import API_DB

document_list_ep = APIRouter()
templates = Jinja2Templates("templates/")
db_conn = API_DB()

@document_list_ep.get("/")
async def home_documents(request: Request, page: int = Query(1, alias='page'), limit: int = Query(25, alias='perpage')):
    contexts = {"request": request, "page": page, "title": "Track Record Documents", "limit": limit}
    offset = (page - 1) * limit
    serve_data = await db_conn.read_documentdb(limit=limit, offset=offset)
    # calculate the total number of records and pages
    total_records = db_conn.count_record_registered_documents()
    total_pages = (total_records + limit -1) // limit ## calculate total pages
    contexts.update({"total_pages": total_pages, "recorded_documents": serve_data})
    return templates.TemplateResponse("documents.html", context=contexts)

@document_list_ep.get("/serverfile/dynamic/api/{document_no}")
async def open_file_in_browser(document_no: str, background_task: BackgroundTasks):
    document = await db_conn.serve_document_blob(document_no=document_no)
    
    if document:
        # Get the BLOB content
        file_data = document.filename_upload
        fileBuffer = io.BytesIO(file_data)
        background_task.add_task(fileBuffer.close)
        return Response(fileBuffer.getvalue(), headers={"Content-Disposition": f'inline; filename="{document_no}.pdf'},
                            media_type="application/pdf")
    
    raise HTTPException(status_code=404, detail="File not found")