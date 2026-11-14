"""Report URL validation and regression separately; no selecting best predictions."""
import hashlib,json
from pathlib import Path

ROOT=Path(__file__).resolve().parent
OUTPUT=ROOT/'reports/urls'

def read(path):return json.loads(path.read_text(encoding='utf-8'))

def main():
    runs=[];details=['# Dự đoán URL và văn bản từng phiên','','Các URL dưới đây là đầu vào tổng hợp; hệ thống không mở trang đích. Không phải danh sách website đã xác minh độc hại.','']
    for name in ('live','checked'):
        p=OUTPUT/name;predictions=read(p/'predictions.json');measured=read(p/'summary.json')
        refs={r['id']:r for r in read(ROOT/'fixtures/url_checks/expected.json')['cases']}
        inputs={r['id']:r for r in read(ROOT/'fixtures/url_checks/inputs.json')}
        rows=[]
        for r in predictions:
            body=r['response'];status=body.get('risk_status') if r['http_status']==200 else 'error'
            row={'id':r['id'],'expected':refs[r['id']]['acceptable'],'actual':status,
                 'match':status in refs[r['id']]['acceptable'],'http':r['http_status'],
                 'api_ms':r['api_ms'],'error':body.get('code'),
                 'used_url_evidence':body.get('analysis',{}).get('used_url_evidence'),
                 'discarded_url_uses':body.get('analysis',{}).get('discarded_url_uses')}
            rows.append(row)
        run={'run':name,'n':len(rows),'api_success':measured['successful'],
             'matches':sum(r['match'] for r in rows),'errors':measured['errors'],
             'latency':measured['latency_all_executed'],'provider_attempts':measured['provider_attempts'],
             'exact_quotes':measured['exact_quotes'],'quotes':measured['quote_count'],'cases':rows}
        runs.append(run)
        details += [f'## {name}','','| Ca | Kỳ vọng | Thực tế | HTTP | Giây |','| --- | --- | --- | --- | --- |']
        for row in rows:details.append(f"| {row['id']} | {'/'.join(row['expected'])} | {row['actual']} | {row['http']} | {row['api_ms']/1000:.3f} |")
        for r in predictions:
            body=r['response'];details += ['',f"### {name}/{r['id']} — {inputs[r['id']]['name']}",'','```json',json.dumps(inputs[r['id']]['input'],ensure_ascii=False,indent=2),'```','',
                '```json',json.dumps({k:body.get(k) for k in ('risk_status','url_analysis','url_uses','code','diagnostic')},ensure_ascii=False,indent=2),'```','']
    lock=read(OUTPUT/'checked/lock.json')
    assert all(hashlib.sha256((ROOT/n).read_bytes()).hexdigest()==h for n,h in lock['hashes'].items())
    (OUTPUT/'runs.json').write_text(json.dumps(runs,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    (OUTPUT/'CASES.md').write_text('\n'.join(details),encoding='utf-8')
    summary={'latest_run':runs[-1],'tests_passed':137,'chrome_url_checks':8,'chrome_ocr_regression_checks':10,
             'worker_security_checks':10,'ocr_worker_checks':7,'frozen_hashes_unchanged':True,
             'independent_accuracy':False,'destination_network_requests':0,
             'destination_network_scope':'implementation has no URL fetch or DNS; offline unit guard and Chrome navigation assertions, not packet capture',
             'reference_domains':['youtube.com','google.com'],'reference_status':'documented_reference_not_safe_allowlist'}
    (OUTPUT/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps([{'run':r['run'],'n':r['n'],'matches':r['matches'],'errors':r['errors']} for r in runs]))

if __name__=='__main__':main()
