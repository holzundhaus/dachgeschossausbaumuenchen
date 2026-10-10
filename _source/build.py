"""Build approved article data into the existing static blog. No network calls."""
from pathlib import Path
import json,html,re,sys,xml.etree.ElementTree as ET
root=Path(__file__).resolve().parent
cfg=json.loads((root/'site.json').read_text(encoding='utf-8'));posts=json.loads((root/'posts.json').read_text(encoding='utf-8'))
out=Path(sys.argv[1]).resolve() if len(sys.argv)>1 else root.parent/'dist';out.mkdir(parents=True,exist_ok=True)
template=(root/'template.html').read_text(encoding='utf-8');E=lambda s:html.escape(str(s),quote=True)
base=cfg['url'].rstrip('/');prefix='/'+base.split('/')[-1] if cfg.get('platform')=='github' else ''
live=sorted([p for p in posts if p.get('approved') is True],key=lambda p:p['date'],reverse=True)
if any(not re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*',p['slug']) for p in live):raise ValueError('Invalid article slug')
if len({p['slug'] for p in live})!=len(live):raise ValueError('Duplicate article slug')
cards=''.join(f'<div class="card"><p>{E(p["date"])} · {E(p["category"])}</p><h2><a href="{prefix}/blog/{p["slug"]}/">{E(p["title"])}</a></h2><p>{E(p["description"])}</p></div>' for p in live) or '<div class="card"><h2>Noch keine Beiträge veröffentlicht</h2><p>Neue Beiträge erscheinen hier und im RSS-Feed.</p></div>'
def make(path,title,description,body,hero=False):
 h=re.sub(r'<title>.*?</title>','<title>'+E(title)+' | '+E(cfg['title'])+'</title>',template,count=1)
 for attr,value in [('name="description"',description),('property="og:title"',title),('property="og:description"',description)]:h=re.sub(r'<meta '+attr+r' content="[^"]*">','<meta '+attr+' content="'+E(value)+'">',h,count=1)
 h=re.sub(r'<link rel="canonical" href="[^"]*">','<link rel="canonical" href="'+E(base+path)+'">',h,count=1)
 if hero:
  h=re.sub(r'<section class="wrap"><h2>Aus dem Blog</h2>.*?</section>','<section class="wrap"><h2>Aus dem Blog</h2>'+body+'</section>',h,count=1,flags=re.S)
 else:h=re.sub(r'<main>.*?</main>','<main><section class="wrap">'+body+'</section></main>',h,count=1,flags=re.S)
 dest=out/path.strip('/')/'index.html' if path!='/' else out/'index.html';dest.parent.mkdir(parents=True,exist_ok=True);dest.write_text(h,encoding='utf-8')
make('/',cfg['title'],cfg['description'],cards,True);make('/blog/','Blog',cfg['description'],cards)
for p in live:
 body='<article><h1>'+E(p['title'])+'</h1><p>'+E(p['date'])+' · '+E(p['category'])+'</p>'+''.join('<p>'+E(text)+'</p>' for text in p['paragraphs'])+'</article>'
 # Keep the request form in the upper section on article pages as well.
 form=re.search(r'<section class="form-panel">.*?</section>',template,re.S).group(0)
 make('/blog/'+p['slug']+'/',p['title'],p['description'],'<div class="hero"><div>'+body+'</div>'+form+'</div>')
make('/archiv/','Archiv',cfg['description'],'<h1>Archiv</h1>'+cards)
categories=sorted({p['category'] for p in live})
make('/kategorien/','Kategorien',cfg['description'],'<h1>Kategorien</h1>'+''.join('<h2>'+E(c)+'</h2>'+''.join(f'<p><a href="{prefix}/blog/{p["slug"]}/">{E(p["title"])}</a></p>' for p in live if p['category']==c) for c in categories))
rss=ET.Element('rss',version='2.0');channel=ET.SubElement(rss,'channel')
for key,val in [('title',cfg['title']),('description',cfg['description']),('link',base+'/'),('language','de')]:ET.SubElement(channel,key).text=val
for p in live:
 item=ET.SubElement(channel,'item')
 for key,val in [('title',p['title']),('description',p['description']),('link',base+'/blog/'+p['slug']+'/'),('guid',base+'/blog/'+p['slug']+'/')]:ET.SubElement(item,key).text=val
ET.ElementTree(rss).write(out/'feed.xml',encoding='utf-8',xml_declaration=True)
sitemap=ET.Element('urlset',xmlns='http://www.sitemaps.org/schemas/sitemap/0.9')
for route in ['/','/blog/','/archiv/','/kategorien/','/impressum/','/datenschutz/']+['/blog/'+p['slug']+'/' for p in live]:ET.SubElement(ET.SubElement(sitemap,'url'),'loc').text=base+route
ET.ElementTree(sitemap).write(out/'sitemap.xml',encoding='utf-8',xml_declaration=True)
print('Built',len(live),'approved articles')
