import os
import json
import hashlib
import secrets
from datetime import datetime
from pymongo import MongoClient
from pymongo.server_api import ServerApi

# Конфігурація
GENRES = [
    "Поп", "Рок", "Фолк", "Реп", "Електронна", "Інді", "Джаз", 
    "Класична", "Альтернатива", "R&B/Soul", "Метал", "Реггі", 
    "Блюз", "Кантрі", "Латино", "Фанк", "Панк", "Транс", 
    "Шансон", "Дабстеп"
]

STUDENT_IDS = [f"STU_{str(i).zfill(3)}" for i in range(1, 21)] + ["TEACHER_001"]

# MongoDB клієнт (singleton)
_db_client = None

def get_db():
    """Отримання підключення до MongoDB"""
    global _db_client
    
    if _db_client is None:
        uri = os.environ.get('MONGODB_URI')
        
        if not uri:
            raise ValueError("MONGODB_URI not set in environment variables")
        
        _db_client = MongoClient(uri, server_api=ServerApi('1'))
    
    return _db_client.music_voting

def load_db():
    """Завантаження даних з MongoDB"""
    try:
        db = get_db()
        votes_collection = db.votes
        
        votes = list(votes_collection.find({}, {'_id': 0}))
        voted_ids = [v['id'] for v in votes]
        
        return {
            "votes": votes,
            "voted_ids": voted_ids
        }
    except Exception as e:
        # Fallback для помилок підключення
        return {"votes": [], "voted_ids": []}

def save_vote(vote_record):
    """Збереження голосу в MongoDB"""
    try:
        db = get_db()
        votes_collection = db.votes
        
        # Перевірка чи вже голосував
        if votes_collection.find_one({"id": vote_record["id"]}):
            return False
        
        votes_collection.insert_one(vote_record)
        return True
    except Exception as e:
        return False

def generate_hash(data):
    return hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest()

def html_template(title, content):
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
        .form-group {{ margin-bottom: 25px; }}
        label {{
            display: block;
            font-weight: 600;
            margin-bottom: 8px;
            color: #2d3748;
            font-size: 1.1em;
        }}
        select, input, button {{
            width: 100%;
            padding: 12px 15px;
            border: 2px solid #e2e8f0;
            border-radius: 8px;
            font-size: 16px;
        }}
        select:focus, input:focus {{
            outline: none;
            border-color: #5a67d8;
            box-shadow: 0 0 0 3px rgba(90,103,216,0.1);
        }}
        .priority-section {{
            background: #f7fafc;
            padding: 25px;
            border-radius: 12px;
            margin-bottom: 20px;
            border: 2px solid #e2e8f0;
        }}
        .priority-section.gold {{
            border-color: #ffd700;
            background: linear-gradient(135deg, #fffbeb 0%, #fef3c7 100%);
        }}
        .priority-section.silver {{
            border-color: #c0c0c0;
            background: linear-gradient(135deg, #f3f4f6 0%, #e5e7eb 100%);
        }}
        .priority-section.bronze {{
            border-color: #cd7f32;
            background: linear-gradient(135deg, #fef3f2 0%, #fee2e2 100%);
        }}
        .badge {{
            display: inline-block;
            padding: 5px 12px;
            border-radius: 20px;
            font-size: 0.9em;
            font-weight: bold;
            margin-bottom: 10px;
        }}
        .badge.gold {{ background: #ffd700; color: #744210; }}
        .badge.silver {{ background: #c0c0c0; color: #374151; }}
        .badge.bronze {{ background: #cd7f32; color: white; }}
        button {{
            background: linear-gradient(135deg, #5a67d8 0%, #4c51bf 100%);
            color: white;
            border: none;
            font-size: 1.2em;
            font-weight: 600;
            cursor: pointer;
            transition: transform 0.2s;
        }}
        button:hover {{ transform: translateY(-2px); box-shadow: 0 10px 30px rgba(90,103,216,0.3); }}
        .result-box {{
            display: none;
            margin-top: 30px;
            padding: 30px;
            background: #f0fff4;
            border: 2px solid #48bb78;
            border-radius: 12px;
            text-align: center;
        }}
        .hash-box {{
            background: #1a202c;
            color: #48bb78;
            padding: 15px;
            border-radius: 8px;
            font-family: 'Courier New', monospace;
            font-size: 0.9em;
            word-break: break-all;
            margin: 15px 0;
        }}
        .error {{
            color: #e53e3e;
            font-size: 0.9em;
            margin-top: 5px;
            display: none;
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
        tr:hover {{ background: #f7fafc; }}
        .rank-1 {{ background: #fffbeb !important; font-weight: bold; }}
        .rank-2 {{ background: #f3f4f6 !important; }}
        .rank-3 {{ background: #fef3f2 !important; }}
        .leaders {{
            background: #e6fffa;
            border: 2px solid #38b2ac;
            padding: 20px;
            border-radius: 10px;
            margin: 20px 0;
        }}
        .metric {{
            display: inline-block;
            background: #edf2f7;
            padding: 5px 10px;
            border-radius: 15px;
            margin: 2px;
            font-size: 0.9em;
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
        code {{
            background: #edf2f7;
            padding: 2px 6px;
            border-radius: 4px;
            font-family: monospace;
        }}
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 15px;
            margin: 20px 0;
        }}
        .stat-card {{
            background: #f7fafc;
            padding: 20px;
            border-radius: 10px;
            text-align: center;
        }}
        .stat-number {{
            font-size: 2em;
            font-weight: bold;
            color: #5a67d8;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🎵 Експертне опитування</h1>
            <p>Пріоритизація жанрів української музики (ID-анонімність)</p>
        </div>
        <div class="content">
            {content}
        </div>
    </div>
</body>
</html>"""