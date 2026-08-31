# app.py

from fastapi import FastAPI, HTTPException
from engine import ExtractionFailedException, get_data
from schemas import Ticket, TicketRequestModel
from fastapi.middleware.cors import CORSMiddleware
import os

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=[os.getenv("FRONTEND_ORIGIN", "http://localhost:3000")],
    allow_methods=["POST"],
    allow_headers=["*"],
)

@app.post("/extract", response_model=Ticket)
def extract(input_ticket: TicketRequestModel):
    try:
        output = get_data(input_ticket)
        return output

    except ExtractionFailedException as e:
        print(str(e))
        raise HTTPException(status_code=500, detail="Internal Server Error. Extraction Failed")