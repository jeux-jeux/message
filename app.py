from flask import Flask, request, jsonify
from flask_cors import CORS
import os
from dotenv import load_dotenv
import smtplib
from email.message import EmailMessage
import logging


# Charger .env
load_dotenv()


app = Flask(__name__)
CORS(app)
logging.basicConfig(level=logging.INFO)


GMAIL_USER = os.environ.get("GMAIL_USER")
GMAIL_PASS = os.environ.get("GMAIL_PASS") # mot de passe d'application recommandé


if not GMAIL_USER or not GMAIL_PASS:
logging.warning("GMAIL_USER ou GMAIL_PASS non définis dans l'environnement. L'envoi échouera tant qu'ils ne seront pas renseignés.")




def _send_mail(from_addr: str, to_addr: str, subject: str, body: str) -> None:
"""Envoie un email via le SMTP Gmail (TLS/587)."""
msg = EmailMessage()
msg.set_content(body)
msg["Subject"] = subject
msg["From"] = from_addr
msg["To"] = to_addr


# Connexion SMTP TLS
with smtplib.SMTP("smtp.gmail.com", 587, timeout=10) as smtp:
smtp.ehlo()
smtp.starttls()
smtp.ehlo()
smtp.login(GMAIL_USER, GMAIL_PASS)
smtp.send_message(msg)




@app.route('/', methods=['POST'])
def send_mail_route():
data = request.get_json() or {}
to = data.get('to')
subject = data.get('subject')
body = data.get('body')


if not to or not subject or not body:
return jsonify({ 'error': 'Champs to, subject, body obligatoires' }), 400


try:
_send_mail(GMAIL_USER, to, subject, body)
return jsonify({ 'status': 'Email envoyé avec succès' })
except Exception as e:
logging.exception("Erreur lors de l'envoi d'email")
app.run(host='0.0.0.0', port=port)
