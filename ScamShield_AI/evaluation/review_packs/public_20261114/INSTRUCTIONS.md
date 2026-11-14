# Gói rà soát đầu vào

Chỉ có nội dung gốc và định nghĩa schema; không có nhãn draft hoặc dự đoán của model.
Family/template/source group bị loại vì một số ID cũ chứa tên mức cảnh báo.
Đây vẫn là dữ liệu công khai đã được agent xem, không phải blind holdout.

Mỗi người rà nhận bản sao gói này, tự sao chép annotations_blank.jsonl sang file
riêng rồi điền expected và độ hoàn thiện từng task. Không sửa inputs.jsonl hoặc
file gốc trong pack. Không xem kết quả của người rà kia trong lượt độc lập.

Đọc evaluation/annotation_guide.md. Offset là Unicode code point, end loại trừ.
Chưa gán nhãn khác với không có hành vi. Không đoán danh tính hoặc tội danh.
Reference người rà nên là mã công việc không nhận dạng cá nhân, không cần tên thật.

CLI submit cần attestation có reviewer_reference thực, human_review_performed=true,
independent_of_other_reviewer=true, used_model_generated_annotations=false. Phần mềm
chỉ ghi nhận lời xác nhận, không thể tự chứng minh con người đã rà độc lập.

Hai bản gán nhãn chỉ tạo báo cáo đồng thuận/bất đồng. Chúng không tự được đưa vào
train. Người chịu trách nhiệm phải lập resolution, ghi lý do, xác nhận đã rà và
chọn approved_for_training. Split, family và label mapping vẫn qua training gate.
