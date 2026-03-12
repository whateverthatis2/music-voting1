import os
import json
import hashlib
import secrets
from datetime import datetime
from pymongo import MongoClient
from pymongo.server_api import ServerApi

# Константи
GENRES = [
    "Поп", "Рок", "Фолк", "Реп", "Електронна", "Інді", "Джаз",
    "Класична", "Альтернатива", "R&B/Soul", "Метал", "Реггі",
    "Блюз", "Кантрі", "Латино", "Фанк", "Панк", "Транс",
    "Шансон", "Дабстеп"
]

STUDENT_IDS = [f"STU_{str(i).zfill(3)}" for i in range(1, 21)] + ["TEACHER_001"]

HEURISTICS = [
    {"id": "E1", "name": "Тільки 3-тє місце", "desc": "Прибрати жанри, що були лише на 3-му місці"},
    {"id": "E2", "name": "Тільки 2-ге місце", "desc": "Прибрати жанри, що були лише на 2-му місці"},
    {"id": "E3", "name": "1 голос", "desc": "Прибрати жанри з мінімальною підтримкою (1 голос)"},
    {"id": "E4", "name": "Без 1-го місця", "desc": "Прибрати жанри, що ніколи не були на 1-му місці"},
    {"id": "E5", "name": "Найрідший", "desc": "Прибрати найрідше згадуваний жанр"},
    {"id": "E6", "name": "Тільки 1-ше місце", "desc": "Прибрати жанри, що були лише на 1-му місці"},
    {"id": "E7", "name": "Без 1-го місця (2-3)", "desc": "Прибрати жанри тільки з 2-3 місць"},
]

# MongoDB клієнт
_db_client = None

def get_db():
    """Отримання підключення до MongoDB"""
    global _db_client
    if _db_client is not None:
        return _db_client.music_voting
    
    uri = os.environ.get('MONGODB_URI')
    if not uri:
        raise ValueError("MONGODB_URI not set in environment variables")
    
    _db_client = MongoClient(uri, server_api=ServerApi('1'), connectTimeoutMS=5000)
    return _db_client.music_voting

def load_db():
    """Завантаження даних з MongoDB (голоси за жанри)"""
    try:
        db = get_db()
        votes_collection = db.votes
        votes = list(votes_collection.find({}, {'_id': 0}))
        voted_ids = [v['id'] for v in votes]
        return {
            "votes": votes,
            "voted_ids": voted_ids,
            "ok": True
        }
    except Exception as e:
        return {
            "votes": [],
            "voted_ids": [],
            "ok": False,
            "error": str(e)
        }

def generate_hash(data):
    """Генерація SHA-256 хешу"""
    return hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest()

def html_template(title, content):
    """Шаблон HTML сторінки"""
    return f"""<!DOCTYPE html>
<html lang="uk">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: 'Segoe UI', system-ui, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }}
        .container {{
            max-width: 1000px;
            margin: 0 auto;
            background: white;
            border-radius: 20px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            overflow: hidden;
        }}
        .header {{
            background: linear-gradient(135deg, #5a67d8 0%, #4c51bf 100%);
            color: white;
            padding: 40px;
            text-align: center;
        }}
        .header h1 {{ font-size: 2.5em; margin-bottom: 10px; }}
        .content {{ padding: 40px; }}
        .info-box {{
            background: #fffaf0;
            border-left: 5px solid #ed8936;
            padding: 20px;
            margin-bottom: 30px;
            border-radius: 0 8px 8px 0;
        }}
        .error-box {{
            background: #fed7d7;
            border-left: 5px solid #e53e3e;
            padding: 20px;
            margin-bottom: 30px;
            border-radius: 0 8px 8px 0;
            color: #c53030;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }}
        th, td {{
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #e2e8f0;
        }}
        th {{
            background: #5a67d8;
            color: white;
        }}
        .links {{
            margin-top: 30px;
            text-align: center;
        }}
        .links a {{
            color: #5a67d8;
            text-decoration: none;
            margin: 0 15px;
            font-weight: 500;
        }}
        .ranking {{
            background: #e6fffa;
            padding: 15px;
            border-radius: 6px;
            margin-bottom: 20px;
        }}
        .rank-item {{
            display: flex;
            justify-content: space-between;
            padding: 8px 0;
            border-bottom: 1px solid #b2f5ea;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🎵 Експертне опитування</h1>
            <p>Пріоритизація жанрів української музики</p>
        </div>
        <div class="content">
            {content}
        </div>
    </div>
</body>
</html>"""
