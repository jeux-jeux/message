from flask import Flask, request, jsonify
from flask_cors import CORS
import os
from dotenv import load_dotenv
import smtplib
from email.message import EmailMessage
import logging
import requests
import base64
from email.mime.text import MIMEText
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
import logging

# Charger .env
load_dotenv()


app = Flask(__name__)
CORS(app)
logging.basicConfig(level=logging.INFO)


CLE_MESSAGE = os.environ.get("CLE")
URL = os.environ.get("URL") # mot de passe d'application recommandé


if not CLE_MESSAGE or not URL:
    logging.warning("CLE_MAIL ou URL non définis dans l'environnement. L'envoi échouera tant qu'ils ne seront pas renseignés.")

resp = requests.post(URL, json={"cle": CLE_MESSAGE}, timeout=5 )
resp.raise_for_status()
j = resp.json()
GMAIL_USER = j.get("gmail_user")
GMAIL_PASS = j.get("gmail_pass")
level_allowed = j.get("level")
allowed = j.get('allowed')
port = j.get("port_message")
email = j.get("email")
ntfy_url = j.get('ntfy_url')

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import json

def _send_mail(from_addr: str, to_addr: str, subject: str, body: str) -> None:
    """Envoie un e-mail via l'API Gmail sans fichier token."""
    try:
        # Le token JSON est stocké dans une variable d'environnement
        token_json = GMAIL_PASS
        if not token_json:
            raise Exception("Reponse GMAIL_TOKEN manquante")

        # Charger le JSON directement en mémoire
        creds_data = json.loads(token_json)
        creds = Credentials.from_authorized_user_info(creds_data)

        service = build("gmail", "v1", credentials=creds)

        message = {
            "raw": base64.urlsafe_b64encode(
                f"From: {from_addr}\r\nTo: {to_addr}\r\nSubject: {subject}\r\n\r\n{body}".encode("utf-8")
            ).decode("utf-8")
        }

        service.users().messages().send(userId="me", body=message).execute()

    except HttpError as error:
        raise Exception(f"Erreur API Gmail : {error}")
    except Exception as e:
        raise Exception(f"Erreur lors de l’envoi : {e}")


        
@app.route('/ntfy', methods=['POST'])
def send_ntfy_route():
    data = request.get_json() or {}
    message = data.get('message')
    origin = request.headers.get('Origin')

    if level_allowed == "nothing":
        ok = False
    elif level_allowed == "origin":
        origin = request.headers.get('Origin')
        if origin and origin in allowed:
            ok = True
        else:
            ok = False
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
        if not message:
            return jsonify({ 'error': 'Champs message obligatoire' })
    
        try:
            resp = requests.post(ntfy_url, data=message, headers={"Content-Type": "text/plain"}, timeout=5 )
            return jsonify({ 'status': 'Message ntfy envoyé avec succès' })
        except Exception as e:
            logging.exception("Erreur lors de l'envoi d'email")
            return jsonify({ 'error': "Erreur lors de l’envoi"})
    else:
        return jsonify({ 'error': "Acces refusé"})

@app.route('/mail', methods=['POST'])
def send_mail_route():
    data = request.get_json() or {}
    to = email
    subject = "Jeu des Trizos"
    body = data.get('body')
    origin = request.headers.get('Origin')

    if level_allowed == "nothing":
        ok = False
    elif level_allowed == "origin":
        origin = request.headers.get('Origin')
        if origin and origin in allowed:
            ok = True
        else:
            ok = False
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


@app.route("/wake", methods=["POST"])
def wake():
    data = request.get_json(force=True, silent=True) or {}
    cle_received = data.get('cle')
    if cle_received:
        resp = requests.post(f"{URL}cle-ultra", json={"cle": cle_received}, timeout=5 )
        resp.raise_for_status()
        j = resp.json()
        access = j.get("access")
        if not access == "false":
            return jsonify({"status": "ok"})
    return jsonify({"status": "error", "message": "clé invalide"})


if __name__ == '__main__':
    port = int(port)
    # Hôte 0.0.0.0 pour permettre l'accès depuis l'extérieur (sur un service comme Render)
    app.run(host='0.0.0.0', port=port)



