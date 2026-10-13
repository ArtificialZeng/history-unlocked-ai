"""Static catalogue table projection; no network, credentials or source values."""
from html.parser import HTMLParser
import re
from urllib.parse import urljoin, urlsplit

ALLOWED_HEADERS={'Current Location and Name','Record Type','Status','Dates','Date','Cipher Type','Languages','Cleartext Language','Plaintext Language','ID','ID Descending','ID Ascending'}
VOID={'area','base','br','col','embed','hr','img','input','link','meta','param','source','track','wbr'}

class Node:
    def __init__(self,tag='',attrs=None,parent=None):
        self.tag=tag;self.attrs=dict(attrs or []);self.parent=parent;self.children=[]
    def text(self):
        return '' if self.tag in {'script','style'} else ' '.join(x.text() if isinstance(x,Node) else x for x in self.children)
    def descendants(self,tag=None):
        for x in self.children:
            if isinstance(x,Node):
                if tag is None or x.tag==tag:yield x
                yield from x.descendants(tag)

class DOM(HTMLParser):
    def __init__(self):super().__init__(convert_charrefs=True);self.root=Node();self.current=self.root
    def handle_starttag(self,tag,attrs):
        n=Node(tag,attrs,self.current);self.current.children.append(n)
        if tag not in VOID:self.current=n
    def handle_endtag(self,tag):
        n=self.current
        while n.parent and n.tag!=tag:n=n.parent
        if n.parent:self.current=n.parent
    def handle_data(self,value):self.current.children.append(value)

def normalized(n):return ' '.join(n.text().split())

def record_link(href,base_url):
    absolute=urljoin(base_url,href);p=urlsplit(absolute)
    match=re.fullmatch(r'/decrypt-web/RecordsView/(\d+)/?',p.path)
    if p.scheme!='https' or p.netloc!='de-crypt.org' or not match or p.username or p.password:
        return None
    return {'case_id':'decrypt:'+str(int(match.group(1))),'observed_detail_URL':absolute,
            'canonical_detail_URL':'https://de-crypt.org/decrypt-web/RecordsView/'+str(int(match.group(1)))}

def project(html,base_url):
    dom=DOM();dom.feed(html);rows=[];recognized=0;unparsed=0;empty=False
    for table in dom.root.descendants('table'):
        headers=[normalized(n) for n in table.descendants('th')]
        if not any(x=='Current Location and Name' for x in headers):continue
        recognized+=1
        for n in table.descendants():
            if n.attrs.get('class') in {'ew-no-record','ew-no-records'} and normalized(n).casefold() in {'no records found','no records','no records to display'}:
                empty=True
        for tr in table.descendants('tr'):
            cells=[x for x in tr.children if isinstance(x,Node) and x.tag=='td']
            if not cells:continue
            links=[record_link(a.attrs.get('href',''),base_url) for a in tr.descendants('a')]
            links=[x for x in links if x]
            empty_row=any(n.attrs.get('class') in {'ew-no-record','ew-no-records'} and normalized(n).casefold() in {'no records found','no records','no records to display'} for n in tr.descendants())
            pure_empty_row=(empty_row and len(cells)==1 and not any(tr.descendants('a'))
                            and normalized(tr).casefold() in {'no records found','no records','no records to display'})
            if pure_empty_row:continue
            if len(cells)!=len(headers):
                if normalized(tr):unparsed+=1
                continue
            if not links:
                if normalized(tr):unparsed+=1
                continue
            identities={x['case_id'] for x in links}
            if len(identities)!=1:unparsed+=1;continue
            row={**links[0],'observed_fields':{h:normalized(c) for h,c in zip(headers,cells) if h in ALLOWED_HEADERS}}
            id_text=row['observed_fields'].get('ID',row['observed_fields'].get('ID Descending',row['observed_fields'].get('ID Ascending')))
            if id_text and id_text.strip()!=row['case_id'].split(':')[1]:unparsed+=1;continue
            rows.append(row)
    # An empty indicator must be inside a recognized result table, with no ignored data rows.
    state='ROWS_VERIFIED' if rows and not unparsed else 'EXPLICIT_EMPTY' if recognized and empty and not rows and not unparsed else 'HOLD_RESULT_COUNT_UNVERIFIED'
    return {'root_safe':True,'status':state,'recognized_tables':recognized,'unparsed_record_rows':unparsed,
            'explicit_empty_indicator':empty,'projected_rows':len(rows),'actual_result_count':len(rows) if state in {'ROWS_VERIFIED','EXPLICIT_EMPTY'} else None,
            'rows':rows,'limit':'One retained page only; no filter-enforcement, primary item status, prior clearance, or Source/SOLVE qualification.'}
