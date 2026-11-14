# Kiểm thử phân giải viết tắt — 12/11/2026

Áp dụng rules-1.2 / vi-abbreviations-1.0.0 cho POST /api/observe. Không thay luồng
/api/analyze, không gọi Gemini, không đo hoặc ép mức cảnh báo cuối.

Đã thêm kho **29 cách hiểu cho 23 dạng viết tắt**, kèm 29 mẫu phát triển có nhãn nháp.
Bao gồm phủ định, giao dịch/tài khoản, giấy tờ, phần mềm, chia sẻ màn hình và các
nghĩa đối chứng bình thường. Dataset gốc dev/validation/holdout giữ nguyên;
không mở validation/holdout để bổ sung luật.

## Kết quả

- **245 unittest đạt**, gồm 12 bài chuyên cho viết tắt, một bài bảng 22 ví dụ.
- **29/29 ca API** đúng tham chiếu nháp: 22 ca chọn được cách hiểu cùng hành động
  tương ứng hoặc không có hành động, 7 ca giữ mơ hồ và có câu hỏi thay vì đoán.
- Trong bộ 29 ca có **29 lần mở rộng**, **7 lần không chọn nghĩa**;
  **77/77** kiểm tra offset của bằng chứng và token viết tắt khớp bản gốc.
- **0 provider calls, 0 request mạng**. Không biến chữ đầy đủ do mở rộng thành quote gốc.
- Kiểm thử thêm URL/email/backtick/mã dài, tên Hong, Đơn A/B/K, 500k/500 k,
  tên mã KO/ID tk, không lấy ngữ cảnh từ câu/tin khác, NFD/emoji, lời trích cảnh báo,
  và hai yêu cầu liền nhau với phủ định chỉ thuộc ý trước.
- Hồi quy 30 ca cũ vẫn được chạy; số liệu mã cuối lưu trong final/regression30.

Các ca đã được dùng phát triển luật, không phải accuracy độc lập hoặc chứng minh
phân giải mọi viết tắt chính xác. Nhãn ngôn ngữ cần người rà; chưa đo chất lượng
cảnh báo downstream hay chạy lại Chrome trong lượt này vì không sửa frontend.

## Tệp bàn giao

- [Cấu trúc dataset, bảng từ và giới hạn](../../../data/README_ABBREVIATIONS.md).
- [Kho quy tắc runtime](../../../data/abbreviations_vi.json).
- [29 mẫu gán nhãn nháp](../../../data/abbreviations_examples.jsonl).
- [Kết quả từng ca](final/CASES.md), [dự đoán đầy đủ](final/predictions.json),
  [số liệu/hash](final/summary.json), [hồi quy và thời gian](final/regression30/summary.json).

final là bản cuối có bảo vệ đơn vị k tách rời và tên mã. Các kết quả ở thư mục cha
là lượt phát triển trước đó; không gộp hai lượt làm mẫu độc lập hoặc chọn số tốt hơn.

Luật dùng đúng một nghĩa khi có căn cứ ngữ cảnh; nhiều nghĩa hoặc thiếu căn cứ trả
ambiguous/unresolved. Resolved không chứng minh đó là cách hiểu duy nhất ngoài đời.
Không tự thay đại từ a/c/e/t, không đổi mọi đơn vị k/tr hoặc viết dính ck500k;
ngữ cảnh ngầm, tên riêng không đánh dấu, lỗi chính tả mới vẫn có thể sai/chưa nhận ra.

Chạy từ thư mục có backend, dùng output mới:

```powershell
python -m unittest discover -s tests -p test_abbreviations.py -v
python abbreviation_check.py --output reports/abbreviations_rerun
python local_observation_check.py --output reports/abbreviations_regression_rerun
```

Khởi động lại backend để nạp cache mới; trong /docs chọn POST /api/observe,
thử `{"text":"ko ck tiền trước gửi mk tk cho tôi"}` và xem abbreviation_resolutions,
events, negation_span cùng các evidence. Không cần API key cho endpoint này.
