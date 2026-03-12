# ==================== КОНФІГУРАЦІЯ ====================

# 10 об'єктів для ранжування
OBJECTS = ["Об'єкт "+str(i) for i in range(1, 11)]

# 5-8 експертів
EXPERTS = ["Експерт "+str(i) for i in range(1, 9)]

# Пароль для перегляду протоколу
PROTOCOL_PASSWORD = "0000"

# ==================== MONGODB ====================

import os, hashlib, json
from pymongo import MongoClient
from pymongo.server_api import ServerApi

_db_client = None

def get_db():
    global _db_client
    if _db_client is None:
        uri = os.environ.get('MONGODB_URI')
        if not uri:
            raise ValueError("MONGODB_URI not set")
        _db_client = MongoClient(uri, server_api=ServerApi('1'))
    return _db_client.expert_ranking

def load_rankings():
    try:
        db = get_db()
        rankings = list(db.rankings.find({}, {'_id': 0}))
        return rankings
    except:
        return []

def save_ranking(expert, ranking):
    try:
        db = get_db()
        existing = db.rankings.find_one({"expert": expert})
        if existing:
            db.rankings.update_one({"expert": expert}, {"$set": {"ranking": ranking, "time": __import__('datetime').datetime.now().isoformat()}})
        else:
            db.rankings.insert_one({"expert": expert, "ranking": ranking, "time": __import__('datetime').datetime.now().isoformat()})
        return True
    except:
        return False

# ==================== HTML ШАБЛОН ====================

def html_template(title, content):
    return f'''<!DOCTYPE html>
<html lang="uk"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>{title}</title>
<style>*{{margin:0;padding:0;box-sizing:border-box}}body{{font-family:'Segoe UI',system-ui,sans-serif;background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);min-height:100vh;padding:20px}}.container{{max-width:1200px;margin:0 auto;background:white;border-radius:20px;box-shadow:0 20px 60px rgba(0,0,0,0.3);overflow:hidden}}.header{{background:linear-gradient(135deg,#5a67d8 0%,#4c51bf 100%);color:white;padding:40px;text-align:center}}.header h1{{font-size:2em;margin-bottom:10px}}.content{{padding:30px}}.info-box{{background:#fffaf0;border-left:5px solid #ed8936;padding:20px;margin-bottom:20px;border-radius:0 8px 8px 0}}.links{{margin-top:20px;text-align:center}}.links a{{color:#5a67d8;text-decoration:none;margin:0 15px;font-weight:500}}table{{width:100%;border-collapse:collapse;margin:20px 0}}th,td{{padding:12px;text-align:left;border-bottom:1px solid #ddd}}th{{background:#5a67d8;color:white}}.btn{{background:#5a67d8;color:white;padding:10px 20px;border-radius:6px;text-decoration:none;display:inline-block;margin:10px 5px}}.btn:hover{{background:#4c51bf}}</style></head>
<body><div class="container"><div class="header"><h1>🔬 Експертне ранжування</h1><p>Система підтримки прийняття рішень</p></div><div class="content">{content}</div></div></body></html>'''
