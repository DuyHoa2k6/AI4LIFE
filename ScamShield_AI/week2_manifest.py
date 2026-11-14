"""Package metadata only; never read datasets or personal browser profiles."""
import hashlib
import json
from pathlib import Path

root = Path(__file__).resolve().parent
files = [*sorted((root/'web').glob('*')), *sorted((root/'extension').glob('*')),
         *[p for p in sorted((root/'backend').glob('*.py')) if p.name != 'local_settings.py'], root/'README_TUAN_2.md', root/'chay_he_thong.cmd',
         root/'tests/browser_week2.mjs', root/'tests/worker_security.mjs', root/'tests/test_week2_routes.py']
report = {'release': 'week2-local-0.2.0', 'schema': '04_API 1.0',
          'live_provider': 'not configured; not assessed',
          'files_sha256': {str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest() for p in files if p.is_file()}}
destination = root/'reports/week2'
destination.mkdir(parents=True, exist_ok=True)
(destination/'manifest.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
browser = json.loads((destination/'browser.json').read_text(encoding='utf-8'))
lines = ['# Kiểm thử tuần 2', '', f"Browser: {browser.get('browser_version', 'unknown')}; mode: mock.", '',
         '| Ca | Kết quả | Ghi chú |', '| --- | --- | --- |']
for row in browser['checks']:
    lines.append(f"| {row['id']} | {'PASS' if row['passed'] else 'FAIL'} | {row.get('detail', '')} |")
if browser.get('error'):
    lines += ['', 'Lượt chạy chưa hoàn tất: ' + browser['error'].splitlines()[0]]
lines += ['', 'Live chưa chạy. Các lỗi mạng/429/timeout được chèn tại fetch. Chỉ xác minh fixture local, chưa xác minh mạng xã hội thật.']
(destination/'test_matrix.md').write_text('\n'.join(lines)+'\n', encoding='utf-8')
print('Wrote week2 manifest and test matrix')
