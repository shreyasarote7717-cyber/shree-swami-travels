from fastapi import FastAPI, Request, Form, Depends
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from datetime import datetime
from twilio.rest import Client
import database  # This refers to your database.py file

app = FastAPI()
templates = Jinja2Templates(directory="templates")

# 1. DATABASE INITIALIZATION
# This line creates the tables automatically if they don't exist
database.Base.metadata.create_all(bind=database.engine)

# 2. TWILIO CONFIGURATION
TWILIO_SID = "ACfb17ee0a7d097aa91e5242c2783091fb"
TWILIO_TOKEN = "105fc4edefa41f215fd6114b74f642ad"
TWILIO_NUMBER = "whatsapp:+14155238886"
# Your staff numbers
STAFF_NUMBERS = ["whatsapp:+918320286948", "whatsapp:+916353963704"]

# Use the EXACT name from your Render Environment tab here
raw_numbers = os.environ.get('THE_NAME_FROM_RENDER', '') 

# This splits your comma-separated numbers into a list
staff_list = [num.strip() for num in raw_numbers.split(',') if num.strip()]

client = Client(TWILIO_SID, TWILIO_TOKEN)

# --- ROUTES ---

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
   return templates.TemplateResponse(
    request=request, 
    name="index.html", 
    context={"request": request}
)

@app.post("/book")
async def create_booking(
    customer_name: str = Form(...),
    customer_number: str = Form(...),
    start_location: str = Form(...),
    destination: str = Form(...),
    time: str = Form(...),
    car_type: str = Form(...),
    db: Session = Depends(database.get_db)
):
    # Create the booking object
    new_booking = database.Booking(
        customer_name=customer_name,
        customer_number=customer_number,
        start_location=start_location,
        destination=destination,
        time=time,
        car_type=car_type,
        status="Pending"
    )
    
    # Save to Database
    db.add(new_booking)
    db.commit()
    db.refresh(new_booking)

    # 3. WHATSAPP ALERT (With Safety Catch)
    message_text = (
        f"🚕 *New Trip - Shree Swami Travels*\n\n"
        f"👤 *Customer:* {customer_name}\n"
        f"📞 *Phone:* {customer_number}\n"
        f"📍 *From:* {start_location}\n"
        f"🏁 *To:* {destination}\n"
        f"⏰ *Time:* {time}\n"
        f"🚗 *Car:* {car_type}\n\n"
        f"Check Admin Panel to confirm."
    )

    try:
        for staff in STAFF_NUMBERS:
            client.messages.create(
                from_=TWILIO_NUMBER,
                body=message_text,
                to=staff
            )
    except Exception as e:
        print(f"⚠️ WhatsApp Error: {e}")
        # We don't crash the app here so the user still sees the success page

    return RedirectResponse(url="/thankyou", status_code=303)

@app.get("/thankyou", response_class=HTMLResponse)
async def thank_you(request: Request):
    return templates.TemplateResponse(request=request, name="thankyou.html", context={"request": request})

@app.get("/admin", response_class=HTMLResponse)
async def admin_panel(request: Request, db: Session = Depends(database.get_db)):
    # Get all bookings from the database, newest at the top
    bookings = db.query(database.Booking).order_by(database.Booking.id.desc()).all()
    
    return templates.TemplateResponse(
        request=request, 
        name="admin.html", 
        context={"request": request, "bookings": bookings}
    )

@app.post("/admin/confirm/{booking_id}")
async def confirm_booking(booking_id: int, db: Session = Depends(database.get_db)):
    # Find the specific booking by its ID
    booking = db.query(database.Booking).filter(database.Booking.id == booking_id).first()
    
    if booking:
        booking.status = "Confirmed" # Change the status
        db.commit()
    
    # Send you back to the admin page to see the update
    return RedirectResponse(url="/admin", status_code=303)


@app.post("/admin/confirm/{booking_id}")
async def confirm_booking(booking_id: int, db: Session = Depends(database.get_db)):
    # 1. Search for the specific booking by its ID
    booking = db.query(database.Booking).filter(database.Booking.id == booking_id).first()
    
    if not booking:
        return {"error": "Booking not found"}

    # 2. Update the status in the database
    booking.status = "Confirmed"
    db.commit()
    
    # 3. Redirect back to the admin page so you see the "Verified" status
    return RedirectResponse(url="/admin", status_code=303)



@app.post("/book")
async def create_booking(
    customer_name: str = Form(...),
    customer_number: str = Form(...),
    # ... other fields ...
    db: Session = Depends(database.get_db)
):
    # [DATABASE CODE HERE - Keep as is]

    # 1. Message to STAFF (You)
    staff_text = f"🚕 *New Trip Request*\n👤 {customer_name}\n📍 {start_location} to {destination}"

    # 2. Message to CUSTOMER (The traveler)
    customer_text = (
        f"Hello {customer_name}! 🙏\n"
        f"Your booking for a {car_type} to {destination} has been received by *Shree Swami Travels*.\n"
        f"We will confirm your ride shortly! ✅"
    )

    try:
        # Alert Staff
        for staff in STAFF_NUMBERS:
            client.messages.create(from_=TWILIO_NUMBER, body=staff_text, to=staff)
        
        # ALERT CUSTOMER (Add this line!)
        # Ensure customer_number is formatted as 'whatsapp:+91...'
        formatted_cust_number = f"whatsapp:{customer_number}" if "whatsapp:" not in customer_number else customer_number
        
        client.messages.create(
            from_=TWILIO_NUMBER, 
            body=customer_text, 
            to=formatted_cust_number
        )

    except Exception as e:
        print(f"⚠️ WhatsApp Error: {e}")

    return RedirectResponse(url="/thankyou", status_code=303)
