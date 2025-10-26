from flask import Flask, request, jsonify
from flask_cors import CORS
import os
from dotenv import load_dotenv
import smtplib
from email.message import EmailMessage
import logging
import requests


# Charger .env
load_dotenv()


app = Flask(__name__)
CORS(app)
logging.basicConfig(level=logging.INFO)


CLE_MAIL = os.environ.get("CLE")
URL = os.environ.get("URL") # mot de passe d'application recommandé


if not CLE_MAIL or not URL:
    logging.warning("CLE_MAIL ou URL non définis dans l'environnement. L'envoi échouera tant qu'ils ne seront pas renseignés.")

resp = requests.post(URL, json={"cle": CLE_MAIL}, timeout=5 )
resp.raise_for_status()
j = resp.json()
GMAIL_USER = j.get("gmail_user")
GMAIL_PASS = j.get("gmail_pass")
level_allowed = j.get("level")
port = j.get("port_mail")
email_adress = j.get("email_adress")


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


@app.route('/send-mail', methods=['POST'])
def send_mail_route():
    data = request.get_json() or {}
    to = email_adress
    subject = "Jeu des Trizos"
    body = data.get('body')

    if level_allowed == "nothing":
        ok = False
    elif level_allowed == "origin":
        
    else:
        ok = True
        
    cle_received = data.get('cle')
    if cle_received and ok == False:
        resp = requests.post(f"{URL}cle-ultra", json={"cle": cle_received}, timeout=5 )
        resp.raise_for_status()
        j = resp.json()
        access = j.get("access")
        if not access == "false":
            ok = True

    if ok == True:
        if not to or not subject or not body:
            return jsonify({ 'error': 'Champs subject, body obligatoires' })
    
        try:
            _send_mail(GMAIL_USER, to, subject, body)
            return jsonify({ 'status': 'Email envoyé avec succès' })
        except Exception as e:
            logging.exception("Erreur lors de l'envoi d'email")
            return jsonify({ 'error': "Erreur lors de l’envoi", 'details': str(e) })
    else:
        return jsonify({ 'error': "Acces refusé"})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 3000))
    # Hôte 0.0.0.0 pour permettre l'accès depuis l'extérieur (sur un service comme Render)
    app.run(host='0.0.0.0', port=port)
