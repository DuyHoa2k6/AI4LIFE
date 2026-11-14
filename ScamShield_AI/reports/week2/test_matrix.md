# Kiểm thử tuần 2

Browser: Chrome/156.0.8078.81; mode: mock.

| Ca | Kết quả | Ghi chú |
| --- | --- | --- |
| WEB-01 preview does not send | PASS |  |
| WEB-01 real API rendering | PASS |  |
| WEB Unicode codepoint highlight | PASS |  |
| WEB masked payload only | PASS |  |
| WEB stale response ignored | PASS |  |
| WEB-01 supplemental context retained | PASS |  |
| WEB ordered messages and speakers | PASS |  |
| WEB blank input rejected | PASS |  |
| WEB oversized input rejected | PASS |  |
| WEB offline error retry available | PASS |  |
| EXT real unpacked worker loaded | PASS | Installed Chrome must support unpacked extension loading in test mode |
| EXT-01 selection sends zero requests | PASS |  |
| EXT-02 correct item and separate result | PASS |  |
| PRIV-01 restricted request bodies | PASS |  |
| EXT-03 no unchanged duplicates | PASS |  |
| E2E-01 shared API behavior evidence and decision | PASS |  |
| EXT-04 old item response ignored | PASS |  |
| EXT-03 newly loaded visible item scanned | PASS |  |
| PRIV-01 after scroll still restricted | PASS |  |
| EXT-05 pause stops requests | PASS |  |
| EXT-05 stop clears session | PASS |  |
| EXT-06 SPA navigation stops scanning | PASS |  |
| EXT-06 removed region stops scanning | PASS |  |
| EXT-07 429 no infinite retries | PASS |  |
| EXT-07 offline no repeated request storm | PASS |  |
| EXT-07 timeout label | PASS | AbortError injected in real worker fetch; API timer independently tested in week1 |
| EXT-05 old session response ignored after region change | PASS |  |
| EXT-07 bounded queue and deferred items | PASS | Hàng chờ 18/20 · Mục bị hoãn: 15 |
| EXT-07 burst no duplicate requests and concurrency one | PASS |  |

Live chưa chạy. Các lỗi mạng/429/timeout được chèn tại fetch. Chỉ xác minh fixture local, chưa xác minh mạng xã hội thật.
