import sqlite3,time
from .config import DB_PATH

def init_knowledge():
    with sqlite3.connect(DB_PATH) as c:
        c.execute('CREATE VIRTUAL TABLE IF NOT EXISTS knowledge USING fts5(title,content,source,url,created_at UNINDEXED)')

def remember(title,content,source='user',url=''):
    init_knowledge()
    with sqlite3.connect(DB_PATH) as c:
        c.execute('INSERT INTO knowledge(title,content,source,url,created_at) VALUES(?,?,?,?,?)',(title,content,source,url,time.time()))

def search_knowledge(query,limit=6):
    init_knowledge()
    with sqlite3.connect(DB_PATH) as c:
        safe_query = '"' + query.replace('"', '""') + '"'
        rows=c.execute('SELECT title,content,source,url FROM knowledge WHERE knowledge MATCH ? ORDER BY rank LIMIT ?', (safe_query,limit)).fetchall()
    return [{'title':r[0],'content':r[1],'source':r[2],'url':r[3]} for r in rows]
