"""Metadata-only regression controls built from retained observed URL/header roles."""
import json
from pathlib import Path
from html import escape
from parse_list_metadata import project,record_link

fixture=Path(__file__).resolve().parent/'fixtures/observed_link_roles.json'
old=json.loads(fixture.read_text())
headers=['ID Descending','Current Location and Name','Dates','Languages','Record Type','Status']
html='<table><thead><tr>'+''.join('<th>'+h+'</th>' for h in headers)+'</tr></thead><tbody>'
for row in old['rows']:
    values={**row['metadata'],'ID Descending':row['id'].split(':')[1]}
    html+='<tr>'
    for h in headers:
        value=escape(values.get(h,''))
        if h=='Current Location and Name':value='<a href="'+escape(row['actual_detail_href'],quote=True)+'">'+value+'</a>'
        html+='<td>'+value+'</td>'
    html+='</tr>'
html+='</tbody></table>'
base='https://de-crypt.org/decrypt-web/RecordsList'
checks=[]
def check(label,ok):checks.append({'label':label,'passed':bool(ok)})
got=project(html,base);check('20_old_observed_query_links_preserved',len(got['rows'])==20 and [x['case_id'] for x in got['rows']]==[x['id'] for x in old['rows']])
check('all_observed_showdetail_queries_preserved',all(x['observed_detail_URL']==y['actual_detail_href'] for x,y in zip(got['rows'],old['rows'])))
check('no_table_not_empty',project('<p>Unrelated page</p>',base)['actual_result_count'] is None)
check('empty_table_not_confirmed_empty',project('<table><th>Current Location and Name</th></table>',base)['actual_result_count'] is None)
check('unbound_ui_empty_is_unknown',project('<div class="ew-no-record">No records found</div>',base)['actual_result_count'] is None)
check('generic_alert_not_empty',project('<div class="alert alert-info">No records found</div>',base)['actual_result_count'] is None)
check('explicit_bound_ui_empty',project('<table><th>Current Location and Name</th><tr><td><div class="ew-no-record">No records found</div></td></tr></table>',base)['status']=='EXPLICIT_EMPTY')
check('invalid_host_row_not_hidden_by_empty_banner',project('<table><th>Current Location and Name</th><tr><td><a href="https://example.invalid/decrypt-web/RecordsView/123">example</a></td></tr><tr><td><div class="ew-no-record">No records found</div></td></tr></table>',base)['actual_result_count'] is None)
check('co_located_invalid_pointer_is_unknown',project('<table><th>Current Location and Name</th><tr><td><a href="https://example.invalid/decrypt-web/RecordsView/123">example</a><div class="ew-no-record">No records found</div></td></tr></table>',base)['actual_result_count'] is None)
check('co_located_nonempty_data_is_unknown',project('<table><th>Current Location and Name</th><tr><td>additional data<div class="ew-no-record">No records found</div></td></tr></table>',base)['actual_result_count'] is None)
check('unknown_link_host_rejected',record_link('https://example.invalid/decrypt-web/RecordsView/1',base) is None)
check('numeric_suffix_rejected',record_link('/decrypt-web/RecordsView/2034extra',base) is None)
check('numeric_namespace_boundary',record_link('/decrypt-web/RecordsView/203?showdetail=',base)['case_id']=='decrypt:203')
check('malformed_url_rejected',record_link('/decrypt-web/RecordsView/not-a-number',base) is None)
result={'root_safe':True,'scope':'Synthetic metadata regression controls using retained actual header/URL roles; no unknown-source payload','checks':checks,'status':'PASS' if all(x['passed'] for x in checks) else 'FAIL','historical_Source_Target':0,'network':0}
print(json.dumps(result,indent=2))
raise SystemExit(0 if result['status']=='PASS' else 1)
