import httpx

async def search_web(query, searxng_url):
    if not searxng_url:
        return []
    try:
        async with httpx.AsyncClient(timeout=20, follow_redirects=True) as c:
            r=await c.get(searxng_url.rstrip('/')+'/search', params={'q':query,'format':'json','language':'en'})
            r.raise_for_status()
            data=r.json()
    except (httpx.HTTPError, ValueError):
        return []
        return [{'title':x.get('title',''),'url':x.get('url',''),'content':x.get('content','')} for x in data.get('results',[])[:8]]

async def fetch_page(url):
    async with httpx.AsyncClient(timeout=30,follow_redirects=True,headers={'User-Agent':'Darshan-JARVIS/2.0'}) as c:
        r=await c.get(url); r.raise_for_status(); return r.text[:200000]
