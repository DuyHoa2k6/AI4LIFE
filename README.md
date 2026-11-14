# ScamShield AI

Luồng hiện hành: [TWO_PASS.md](ScamShield_AI/TWO_PASS.md). Gemini lượt đầu → kiểm chứng → hai nhánh tình huống/quy tắc và nguồn đã duyệt song song → Gemini rà lại bản gốc → backend quyết định. Cấu hình riêng đã chọn two_pass; key/model giữ ở backend. Nguồn vẫn candidate nên có trạng thái fallback, chưa nghiệm thu P0/RAG. [Cách chạy Gemini](ScamShield_AI/README_GEMINI.md), [kết quả thực](ScamShield_AI/reports/two_pass/README.md). Hybrid một lượt là chế độ đối chứng cũ.

Mock hành vi hiện tại: [MOCK_RULES.md](ScamShield_AI/MOCK_RULES.md). Quy tắc có phiên bản và bằng chứng theo đoạn; đây là mock kiểm thử, không phải AI live.

Backend tuần 1 đã có tại [ScamShield_AI/README_TUAN_1.md](ScamShield_AI/README_TUAN_1.md): hướng dẫn chạy API mock/live, kiểm thử, fixture và báo cáo thực tế. Gói đánh giá tuần 3 trước đó vẫn được giữ trong cùng thư mục.

Website và extension tuần 2: [hướng dẫn chạy và cài đặt](ScamShield_AI/README_TUAN_2.md). Chạy `python -m uvicorn backend.main:app --app-dir ScamShield_AI --host 127.0.0.1 --port 8000 --no-access-log`, mở http://127.0.0.1:8000/. Extension unpacked ở `ScamShield_AI/extension`.

Bộ đặc tả cho AI triển khai một bản demo trong ba tuần. Bắt đầu với dữ liệu và bộ phân tích hành vi, sau đó nối web và extension rồi đánh giá. Đây là tài liệu triển khai và dữ liệu khởi tạo.

| Đọc theo thứ tự | Mục đích |
| --- | --- |
| [01 Ý tưởng và phạm vi](01_Y_Tuong.md) | Hiểu mục tiêu, người dùng, tiêu chí bàn giao |
| [02 Công cụ và kiến trúc](02_Cong_Cu.md) | Chọn công nghệ, bố trí mã nguồn, cấu hình |
| [03 Luồng nghiệp vụ](03_Luong.md) | Hiểu bước xử lý và các nhánh ngoại lệ |
| [04 Hợp đồng API](04_API.md) | Thống nhất dữ liệu giữa mô hình, backend và giao diện |
| [05 Dataset và kho tri thức](05_Dataset.md) | Đọc JSONL, gán nhãn và tách tập |
| [06 Kiểm thử và hiệu năng](06_Kiem_Thu.md) | Đo chất lượng, độ trễ và lỗi |
| [07 Lộ trình ba tuần](07_Lo_Trinh.md) | Xác định cổng nghiệm thu từng tuần |
| [08 Quyền riêng tư và mở rộng](08_Mo_Rong.md) | Thiết kế OCR, URL, media và cộng đồng theo giai đoạn |
| [Prompt triển khai](prompts/00_Bat_Dau.md) | Giao việc cho AI theo từng tuần |

Dùng [dev.jsonl](data/dev.jsonl) khi phát triển, [validation.jsonl](data/validation.jsonl) khi chọn cấu hình và [holdout.jsonl](data/holdout.jsonl) khi đánh giá cuối. Khi giao cho AI triển khai, giữ holdout ngoài workspace của AI cho đến lúc đánh giá. [knowledge_seed.jsonl](data/knowledge_seed.jsonl) là nội dung ứng viên cho kho tri thức.

Thứ tự ưu tiên khi có khác biệt giữa tài liệu là yêu cầu mới nhất của Hòa, phạm vi tại 01, hợp đồng tại 04, tiêu chí đánh giá tại 06, rồi các tài liệu còn lại. Các file tuần là prompt giao việc. Chúng không thay đổi hợp đồng API.
