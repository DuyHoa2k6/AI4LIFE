# ScamShield AI — dữ liệu và suy luận v2

Bổ sung 13/11: [24 ca biến thể ngữ nghĩa và ca đối chứng](semantic_variants/README.md),
[nhóm mẫu runtime](semantic_phrases.json). Đây là dữ liệu development, không phải
huấn luyện mô hình hoặc tập độc lập. Nhãn kỳ vọng tách riêng khỏi input.

Bộ quyết định mặc định đã quay lại event/rulebook: dùng rulebook.json/templates.json, kèm RAG/URL. Nhánh fact ba trạng thái chỉ giữ để đối chiếu: [catalog](fact_catalog.json), [rulebook thử nghiệm](fact_rules.json), [schema fact](fact_record.schema.json), [lịch sử](../../ScamShield_AI/FACT_REASONER.md).

- [Dataset card, phạm vi và nhãn yếu](DATASET_CARD.md).
- [Schema ca chuẩn](case.schema.json) và [đầu ra backend](output.schema.json).
- [Nhãn máy đọc](labels.json), [định nghĩa/hướng quan hệ](LABEL_DICTIONARY.md).
- [Hướng dẫn gán nhãn](ANNOTATION_GUIDE.md).
- [Rulebook](rulebook.json), [đặc tả điều kiện/ngoại lệ](RULEBOOK_SPEC.md),
  [mẫu giải thích](templates.json), [luật trích an toàn](extraction_rules.json).
- [Bản pilot đang dùng](release_final/pilot.jsonl), [input riêng](release_final/inputs.json),
  [67 target phát triển](release_final/acceptance_targets.json), [manifest](manifest.json).
- [Chia tập và kế hoạch đánh giá](EVALUATION.md), [chuyển đổi dữ liệu cũ](MIGRATION.md).
- [Báo cáo chạy thật và các ca](../../ScamShield_AI/reports/local_v2_20261112/README.md).

Từ workspace gốc:

```powershell
python -m uvicorn backend.main:app --app-dir ScamShield_AI --host 127.0.0.1 --port 8000 --no-access-log
```

Mở http://127.0.0.1:8000/local để thử luồng Python → bằng chứng → rulebook → mẫu giải
thích. Hoặc vào /docs, POST /api/analyze-local. Không cần API key cho luồng này.
Không tự chuyển cấu hình website/extension cũ khỏi Gemini; đây là đường chạy cục bộ
song song để rà dữ liệu và so sánh trước khi thay dần.

Ví dụ body:

```json
{"messages":[{"id":"m1","speaker_id":"user","scope_id":"sale-1","text":"Chưa thấy tiền về, nhưng cứ giao máy trước."}]}
```

Kết quả R-HANDOVER/suspicious, quote của cả trạng thái và yêu cầu, không kết luận
biên lai giả. Với lời báo hiện đang bị giữ, safety_urgency có thể urgent dù những
trường khác unknown. Xem quote, attribution và rule IDs ở API để rà; UI không hiển
thị 18 answers/nguồn RAG/suy luận nội bộ.

Từ thư mục ứng dụng có backend:

```powershell
python validate_v2_dataset.py --output reports/v2_validation_rerun.json
python -m unittest discover -s tests -p test_local_reasoning.py -v
python evaluate_local_v2.py --output reports/v2_acceptance_rerun
python prepare_v2_training.py --output reports/v2_training_export_rerun
```

Các thư mục output đánh giá/export phải mới. Export hiện trả not_ready_no_reviewed_cases
và train/dev/test rỗng vì cả 70 ca còn weak_label. **Chưa huấn luyện mô hình riêng**;
không dùng kết quả nghiệm thu trên ca phát triển để tuyên bố accuracy 98%.
