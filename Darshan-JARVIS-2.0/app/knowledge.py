import re, sqlite3, time
from .config import DB_PATH

def init_knowledge():
    with sqlite3.connect(DB_PATH) as c:
        c.execute('CREATE VIRTUAL TABLE IF NOT EXISTS knowledge USING fts5(title,content,source,url,created_at UNINDEXED)')

def remember(title, content, source='user', url=''):
    init_knowledge()
    with sqlite3.connect(DB_PATH) as c:
        c.execute(
            'INSERT INTO knowledge(title,content,source,url,created_at) VALUES(?,?,?,?,?)',
            (title, content, source, url, time.time()),
        )

def search_knowledge(query, limit=6):
    init_knowledge()
    # SQLite FTS5 treats punctuation such as *, :, (, ) as query syntax.
    # JARVIS receives natural-language prompts, so convert them to safe tokens.
    tokens = re.findall(r'[A-Za-z0-9_]+', query or '')
    if not tokens:
        return []
    fts_query = ' OR '.join('"' + t.replace('"', '""') + '"' for t in tokens[:40])
    with sqlite3.connect(DB_PATH) as c:
        try:
            rows = c.execute(
                'SELECT title,content,source,url FROM knowledge WHERE knowledge MATCH ? ORDER BY rank LIMIT ?',
                (fts_query, limit),
            ).fetchall()
        except sqlite3.OperationalError:
            return []
    return [{'title':r[0], 'content':r[1], 'source':r[2], 'url':r[3]} for r in rows]
