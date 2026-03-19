import os
from pymongo import MongoClient
from pymongo.server_api import ServerApi

_db = None

def get_db():
    global _db
    if _db: return _db
    uri = os.environ.get('MONGODB_URI')
    if not uri: raise ValueError("MONGODB_URI missing")
    # Важливо: music_voting - назва бази даних
    _db = MongoClient(uri, server_api=ServerApi('1'), connectTimeoutMS=5000).music_voting
    return _db

OBJECTS = ["Поп","Рок","Фолк","Реп","Електронна","Інді","Джаз","Класична","Метал","R&B/Soul"]

def html(title, content):
    return f"""<!DOCTYPE html><html><head><meta charset="UTF-8"><title>{title}</title>
    <style>body{{font-family:sans-serif;max-width:900px;margin:20px auto;padding:20px}}
    table{{width:100%;border-collapse:collapse;margin:15px 0}}
    th,td{{padding:8px;border:1px solid #ddd;text-align:left}}
    th{{background:#5a67d8;color:white}}
    .info{{background:#fffaf0;padding:15px;border-left:4px solid #ed8936;margin:15px 0}}
    a{{color:#5a67d8;margin:0 10px}}</style></head>
    <body><h1>{title}</h1>{content}</body></html>"""
