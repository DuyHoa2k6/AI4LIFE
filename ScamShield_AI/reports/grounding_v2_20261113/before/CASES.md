# Kiểm tra riêng mức cảnh báo và dữ kiện

Các check là chú giải sparse, không phải chấm đầy đủ mọi sự kiện.

| Ca | Risk | Risk đúng kỳ vọng | Dữ kiện/quan hệ/câu hỏi đạt check | Trạng thái |
|---|---|---|---|---|
| receive_document | clear | True | False | complete |
| receive_money | need_context | False | False | complete |
| send_guide | need_context | False | False | complete |
| send_credentials | high | True | True | complete |
| prohibition | clear | True | True | complete |
| not_yet | clear | True | True | complete |
| conditional_loss | high | True | False | complete |
| no_requirement | clear | True | True | complete |
| deny_request | clear | True | True | complete |
| exit_alone | need_context | True | True | complete |
| reported_pressure | clear | False | False | complete |
| paid_a_hold_b | need_context | False | False | complete |
| unpaid_a | suspicious | True | True | complete |
| ambiguous_transaction | need_context | True | True | complete |
| verify_first | need_context | True | False | complete |
| pay_first | suspicious | True | True | complete |
| review_only | need_context | True | False | complete |
| missing_purpose | need_context | True | False | complete |
| known_purpose | need_context | True | False | complete |
| unknown_people | need_context | True | False | unsupported |
| named_pronoun | need_context | True | False | complete |
| ambiguous_pronoun | need_context | True | False | complete |
| passport_debt | high | True | False | complete |
| quoted_warning | clear | True | True | complete |
