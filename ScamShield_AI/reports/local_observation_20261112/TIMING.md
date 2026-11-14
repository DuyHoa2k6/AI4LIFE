# Độ trễ bộ phân tích cục bộ

Không provider, không browser/extension, không tải đồng thời; warm cùng process.

| Loại đầu vào | Ký tự | Số lượt | p50 (ms) | p95 (ms) | Giới hạn 50 event |
|---|---:|---:|---:|---:|---|
| no_rule | 100 | 30 | 0.55 | 0.83 | False |
| no_rule | 1000 | 30 | 4.85 | 5.82 | False |
| no_rule | 10000 | 30 | 46.47 | 53.40 | False |
| many_events | 100 | 30 | 1.06 | 1.29 | False |
| many_events | 1000 | 30 | 6.59 | 9.10 | True |
| many_events | 10000 | 30 | 33.04 | 37.63 | True |
