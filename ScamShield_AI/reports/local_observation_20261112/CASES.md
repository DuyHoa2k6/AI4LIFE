# Đầu ra 30 ca phân tích đầu tiên

Chỉ Python rules, không Gemini/RAG/URL và không mức rủi ro cuối. Nhãn nháp phát triển, không đánh giá độc lập.

## Ca A

```json
{
  "text": "Chưa thấy tiền về, nhưng cứ giao máy trước."
}
```

| Event | Hành động | Cụm động từ | Phủ định | Vai | Trạng thái | Phạm vi |
|---|---|---|---|---|---|---|
| a1 | receive_funds | thấy (m1:5–9) | negative | claim | pending | chưa có mã |
| a2 | handover_asset | giao (m1:28–32) | positive | request | requested | chưa có mã |

Quan hệ:
- before: a2 → a1; observed; luật REL-HANDOVER-BEFORE-CONFIRMATION. Thứ tự được yêu cầu; không chứng minh biên lai giả.

Câu hỏi bổ sung:
- Không có câu hỏi theo bộ luật hiện tại.

Trường unknown: sender_identity, relationship, communication_channel, stated_purpose, benefit_and_mismatch, persuasion, technical_checks, missing_information.

## Ca B

```json
{
  "text": "Tôi đã kiểm tra và nhận đủ tiền. Anh giao máy cho tài xế nhé."
}
```

| Event | Hành động | Cụm động từ | Phủ định | Vai | Trạng thái | Phạm vi |
|---|---|---|---|---|---|---|
| a1 | receive_funds | nhận (m1:19–23) | positive | claim | completed | chưa có mã |
| a2 | handover_asset | giao (m1:37–41) | positive | request | requested | chưa có mã |

Quan hệ:
- before: a1 → a2; inferred; luật REL-REPORTED-PAYMENT-FIRST. Hai câu liền nhau có cùng mã giao dịch hoặc chưa nêu mã khác; cần rà nếu có nhiều giao dịch ngầm.

Câu hỏi bổ sung:
- Không có câu hỏi theo bộ luật hiện tại.

Trường unknown: sender_identity, relationship, communication_channel, stated_purpose, benefit_and_mismatch, persuasion, contradictions_and_alternatives, technical_checks, missing_information.

## Ca C

```json
{
  "text": "Nếu chưa nhận tiền thì đừng giao máy."
}
```

| Event | Hành động | Cụm động từ | Phủ định | Vai | Trạng thái | Phạm vi |
|---|---|---|---|---|---|---|
| a1 | receive_funds | nhận (m1:9–13) | negative | claim | hypothetical | chưa có mã |
| a2 | handover_asset | giao (m1:28–32) | negative | request | hypothetical | chưa có mã |

Quan hệ:
- prerequisite_for: a1 → a2; observed; luật REL-NEGATIVE-CONDITION. Điều kiện ngăn giao hàng; không phải yêu cầu giao trước khi trả.

Câu hỏi bổ sung:
- Không có câu hỏi theo bộ luật hiện tại.

Trường unknown: sender_identity, relationship, communication_channel, requested_actions, stated_purpose, benefit_and_mismatch, persuasion, technical_checks, missing_information.

## Ca D

```json
{
  "text": "Tôi cảnh báo mọi người đừng nghe câu ‘cứ giao máy trước’."
}
```

| Event | Hành động | Cụm động từ | Phủ định | Vai | Trạng thái | Phạm vi |
|---|---|---|---|---|---|---|
| a1 | handover_asset | giao (m1:41–45) | positive | quoted_warning | unknown | chưa có mã |

Quan hệ:
- warning_about: p1 → a1; observed; luật REL-QUOTED-WARNING. Speaker là người thuật lại/cảnh báo, không phải người ra lệnh trong trích dẫn.

Câu hỏi bổ sung:
- Không có câu hỏi theo bộ luật hiện tại.

Trường unknown: sender_identity, relationship, communication_channel, claims, requested_actions, stated_purpose, benefit_and_mismatch, persuasion, technical_checks, missing_information.

## Ca E

```json
{
  "text": "Hôm qua chưa nhận tiền. Hôm nay tôi đã kiểm tra và nhận đủ."
}
```

| Event | Hành động | Cụm động từ | Phủ định | Vai | Trạng thái | Phạm vi |
|---|---|---|---|---|---|---|
| a1 | receive_funds | nhận (m1:13–17) | negative | claim | pending | chưa có mã |
| a2 | receive_funds | nhận (m1:51–55) | positive | claim | completed | chưa có mã |

Quan hệ:
- state_update: a1 → a2; observed; luật REL-TIMED-UPDATE. Chỉ là trạng thái do văn bản báo, không xác minh ngân hàng.

Câu hỏi bổ sung:
- Không có câu hỏi theo bộ luật hiện tại.

Trường unknown: sender_identity, relationship, communication_channel, requested_actions, stated_purpose, benefit_and_mismatch, persuasion, technical_checks, missing_information.

## Ca F

```json
{
  "text": "Đơn A chưa thanh toán. Đơn B đã nhận đủ, giao đơn B nhé."
}
```

| Event | Hành động | Cụm động từ | Phủ định | Vai | Trạng thái | Phạm vi |
|---|---|---|---|---|---|---|
| a1 | transfer_funds | thanh toán (m1:11–21) | negative | claim | pending | don a |
| a2 | receive_funds | nhận (m1:32–36) | positive | claim | completed | don b |
| a3 | handover_asset | giao (m1:41–45) | positive | request | requested | don b |

Quan hệ:
- before: a2 → a3; observed; luật REL-REPORTED-PAYMENT-FIRST. Trạng thái nhận tiền là lời tự báo.

Câu hỏi bổ sung:
- Không có câu hỏi theo bộ luật hiện tại.

Trường unknown: sender_identity, relationship, communication_channel, stated_purpose, benefit_and_mismatch, persuasion, technical_checks, missing_information.

## Ca G

```json
{
  "text": "Đọc sáu số vừa hiện để nhận tiền."
}
```

| Event | Hành động | Cụm động từ | Phủ định | Vai | Trạng thái | Phạm vi |
|---|---|---|---|---|---|---|
| a1 | provide_code | Đọc (m1:0–3) | positive | request | requested | chưa có mã |
| a2 | receive_funds | nhận (m1:23–27) | positive | claim | unknown | chưa có mã |

Quan hệ:
- prerequisite_for: a1 → a2; observed; luật REL-EXPLICIT-PURPOSE. 
- reason_given_for: a2 → a1; observed; luật REL-STATED-REASON. 

Câu hỏi bổ sung:
- Dãy số được thông báo dùng để làm gì? Chỉ mô tả loại mã, không gửi mã thật.

Trường unknown: sender_identity, relationship, communication_channel, benefit_and_mismatch, persuasion, contradictions_and_alternatives, technical_checks, missing_information.

## Ca H

```json
{
  "messages": [
    {
      "id": "m1",
      "speaker": "Người gửi",
      "text": "Đọc sáu số vừa hiện để nhận tiền."
    },
    {
      "id": "m2",
      "speaker": "Người nhận",
      "text": "Đó là mã đăng nhập."
    }
  ]
}
```

| Event | Hành động | Cụm động từ | Phủ định | Vai | Trạng thái | Phạm vi |
|---|---|---|---|---|---|---|
| a1 | provide_code | Đọc (m1:0–3) | positive | request | requested | chưa có mã |
| a2 | receive_funds | nhận (m1:23–27) | positive | claim | unknown | chưa có mã |
| a3 | code_identity | Đó là mã đăng nhập (m2:0–18) | positive | claim | unknown | chưa có mã |

Quan hệ:
- prerequisite_for: a1 → a2; observed; luật REL-EXPLICIT-PURPOSE. 
- reason_given_for: a2 → a1; observed; luật REL-STATED-REASON. 
- state_update: a1 → a3; inferred; luật REL-EXPLICIT-CODE-REPLY. Liên kết theo hội thoại gửi lại trong cùng request, không lưu/ghép phiên ngầm.

Câu hỏi bổ sung:
- Không có câu hỏi theo bộ luật hiện tại.

Trường unknown: sender_identity, relationship, communication_channel, benefit_and_mismatch, persuasion, technical_checks, missing_information.

## Ca I

```json
{
  "text": "Anh là người quen của em."
}
```

| Event | Hành động | Cụm động từ | Phủ định | Vai | Trạng thái | Phạm vi |
|---|---|---|---|---|---|---|
| a1 | relationship_claim | là người quen (m1:4–17) | positive | claim | unknown | chưa có mã |

Quan hệ:
- Không có quan hệ được trích.

Câu hỏi bổ sung:
- Không có câu hỏi theo bộ luật hiện tại.

Trường unknown: sender_identity, communication_channel, requested_actions, stated_purpose, assets_and_access, benefit_and_mismatch, persuasion, conditions_and_sequence, contradictions_and_alternatives, technical_checks, missing_information.

## Ca J

```json
{
  "text": "😀 Chuyển 500.000 đồng. Mở https://example.invalid/a?x=1. Cảnh báo “họ nhắn ‘gửi OTP’”. Chuyển 500.000 đồng."
}
```

| Event | Hành động | Cụm động từ | Phủ định | Vai | Trạng thái | Phạm vi |
|---|---|---|---|---|---|---|
| a1 | transfer_funds | Chuyển (m1:2–8) | positive | request | requested | chưa có mã |
| a2 | open_link | Mở (m1:23–25) | positive | request | requested | chưa có mã |
| a3 | provide_code | gửi (m1:76–79) | positive | quoted_warning | unknown | chưa có mã |
| a4 | transfer_funds | Chuyển (m1:87–93) | positive | request | requested | chưa có mã |

Quan hệ:
- warning_about: p1 → a3; observed; luật REL-QUOTED-WARNING. Speaker là người thuật lại/cảnh báo, không phải người ra lệnh trong trích dẫn.

Câu hỏi bổ sung:
- Khoản tiền được yêu cầu dùng để thanh toán việc gì?

Trường unknown: sender_identity, relationship, communication_channel, claims, stated_purpose, benefit_and_mismatch, persuasion, technical_checks, missing_information.

## Ca K

```json
{
  "text": "Tài xế đang chờ."
}
```

| Event | Hành động | Cụm động từ | Phủ định | Vai | Trạng thái | Phạm vi |
|---|---|---|---|---|---|---|

Không trích được hành vi thuộc mẫu; không tự coi là an toàn.

Quan hệ:
- Không có quan hệ được trích.

Câu hỏi bổ sung:
- Người gửi có yêu cầu bạn thực hiện thao tác cụ thể nào không? Hãy cung cấp đoạn liên quan đã che bí mật.

Trường unknown: situation, sender_identity, relationship, communication_channel, claims, requested_actions, action_targets, stated_purpose, assets_and_access, benefit_and_mismatch, persuasion, conditions_and_sequence, contradictions_and_alternatives, technical_checks, evidence_quality, missing_information, assessment.

## Ca L

```json
{
  "text": "Mưa rơi trên mái hiên."
}
```

| Event | Hành động | Cụm động từ | Phủ định | Vai | Trạng thái | Phạm vi |
|---|---|---|---|---|---|---|

Không trích được hành vi thuộc mẫu; không tự coi là an toàn.

Quan hệ:
- Không có quan hệ được trích.

Câu hỏi bổ sung:
- Người gửi có yêu cầu bạn thực hiện thao tác cụ thể nào không? Hãy cung cấp đoạn liên quan đã che bí mật.

Trường unknown: situation, sender_identity, relationship, communication_channel, claims, requested_actions, action_targets, stated_purpose, assets_and_access, benefit_and_mismatch, persuasion, conditions_and_sequence, contradictions_and_alternatives, technical_checks, evidence_quality, missing_information, assessment.

## Ca NEGATION

```json
{
  "text": "Đừng chuyển tiền."
}
```

| Event | Hành động | Cụm động từ | Phủ định | Vai | Trạng thái | Phạm vi |
|---|---|---|---|---|---|---|
| a1 | transfer_funds | chuyển (m1:5–11) | negative | request | requested | chưa có mã |

Quan hệ:
- Không có quan hệ được trích.

Câu hỏi bổ sung:
- Khoản tiền được yêu cầu dùng để thanh toán việc gì?

Trường unknown: sender_identity, relationship, communication_channel, claims, requested_actions, stated_purpose, benefit_and_mismatch, persuasion, conditions_and_sequence, technical_checks, missing_information.

## Ca COMPLETED

```json
{
  "text": "Tôi đã chuyển tiền."
}
```

| Event | Hành động | Cụm động từ | Phủ định | Vai | Trạng thái | Phạm vi |
|---|---|---|---|---|---|---|
| a1 | transfer_funds | chuyển (m1:7–13) | positive | claim | completed | chưa có mã |

Quan hệ:
- Không có quan hệ được trích.

Câu hỏi bổ sung:
- Không có câu hỏi theo bộ luật hiện tại.

Trường unknown: sender_identity, relationship, communication_channel, requested_actions, stated_purpose, benefit_and_mismatch, persuasion, conditions_and_sequence, contradictions_and_alternatives, technical_checks, missing_information.

## Ca NOT_YET

```json
{
  "text": "Tôi chưa chuyển tiền."
}
```

| Event | Hành động | Cụm động từ | Phủ định | Vai | Trạng thái | Phạm vi |
|---|---|---|---|---|---|---|
| a1 | transfer_funds | chuyển (m1:9–15) | negative | claim | pending | chưa có mã |

Quan hệ:
- Không có quan hệ được trích.

Câu hỏi bổ sung:
- Không có câu hỏi theo bộ luật hiện tại.

Trường unknown: sender_identity, relationship, communication_channel, requested_actions, stated_purpose, benefit_and_mismatch, persuasion, conditions_and_sequence, technical_checks, missing_information.

## Ca NO_NEED

```json
{
  "text": "Không cần chuyển tiền."
}
```

| Event | Hành động | Cụm động từ | Phủ định | Vai | Trạng thái | Phạm vi |
|---|---|---|---|---|---|---|
| a1 | transfer_funds | chuyển (m1:10–16) | negative | request | requested | chưa có mã |

Quan hệ:
- Không có quan hệ được trích.

Câu hỏi bổ sung:
- Khoản tiền được yêu cầu dùng để thanh toán việc gì?

Trường unknown: sender_identity, relationship, communication_channel, claims, requested_actions, stated_purpose, benefit_and_mismatch, persuasion, conditions_and_sequence, technical_checks, missing_information.

## Ca PENDING

```json
{
  "text": "Chưa được rút tiền."
}
```

| Event | Hành động | Cụm động từ | Phủ định | Vai | Trạng thái | Phạm vi |
|---|---|---|---|---|---|---|
| a1 | withdraw_funds | rút (m1:10–13) | negative | claim | pending | chưa có mã |

Quan hệ:
- Không có quan hệ được trích.

Câu hỏi bổ sung:
- Để tiếp tục rút tiền, họ có yêu cầu chuyển tiền hoặc cung cấp thông tin gì không?

Trường unknown: sender_identity, relationship, communication_channel, requested_actions, stated_purpose, benefit_and_mismatch, persuasion, conditions_and_sequence, technical_checks, missing_information.

## Ca MONEY

```json
{
  "text": "Ứng 500 nghìn để rút số dư."
}
```

| Event | Hành động | Cụm động từ | Phủ định | Vai | Trạng thái | Phạm vi |
|---|---|---|---|---|---|---|
| a1 | transfer_funds | Ứng (m1:0–3) | positive | request | requested | chưa có mã |
| a2 | withdraw_funds | rút (m1:17–20) | positive | claim | unknown | chưa có mã |

Quan hệ:
- prerequisite_for: a1 → a2; observed; luật REL-EXPLICIT-PURPOSE. 
- reason_given_for: a2 → a1; observed; luật REL-STATED-REASON. 

Câu hỏi bổ sung:
- Không có câu hỏi theo bộ luật hiện tại.

Trường unknown: sender_identity, relationship, communication_channel, benefit_and_mismatch, persuasion, contradictions_and_alternatives, technical_checks, missing_information.

## Ca PASSWORD

```json
{
  "text": "Gửi mật khẩu cho tôi."
}
```

| Event | Hành động | Cụm động từ | Phủ định | Vai | Trạng thái | Phạm vi |
|---|---|---|---|---|---|---|
| a1 | provide_credentials | Gửi (m1:0–3) | positive | request | requested | chưa có mã |

Quan hệ:
- Không có quan hệ được trích.

Câu hỏi bổ sung:
- Không có câu hỏi theo bộ luật hiện tại.

Trường unknown: sender_identity, relationship, communication_channel, claims, stated_purpose, benefit_and_mismatch, persuasion, conditions_and_sequence, contradictions_and_alternatives, technical_checks, missing_information.

## Ca DOCUMENTS

```json
{
  "text": "Gửi ảnh hai mặt căn cước qua chat."
}
```

| Event | Hành động | Cụm động từ | Phủ định | Vai | Trạng thái | Phạm vi |
|---|---|---|---|---|---|---|
| a1 | provide_documents | Gửi (m1:0–3) | positive | request | requested | chưa có mã |

Quan hệ:
- Không có quan hệ được trích.

Câu hỏi bổ sung:
- Không có câu hỏi theo bộ luật hiện tại.

Trường unknown: sender_identity, relationship, communication_channel, claims, stated_purpose, benefit_and_mismatch, persuasion, conditions_and_sequence, contradictions_and_alternatives, technical_checks, missing_information.

## Ca INSTALL

```json
{
  "text": "Cài ứng dụng tôi gửi."
}
```

| Event | Hành động | Cụm động từ | Phủ định | Vai | Trạng thái | Phạm vi |
|---|---|---|---|---|---|---|
| a1 | install_app | Cài (m1:0–3) | positive | request | requested | chưa có mã |

Quan hệ:
- Không có quan hệ được trích.

Câu hỏi bổ sung:
- Không có câu hỏi theo bộ luật hiện tại.

Trường unknown: sender_identity, relationship, communication_channel, claims, stated_purpose, benefit_and_mismatch, persuasion, conditions_and_sequence, contradictions_and_alternatives, technical_checks, missing_information.

## Ca SCREEN

```json
{
  "text": "Bật chia sẻ màn hình."
}
```

| Event | Hành động | Cụm động từ | Phủ định | Vai | Trạng thái | Phạm vi |
|---|---|---|---|---|---|---|
| a1 | share_screen | Bật chia sẻ màn hình (m1:0–20) | positive | request | requested | chưa có mã |

Quan hệ:
- Không có quan hệ được trích.

Câu hỏi bổ sung:
- Không có câu hỏi theo bộ luật hiện tại.

Trường unknown: sender_identity, relationship, communication_channel, claims, stated_purpose, benefit_and_mismatch, persuasion, conditions_and_sequence, contradictions_and_alternatives, technical_checks, missing_information.

## Ca CONTROL

```json
{
  "text": "Cấp quyền điều khiển."
}
```

| Event | Hành động | Cụm động từ | Phủ định | Vai | Trạng thái | Phạm vi |
|---|---|---|---|---|---|---|
| a1 | grant_control | Cấp quyền (m1:0–9) | positive | request | requested | chưa có mã |

Quan hệ:
- Không có quan hệ được trích.

Câu hỏi bổ sung:
- Không có câu hỏi theo bộ luật hiện tại.

Trường unknown: sender_identity, relationship, communication_channel, claims, stated_purpose, benefit_and_mismatch, persuasion, conditions_and_sequence, contradictions_and_alternatives, technical_checks, missing_information.

## Ca CHANNEL

```json
{
  "text": "Chuyển sang Telegram nhé."
}
```

| Event | Hành động | Cụm động từ | Phủ định | Vai | Trạng thái | Phạm vi |
|---|---|---|---|---|---|---|
| a1 | change_channel | Chuyển sang (m1:0–11) | positive | request | requested | chưa có mã |

Quan hệ:
- Không có quan hệ được trích.

Câu hỏi bổ sung:
- Không có câu hỏi theo bộ luật hiện tại.

Trường unknown: sender_identity, relationship, claims, stated_purpose, assets_and_access, benefit_and_mismatch, persuasion, conditions_and_sequence, contradictions_and_alternatives, technical_checks, missing_information.

## Ca SECRET

```json
{
  "text": "Giữ bí mật chuyện này."
}
```

| Event | Hành động | Cụm động từ | Phủ định | Vai | Trạng thái | Phạm vi |
|---|---|---|---|---|---|---|
| a1 | keep_secret | Giữ bí mật (m1:0–10) | positive | request | requested | chưa có mã |

Quan hệ:
- Không có quan hệ được trích.

Câu hỏi bổ sung:
- Không có câu hỏi theo bộ luật hiện tại.

Trường unknown: sender_identity, relationship, communication_channel, claims, stated_purpose, assets_and_access, benefit_and_mismatch, conditions_and_sequence, contradictions_and_alternatives, technical_checks, missing_information.

## Ca VERIFY

```json
{
  "text": "Đừng gọi số trong hợp đồng."
}
```

| Event | Hành động | Cụm động từ | Phủ định | Vai | Trạng thái | Phạm vi |
|---|---|---|---|---|---|---|
| a1 | avoid_verification | Đừng gọi (m1:0–8) | positive | request | requested | chưa có mã |

Quan hệ:
- Không có quan hệ được trích.

Câu hỏi bổ sung:
- Không có câu hỏi theo bộ luật hiện tại.

Trường unknown: sender_identity, relationship, communication_channel, claims, stated_purpose, assets_and_access, benefit_and_mismatch, persuasion, conditions_and_sequence, contradictions_and_alternatives, technical_checks, missing_information.

## Ca IDENTITY

```json
{
  "text": "Tôi là công an."
}
```

| Event | Hành động | Cụm động từ | Phủ định | Vai | Trạng thái | Phạm vi |
|---|---|---|---|---|---|---|
| a1 | identity_claim | Tôi là (m1:0–6) | positive | claim | unknown | chưa có mã |

Quan hệ:
- Không có quan hệ được trích.

Câu hỏi bổ sung:
- Không có câu hỏi theo bộ luật hiện tại.

Trường unknown: relationship, communication_channel, requested_actions, stated_purpose, assets_and_access, benefit_and_mismatch, persuasion, conditions_and_sequence, contradictions_and_alternatives, technical_checks, missing_information.

## Ca LOGIN

```json
{
  "text": "Tôi tự nhập mã trên ứng dụng chính thức."
}
```

| Event | Hành động | Cụm động từ | Phủ định | Vai | Trạng thái | Phạm vi |
|---|---|---|---|---|---|---|
| a1 | login | tự nhập (m1:4–11) | positive | claim | unknown | chưa có mã |

Quan hệ:
- Không có quan hệ được trích.

Câu hỏi bổ sung:
- Không có câu hỏi theo bộ luật hiện tại.

Trường unknown: sender_identity, relationship, communication_channel, requested_actions, stated_purpose, benefit_and_mismatch, persuasion, conditions_and_sequence, contradictions_and_alternatives, technical_checks, missing_information.

## Ca REPORTED

```json
{
  "text": "Bạn nói chưa thấy tiền về."
}
```

| Event | Hành động | Cụm động từ | Phủ định | Vai | Trạng thái | Phạm vi |
|---|---|---|---|---|---|---|
| a1 | receive_funds | thấy (m1:13–17) | negative | reported | pending | chưa có mã |

Quan hệ:
- reported_by: a1 → p1; observed; luật REL-REPORTED-SPEECH. Speaker là người thuật lại/cảnh báo, không phải người ra lệnh trong trích dẫn.

Câu hỏi bổ sung:
- Không có câu hỏi theo bộ luật hiện tại.

Trường unknown: sender_identity, relationship, communication_channel, requested_actions, stated_purpose, benefit_and_mismatch, persuasion, technical_checks, missing_information.

## Ca DOUBLE_NEGATION

```json
{
  "text": "Không phải là không cần chuyển tiền."
}
```

| Event | Hành động | Cụm động từ | Phủ định | Vai | Trạng thái | Phạm vi |
|---|---|---|---|---|---|---|
| a1 | transfer_funds | chuyển (m1:24–30) | uncertain | request | requested | chưa có mã |

Quan hệ:
- Không có quan hệ được trích.

Câu hỏi bổ sung:
- Người gửi đang yêu cầu thực hiện hay ngăn thao tác đó? Hãy cung cấp nguyên văn phần giải thích đã che bí mật.
- Khoản tiền được yêu cầu dùng để thanh toán việc gì?

Trường unknown: sender_identity, relationship, communication_channel, claims, requested_actions, stated_purpose, benefit_and_mismatch, persuasion, conditions_and_sequence, contradictions_and_alternatives, technical_checks, missing_information.

