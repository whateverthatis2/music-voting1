import os, json, hashlib, secrets, random
from datetime import datetime
from pymongo import MongoClient
from pymongo.server_api import ServerApi

GENRES = ["Поп","Рок","Фолк","Реп","Електронна","Інді","Джаз","Класична","Альтернатива","R&B/Soul","Метал","Реггі","Блюз","Кантрі","Латино","Фанк","Панк","Транс","Шансон","Дабстеп"]
STUDENT_IDS = [f"STU_{str(i).zfill(3)}" for i in range(1, 21)] + ["TEACHER_001"]

HEURISTICS = [
    {"id":"E1","name":"Тільки 3-тє місце","desc":"Прибрати жанри, що були лише на 3-му місці"},
    {"id":"E2","name":"Тільки 2-ге місце","desc":"Прибрати жанри, що були лише на 2-му місці"},
    {"id":"E3","name":"1 голос","desc":"Прибрати жанри з мінімальною підтримкою"},
    {"id":"E4","name":"Без 1-го місця","desc":"Прибрати жанри без 1-го місця"},
    {"id":"E5","name":"Найрідший","desc":"Прибрати найрідше згадуваний жанр"},
    {"id":"E6","name":"Тільки 1-ше місце","desc":"Прибрати жанри лише з 1-го місця"},
    {"id":"E7","name":"Тільки 2-3 місця","desc":"Прибрати жанри без 1-го місця"},
]

RANKING_OBJECTS = ["Фанк","Рок","Електронна","Інді","Реп","R&B/Soul","Панк","Транс","Блюз","Латино"]

_db = None
def get_db():
    global _db
    if _db: return _db
    uri = os.environ.get('MONGODB_URI')
    if not uri: raise ValueError("MONGODB_URI missing")
    _db = MongoClient(uri, server_api=ServerApi('1'), connectTimeoutMS=5000).music_voting
    _db.admin.command('ping')
    return _db

def load_votes():
    try:
        db = get_db()
        votes = list(db.votes.find({}, {'_id':0}))
        return {"votes":votes, "voted_ids":[v['id'] for v in votes], "ok":True}
    except Exception as e:
        return {"votes":[], "voted_ids":[], "ok":False, "error":str(e)}

def generate_hash(data):
    return hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest()

def html(title, content):
    return f"""<!DOCTYPE html><html lang="uk"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{title}</title>
<style>body{{font-family:system-ui,sans-serif;background:#f5f5f5;padding:20px;max-width:900px;margin:0 auto}}.container{{background:#fff;padding:25px;border-radius:10px;box-shadow:0 2px 8px rgba(0,0,0,.1)}}h1{{color:#333;border-bottom:2px solid #5a67d8;padding-bottom:10px}}.info{{background:#fffaf0;border-left:4px solid #ed8936;padding:15px;margin:15px 0}}button{{background:#5a67d8;color:#fff;border:none;padding:10px 20px;border-radius:6px;cursor:pointer}}button:disabled{{background:#ccc}}a{{color:#5a67d8;text-decoration:none;margin:0 10px}}table{{width:100%;border-collapse:collapse;margin:15px 0}}th,td{{padding:10px;border:1px solid #ddd;text-align:left}}th{{background:#5a67d8;color:#fff}}.error{{color:red}}.success{{color:green}}</style></head><body><div class="container"><h1>{title}</h1>{content}</div></body></html>"""
