# Sửa năm nhóm lỗi ngữ nghĩa — 13/11/2026

Đã sửa và kiểm thử riêng dữ kiện, quan hệ, vai, câu hỏi và mức cảnh báo.
Chưa coi việc khớp mức là đủ nghiệm thu. Không API mô hình/bitmask/huấn luyện.
Mô tả module và cách chạy: [GROUNDING_V2.md](../../GROUNDING_V2.md).

## Trước/sau trên cùng 24 input

Đầu vào `fixtures/grounding_v2_inputs.json` gồm các cặp tối thiểu và ví dụ
người dùng vừa thử. Mỗi ca 3 lượt, payload chỉ text, không gửi nhãn.

| Chỉ số development | Trước | Sau |
|---|---:|---:|
| Khớp mức kỳ vọng (một số ca cho phép khoảng mức có chú giải) | 20/24 | 24/24 |
| Đạt tất cả check ngữ nghĩa gán cho ca | 10/24 | 24/24 |
| Đúng mức nhưng sai ít nhất một check dữ kiện/quan hệ/câu hỏi | 10 ca | 0 ca |
| Đối tượng | 2/10 check | 10/10 check |
| Phạm vi lời nói/phủ định | 6/10 | 10/10 |
| Quan hệ điều kiện/xác minh | 2/5 | 5/5 |
| Người và lần nhắc | 0/4 | 4/4 |
| Giao dịch | 3/4 | 4/4 |
| Câu hỏi | 0/3 | 3/3 |

Đây là **chú giải sparse** theo tiêu chí đã gán, không chấm toàn bộ mọi từ,
sự kiện hoặc 18 trường; 0 ca sai theo check không có nghĩa không còn lỗi.

[Bảng trước](before/CASES.md) · [Bảng sau](release/CASES.md) ·
[Chi tiết từng check](release/semantic_review.json) ·
[Dự đoán/sự kiện/quan hệ sau](release/predictions.json).

## Ví dụ và nguyên nhân gốc

| Nhóm | Nguyên nhân thực tế | Sửa và caller chịu tác động |
|---|---|---|
| Đối tượng | Context tài chính trong cả câu làm “nhận phụ lục” thành receive_funds; “ứng dụng” bị đọc thành ứng tiền; “hướng dẫn đăng nhập” thành login | Guard ngay observer; hòa giải cuối; đổi về action tài liệu/generic; adapter/18 trường không còn dùng dữ kiện sai |
| Phủ định | Bộ dò từ phủ định trong cửa sổ làm “dụng” thành “đừng”, gộp nếu không…thì… thành denial và lan sang mệnh đề khác | Phạm vi riêng, đối chiếu bản gốc, negative antecedent và consequence riêng; ghi actor được thuật lại |
| Giao dịch | Mã A nằm sau động từ nên trạng thái bị gán trước khi thấy A; B làm tình huống chung không rõ | Gán mã trong đối tượng; resource owner đúng scope; nối paid(A) → handover(A), hold(B); không hỏi tiền A lần nữa |
| Người | Placeholder unknown bị dùng như cùng người; view clause_roles còn sao chép placeholder dù sự kiện đã đổi | Mention riêng, candidate/unique antecedent; gán lại sự kiện, frames và view bằng người/vai hợp lệ trước quyết định |
| Câu hỏi | Câu hỏi rút tiền được chọn chỉ vì có hành động chuyển; các view cũ giữ text sau khi dữ kiện bị sửa | Field-needs theo scope; câu hỏi trung lập theo trường thiếu; project lại view và loại frame/quan hệ không còn căn cứ |

Ví dụ đã chạy:

```text
Đã nhận đủ tiền của đơn A → receive_funds(A, claim, completed)
Giao đúng đơn A           → handover_asset(A, request)
Đơn B chưa trả, giữ lại   → payment(B, negative/pending) + hold_asset(B)
→ before(receipt A, handover A), không dùng B cho A
→ clear theo nội dung được báo, không xác minh ngân hàng ngoài đời
```

```text
Nếu không nộp hôm nay thì mất khoản cũ
→ payment(negative, conditional antecedent)
→ loss_consequence(hypothetical, claimed/reported)
→ threatens_unless với bằng chứng đúng hai đầu
→ không đổi cả câu thành lời ngăn nộp
```

Sự kiện giả receive_funds từ phụ lục, payment từ “ứng dụng”, login từ hướng
dẫn, quan hệ thanh toán giả và bản sao cùng hành động đã được loại trên các
ca gán nhãn. Dữ kiện khác có thể vẫn đúng nên mức high cũ được giữ khi đủ căn
cứ, không lấy nhãn đúng để che lỗi ở tầng trích.

## Kiểm thử hồi quy và trạng thái lỗi

- 273 kiểm thử Python qua, gồm unit từng tầng, integration API, phiên bổ sung,
  hai hội thoại đồng thời, bỏ tham chiếu sai và fault injection.
- 10 ca high người dùng: 10/10 vẫn high; 30/30 action và 16/16 method quan hệ
  bắt buộc theo chú giải sparse được tìm thấy, không lỗi cấu trúc.
- Các bộ cũ: 31/31 và 24/24 khớp mức; 42/42 đối chứng thỏa tiêu chí high/not_high.
  Các bộ này chia sẻ họ/cấu trúc, không cộng như mẫu độc lập.
- Bài 31 vẫn còn một required event ngoài phần chấm mức chưa trích (20/21);
  không coi khớp mức là hiểu hết.
- Công cụ tầng observer đã được cập nhật để dùng bản đính chính F và chạy
  thật: 30/30 ca, 40/40 sự kiện theo chú giải draft và 134/134 quote khớp. Đây
  là tầng đầu, không phải chất lượng cảnh báo cuối hoặc nhãn chuyên gia.
- Module cố ý lỗi → 503, không trả mức an toàn. Cố ý làm mất dữ kiện nhận tiền
  tường minh → partial, không hỏi lại người dùng; có credential request độc
  lập thì vẫn high/partial. Ngoài độ phủ → unsupported, không tự clear.
- Khi chạm giới hạn số sự kiện/cụm, trả partial và nêu giới hạn BE, không
  trả complete hoặc yêu cầu người dùng cung cấp lại thông tin đã gửi.
- Lần đầu 7/8 regression mới thất bại trước sửa. Các snapshot before vẫn giữ.

Đính chính nhãn yếu cũ: ca observer F và test chia đoạn từng mặc định “Đơn B
đã nhận đủ” là nhận tiền dù tiền chỉ được nêu ở đơn A. Giữ nguyên file nhãn cũ,
thêm `fixtures/local_observation/expected_grounding_overrides.json` và sửa
assert không suy tiền từ giao dịch A sang B. Đây là sửa giả định ngữ nghĩa
theo yêu cầu, không đổi nhãn mức để che báo nhầm. Không sửa dev/holdout gốc.

## Tập cách nói mới chưa dùng để sửa nhận diện

[8 ca và kết quả](unseen_release/CASES.md), [check chi tiết](unseen_release/semantic_review.json).
Cùng người biên soạn, tổng hợp, không phải tập độc lập hoặc nhãn chuyên gia.
Không dùng các cách nói này mở rộng pattern sau khi đo.

- 6/8 đạt check dữ kiện; 7/8 khớp mức tham khảo.
- U01 “Phụ lục hợp đồng mới tôi vẫn chưa nhận được.”: đảo đối tượng lên đầu,
  chưa tạo receive_document; trả need_context/unsupported, không giả nhận tiền.
- U02 “Tôi sẽ gửi bản hướng dẫn đăng nhập.”: không còn nhầm login/credentials,
  nhưng mới giữ send_unknown, chưa hiểu cụm danh từ “bản hướng dẫn”. Vẫn complete
  dù thiếu object đúng — coverage sentinel chưa bắt hết loại thiếu hiểu này.
- U03 phủ định phối hợp tiền và mã: không có yêu cầu nguy hiểm có hiệu lực,
  nhưng trả need_context thay vì clear do phạm vi còn bảo thủ.
- Trong tập này còn **2 ca mức được chấp nhận nhưng sai check đối tượng**.
  Chưa đánh dấu các cấu trúc này đã giải quyết. Không âm thầm chỉnh theo chúng
  rồi công bố như holdout đạt chuẩn.

## Độ trễ trước/sau

Cùng 24 văn bản, local_rules/legacy/context=1/graph=1, URL network tắt,
ASGI TestClient, 72 request mỗi phiên. Có hash Python/input trong summary.

| Phiên | p50 | p95 nearest-rank |
|---|---:|---:|
| Trước | 16,598 ms | 35,162 ms |
| Sau (release) | 11,078 ms | 43,084 ms |

Median thấp hơn nhưng p95 tăng trong lần đo; không tuyên bố tăng tốc mọi ca.
Mẫu nhỏ, chưa kiểm soát cold start/tải đồng thời hoặc thời gian browser.
0 lỗi HTTP, 0 HTTP bên ngoài trong hai phiên. Báo cáo mới đo backend văn bản,
không chứng minh chất lượng OCR, RAG nguồn thật, redirect hoặc dữ liệu người thật.

Phép đo riêng tầng observer còn thử 100/1.000/10.000 ký tự, 30 lượt/mức.
Đầu vào 10.000 ký tự nhiều hành động có p50 khoảng 953 ms, p95 1.005 ms và
chạm giới hạn 50 hành động. Không suy từ số đo câu ngắn rằng văn bản dài cũng
có cùng độ trễ hoặc đã được đọc đầy đủ. Xem [timing tầng đầu](observer30/summary.json).

Hash các snapshot nằm trong summary tương ứng; [lock.json](lock.json) chốt
45 file mã/config/fixture công khai tại bàn giao, không chứa local_settings
hoặc khóa. Một số bổ sung cuối về provenance và trạng thái giới hạn được kiểm
tra riêng bằng unit/API; không diễn giải thời gian đo như bảo đảm hiệu năng
của mọi đường chạy.

## Chạy lại và file chính

```powershell
python -m unittest discover -s tests -q
python check_grounding.py --output reports/grounding_new
python score_grounding.py reports/grounding_new
python check_grounding.py --inputs fixtures/grounding_v2_untuned_inputs.json --output reports/grounding_unseen_new
python score_grounding.py reports/grounding_unseen_new
```

Thư mục đầu ra phải chưa tồn tại. Script lưu dự đoán trước khi chấm; không
đưa nhãn vào API. Các file backend chính: syntax.py, analyzer.py, extract.py,
grounding.py, schema.py, validation.py, legacy_engine.py, clause_context.py.
Giữ API công khai, thêm schema raw backward-compatible và xuất lại JSON schema.
Chưa chạy lại Chrome E2E. Các parser vẫn theo quy tắc hữu hạn, không đảm bảo
hiểu mọi cấu trúc đảo câu, lược đối tượng hoặc đại từ. Không có bằng chứng đạt
98% độc lập; không mô tả quy tắc như mô hình đã huấn luyện.
