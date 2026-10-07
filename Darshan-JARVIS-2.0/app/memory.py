import sqlite3,time
from .config import DB_PATH
SCHEMA='''CREATE TABLE IF NOT EXISTS memories(id INTEGER PRIMARY KEY AUTOINCREMENT,kind TEXT,text TEXT,source TEXT,confidence REAL,approved INTEGER,created_at REAL,updated_at REAL); CREATE TABLE IF NOT EXISTS audit(id INTEGER PRIMARY KEY AUTOINCREMENT,action TEXT,risk TEXT,status TEXT,details TEXT,created_at REAL); CREATE TABLE IF NOT EXISTS policies(key TEXT PRIMARY KEY,value TEXT,updated_at REAL);'''
def db():
    c=sqlite3.connect(DB_PATH); c.row_factory=sqlite3.Row; c.executescript(SCHEMA); return c
def add_memory(kind,text,source='user',confidence=1.0,approved=True):
    n=time.time()
    with db() as c:
        x=c.execute('INSERT INTO memories(kind,text,source,confidence,approved,created_at,updated_at) VALUES(?,?,?,?,?,?,?)',(kind,text,source,confidence,int(approved),n,n)); return x.lastrowid
def search_memories(query,limit=8):
    words=[w.strip('.,!?').lower() for w in query.split() if len(w)>2][:8]
    if not words:return []
    where=' OR '.join(['lower(text) LIKE ?']*len(words))
    with db() as c: rows=c.execute(f'SELECT id,kind,text,source,confidence FROM memories WHERE approved=1 AND ({where}) ORDER BY confidence DESC,updated_at DESC LIMIT ?',(*[f'%{w}%' for w in words],limit)).fetchall()
    return [dict(x) for x in rows]
def audit(action,risk,status,details=''):
    with db() as c:c.execute('INSERT INTO audit(action,risk,status,details,created_at) VALUES(?,?,?,?,?)',(action,risk,status,details,time.time()))
def recent_audit(limit=30):
    with db() as c:return [dict(x) for x in c.execute('SELECT * FROM audit ORDER BY created_at DESC LIMIT ?',(limit,)).fetchall()]
