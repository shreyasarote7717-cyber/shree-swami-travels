from fastapi import FastAPI, Request, Form, Depends
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from datetime import datetime
from twilio.rest import Client
import database  # Ensure database.py is in the same folder

app = FastAPI()
templates = Jinja2Templates(directory="templates")

# 1. DATABASE INITIALIZATION
database.Base.metadata.create_all(bind=database.engine)

# 2. TWILIO CONFIGURATION
# Best practice: Move these to Render Environment Variables later
TWILIO_SID = "ACfb17ee0a7d097aa91e5242c2783091fb"
TWILIO_TOKEN = "105fc4edefa41f215fd6114b74f642ad"
TWILIO_NUMBER = "whatsapp:+14155238886"

# This list matches your staff numbers
STAFF_NUMBERS = ["whatsapp:+918320286948", "whatsapp:+916353963704"]

client = Client(TWILIO_SID, TWILIO_TOKEN)

# --- ROUTES ---

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/book")
async def create_booking(
    request: Request,
    customer_name: str = Form(...),
    customer_phone: str = Form(...),
    pickup: str = Form(...),
    destination: str = Form(...),
    db: Session = Depends(database.get_db)
):
    # A. Save to Database
    new_booking = database.Booking(
        name=customer_name, 
        phone=customer_phone, 
        pickup=pickup, 
        destination=destination,
        timestamp=datetime.now()
    )
    db.add(new_booking)
    db.commit()

    # B. Send WhatsApp to all staff
    message_body = (
        f"New Booking Alert! 🚕\n"
        f"Name: {customer_name}\n"
        f"From: {pickup}\n"
        f"To: {destination}\n"
        f"Phone: {customer_phone}"
    )
    
    for staff_phone in STAFF_NUMBERS:
        try:
            client.messages.create(
                from_=TWILIO_NUMBER,
                to=staff_phone,
                body=message_body
            )
        except Exception as e:
            print(f"⚠️ WhatsApp Error for {staff_phone}: {e}")

    # C. Redirect to thank you page
    return RedirectResponse(url="/thankyou", status_code=303)

@app.get("/thankyou", response_class=HTMLResponse)
async def thankyou(request: Request):
    return templates.TemplateResponse("thankyou.html", {"request": request})
