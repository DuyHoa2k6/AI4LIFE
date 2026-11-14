"""Run the user's commission example through the real local API."""
import json
import argparse
import time
from pathlib import Path
from fastapi.testclient import TestClient
from backend.main import app


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', type=Path)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    text = 'Khoản hoa hồng của bạn đã được ghi nhận. Tuy nhiên, số dư đang chờ mở quyền rút. Bạn cần nộp thêm tiền bảo chứng trước thì mới nhận lại cả vốn lẫn hoa hồng.'
    if args.input:
        text = args.input.read_text(encoding='utf-8').strip()
    with TestClient(app) as client:
        start = time.perf_counter()
        response = client.post('/api/analyze', json={'text': text})
        elapsed = round((time.perf_counter() - start) * 1000, 2)
    record = {
        'input': {'text': text}, 'http_status': response.status_code,
        'elapsed_ms': elapsed, 'response': response.json(),
        'scope': 'Actual local API via ASGI TestClient; one known development case, not browser latency or independent accuracy.',
    }
    path = Path(__file__).resolve().parent / 'reports/local_pipeline_20261113/commission_test.json'
    if args.output:
        path = args.output
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(record, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
