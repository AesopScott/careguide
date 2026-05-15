import firebase_admin
from firebase_admin import credentials, firestore, auth
import os

_app = None

def init_firebase():
    global _app
    if _app:
        return
    cred_path = os.getenv("FIREBASE_CREDENTIALS_PATH", "../config/careguide-adminsdk.json")
    cred = credentials.Certificate(cred_path)
    _app = firebase_admin.initialize_app(cred)

def get_db():
    init_firebase()
    return firestore.client()

def verify_token(id_token: str) -> dict:
    init_firebase()
    return auth.verify_id_token(id_token)
