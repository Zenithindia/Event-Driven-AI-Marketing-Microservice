from celery import Celery
import os
import requests
import smtplib
from email.message import EmailMessage

CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")
celery_app = Celery("tasks", broker=CELERY_BROKER_URL)

# Ollama using the Docker Gateway to bypass Windows Firewall
OLLAMA_URL = "http://host.docker.internal:11434/api/generate"

# --- MAILTRAP CREDENTIALS ---
SMTP_HOST = "sandbox.smtp.mailtrap.io"
SMTP_PORT = 2525
SMTP_USER = "8290ab4bbc8f90"
SMTP_PASS = "18f2912f686e7f" # <--- DO NOT FORGET TO UPDATE THIS

@celery_app.task(name="tasks.process_abandoned_cart")
def process_abandoned_cart(email: str, name: str, item: str):
    print(f"WORKER: Starting AI generation for {name}'s abandoned {item}...")
    
    prompt = f"Write a short, engaging email for a customer named {name} who abandoned their shopping cart containing: {item}. Just write the email body, keep it to 2 sentences."
    payload = {"model": "llama3.2:3b", "prompt": prompt, "stream": False}

    try:
        response = requests.post(OLLAMA_URL, json=payload)
        response.raise_for_status()
        ai_body = response.json().get("response", "")
        
        msg = EmailMessage()
        msg.set_content(ai_body)
        msg['Subject'] = f"Hey {name}, you left your {item} behind!"
        msg['From'] = "hello@smartnotifier.com"
        msg['To'] = email

        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls() # The Secure Handshake!
            server.login(SMTP_USER, SMTP_PASS)
            server.send_message(msg)

        print(f"WORKER: SUCCESS! Abandoned Cart email sent to {email}.")
        return True
    except Exception as e:
        print(f"WORKER ERROR: {e}")
        return False

@celery_app.task(name="tasks.process_product_interest")
def process_product_interest(email: str, name: str, item: str):
    print(f"WORKER: AI drafting 'High Intent' email for {name} ({item})...")
    
    prompt = f"Write a short, friendly 2-sentence email for a customer named {name} who was just looking at the {item} but didn't buy it. Tell them it's a popular item and offer to answer any questions they might have."
    payload = {"model": "llama3.2:3b", "prompt": prompt, "stream": False}

    try:
        response = requests.post(OLLAMA_URL, json=payload)
        response.raise_for_status()
        ai_body = response.json().get("response", "")
        
        msg = EmailMessage()
        msg.set_content(ai_body)
        msg['Subject'] = f"Still thinking about the {item}, {name}?"
        msg['From'] = "hello@smartnotifier.com"
        msg['To'] = email

        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls() # The Secure Handshake!
            server.login(SMTP_USER, SMTP_PASS)
            server.send_message(msg)

        print(f"WORKER: SUCCESS! 'Interest' email sent to {email}.")
        return True
    except Exception as e:
        print(f"WORKER ERROR: {e}")
        return False