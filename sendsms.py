from fastapi import Request
from twilio.rest import Client
from dotenv import load_dotenv, find_dotenv
import os
import sqlite3

load_dotenv('.env', override=True)
# Initialize Twilio client
TWILIO_ACCOUNT_SID = os.environ["TWILIO_ACCOUNT_SID"]
TWILIO_AUTH_TOKEN = os.environ["TWILIO_AUTH_TOKEN"]
TWILIO_PHONE_NUMBER = os.environ["TWILIO_PHONE_NUMBER"]
twilio_client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

async def handle_call_completion(caller_num: str):
    # Connect to the database
    conn = sqlite3.connect('collected_information.db')
    cursor = conn.cursor()

    # Example: Selecting all rows from the table
    cursor.execute("SELECT * FROM collected_information")
    rows = cursor.fetchall()

    # Close the connection
    conn.close()

    # Prepare message content
    message_content = "\n".join([f"{row[0]}: {row[1]}" for row in rows])  # Modify this based on your database schema

    # Fetch caller's number from the request or from the database, if available
    caller_number = caller_num

    # Send SMS to the caller
    twilio_client.messages.create(
        to=caller_number,
        from_=TWILIO_PHONE_NUMBER,
        body=message_content
    )

    # Return a response indicating successful handling
    return {"message": "Database operations completed successfully and SMS sent to the caller"}

