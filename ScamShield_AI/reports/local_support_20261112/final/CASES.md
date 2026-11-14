# Local text + RAG + URL: development examples

TestClient end-to-end API. No external model; redirects and approved sources explicitly simulated where noted.
Not independent quality, browser latency, real source approval or real-domain reputation.

| Case | Input | Risk | Used sources | Used URLs | Support fixture |
|---|---|---|---:|---:|---|
| url_request | Đăng nhập tại https://youtubee.com/ | suspicious | 0 | 1 | none; actual production index; URL network disabled |
| url_warning | Cảnh báo: đừng đăng nhập tại https://youtubee.com/ | clear | 0 | 0 | none; actual production index; URL network disabled |
| url_only | https://youtubee.com/ | need_context | 0 | 0 | none; actual production index; URL network disabled |
| ordinary_domain | Đăng nhập tại https://youtube.com/ | need_context | 0 | 0 | none; actual production index; URL network disabled |
| high_text | Gửi mã OTP cho tôi tại https://youtubee.com/ | high | 0 | 1 | none; actual production index; URL network disabled |
| separate_context | Đăng nhập tại đây. Ví dụ tên miền: https://youtubee.com/ | need_context | 0 | 0 | none; actual production index; URL network disabled |
| urgent | Hiện tại tôi bị giữ lại và không được rời đi. | high | 0 | 0 | none; actual production index; URL network disabled |
| approved_fixture | Gửi mã OTP cho tôi. | high | 1 | 0 | synthetic approved record; NOT a real approved source |
| candidate_fixture | Gửi mã OTP cho tôi. | high | 0 | 0 | synthetic candidate record |
| redirect_fixture | Đăng nhập tại https://example.com/ | suspicious | 0 | 1 | synthetic redirect observation; no website contacted |
