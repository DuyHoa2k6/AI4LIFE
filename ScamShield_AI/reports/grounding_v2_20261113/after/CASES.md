# Kiểm tra riêng mức cảnh báo và dữ kiện

Các check là chú giải sparse, không phải chấm đầy đủ mọi sự kiện.

| Ca | Risk | Risk đúng kỳ vọng | Dữ kiện/quan hệ/câu hỏi đạt check | Trạng thái |
|---|---|---|---|---|
| receive_document | clear | True | True | complete |
| receive_money | clear | True | True | complete |
| send_guide | clear | True | True | complete |
| send_credentials | high | True | True | complete |
| prohibition | clear | True | True | complete |
| not_yet | clear | True | True | complete |
| conditional_loss | high | True | True | complete |
| no_requirement | clear | True | True | complete |
| deny_request | clear | True | True | complete |
| exit_alone | need_context | True | True | complete |
| reported_pressure | need_context | True | True | complete |
| paid_a_hold_b | clear | True | True | complete |
| unpaid_a | suspicious | True | True | complete |
| ambiguous_transaction | need_context | True | True | complete |
| verify_first | need_context | True | True | complete |
| pay_first | suspicious | True | True | complete |
| review_only | need_context | True | True | complete |
| missing_purpose | need_context | True | True | complete |
| known_purpose | need_context | True | True | complete |
| unknown_people | need_context | True | True | complete |
| named_pronoun | need_context | True | True | complete |
| ambiguous_pronoun | need_context | True | True | complete |
| passport_debt | high | True | True | complete |
| quoted_warning | clear | True | True | complete |
