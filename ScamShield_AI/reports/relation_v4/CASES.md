# Dự đoán từng phiên

Không gộp kết quả giữa các phiên hoặc thay ca lỗi bằng lần chạy tốt hơn.

## live

| Ca | Kỳ vọng | Thực tế | Lỗi | Giây |
| --- | --- | --- | --- | --- |
| RG-01 | high | need_context |  | 10.443 |
| RG-02 | high | high |  | 7.085 |
| RG-03 | clear | clear |  | 5.741 |
| RG-04 | clear | error | EVIDENCE_INVALID | 3.513 |
| RG-05 | clear | clear |  | 10.681 |
| RG-06 | need_context | need_context |  | 7.860 |
| RG-07 | high | high |  | 8.270 |
| RG-08 | need_context | need_context |  | 5.280 |

### live/RG-01 — NW-02 hồi quy dấu xác nhận

```json
{
  "text": "Không gọi là phí đâu anh, đây là dấu xác nhận bằng tiền. Anh gửi 1,2 triệu sang tài khoản em trước; thiếu dấu này thì khoản hoàn 12 triệu chưa thể về."
}
```

Lượt `review_prompt.txt`:

```json
{
  "review": {
    "risk_links": [
      {
        "request_id": "f1",
        "support_id": "f2"
      }
    ],
    "benign_finding_ids": [],
    "uncertain_finding_ids": [],
    "needs_context": true,
    "question_topics": [
      "relationship",
      "payment_purpose"
    ],
    "context_evidence": []
  },
  "relation_assessments": [
    {
      "request_id": "f1",
      "support_id": "f2",
      "status": "supported",
      "relation_type": "payment_required_before_benefit",
      "relation_evidence": [
        {
          "message_id": "m1",
          "quote": "Anh gửi 1,2 triệu sang tài khoản em trước; thiếu dấu này thì khoản hoàn 12 triệu chưa thể về.",
          "start": null,
          "end": null
        }
      ],
      "assessment_note": "Yêu cầu chuyển 1,2 triệu gắn liền với điều kiện phải có để nhận khoản hoàn 12 triệu.",
      "unresolved_reference": null,
      "missing_information": "Cần làm rõ mối quan hệ và bản chất khoản hoàn 12 triệu."
    }
  ],
  "uncertainty_reasons": []
}
```

Lượt `review_prompt.txt`:

```json
{
  "review": {
    "risk_links": [],
    "benign_finding_ids": [],
    "uncertain_finding_ids": [
      "f1"
    ],
    "needs_context": true,
    "question_topics": [
      "relationship",
      "payment_purpose"
    ],
    "context_evidence": []
  },
  "relation_assessments": [
    {
      "request_id": "f1",
      "support_id": "f2",
      "status": "uncertain",
      "relation_type": "payment_required_before_benefit",
      "relation_evidence": [
        {
          "message_id": "m1",
          "quote": "Anh gửi 1,2 triệu sang tài khoản em trước; thiếu dấu này thì khoản hoàn 12 triệu chưa thể về.",
          "start": null,
          "end": null
        }
      ],
      "assessment_note": "Chưa rõ mối quan hệ giữa hai bên và bản chất khoản hoàn 12 triệu để xác định đây là khoản phí bắt buộc hợp lệ hay thủ đoạn yêu cầu nộp tiền trước.",
      "unresolved_reference": "khoản hoàn 12 triệu",
      "missing_information": "Cần làm rõ mối quan hệ và bản chất của khoản tiền hoàn trả."
    }
  ],
  "uncertainty_reasons": [
    {
      "finding_id": "f1",
      "kind": "relation"
    }
  ]
}
```


### live/RG-02 — Tên gọi thay thế cho tiền ứng trước

```json
{
  "text": "Để mở lại số dư 18 triệu, cô mua vé xác thực giá 900 nghìn bằng cách chuyển vào tài khoản của cháu. Vé đó là điều kiện bắt buộc, chưa mua thì cô chưa lấy lại được số dư."
}
```

Lượt `review_prompt.txt`:

```json
{
  "review": {
    "risk_links": [
      {
        "request_id": "f1",
        "support_id": "f2"
      }
    ],
    "benign_finding_ids": [],
    "uncertain_finding_ids": [],
    "needs_context": false,
    "question_topics": [],
    "context_evidence": []
  },
  "relation_assessments": [
    {
      "request_id": "f1",
      "support_id": "f2",
      "status": "supported",
      "relation_type": "payment_required_before_benefit",
      "relation_evidence": [
        {
          "message_id": "m1",
          "quote": "Để mở lại số dư 18 triệu, cô mua vé xác thực giá 900 nghìn bằng cách chuyển vào tài khoản của cháu. Vé đó là điều kiện bắt buộc, chưa mua thì cô chưa lấy lại được số dư.",
          "start": null,
          "end": null
        }
      ],
      "assessment_note": "Yêu cầu chuyển tiền gắn liền với điều kiện bắt buộc phải nộp tiền để nhận lại số dư.",
      "unresolved_reference": null,
      "missing_information": null
    }
  ],
  "uncertainty_reasons": []
}
```


### live/RG-03 — Đặt mua hàng hợp pháp có hóa đơn

```json
{
  "text": "Thanh toán 240 nghìn cho đơn sách trước, cửa hàng xác nhận đủ tiền rồi mới giao đúng đơn đã đặt.",
  "context": "Tôi chủ động đặt đơn sách này trong ứng dụng chính thức. Đã kiểm tra hóa đơn, giá và tài khoản cửa hàng; đây là giá mua sách, không phải phí để mở khoản tiền bị giữ."
}
```

Lượt `review_prompt.txt`:

```json
{
  "review": {
    "risk_links": [],
    "benign_finding_ids": [
      "f1"
    ],
    "uncertain_finding_ids": [],
    "needs_context": false,
    "question_topics": [],
    "context_evidence": [
      {
        "quote": "Tôi chủ động đặt đơn sách này trong ứng dụng chính thức. Đã kiểm tra hóa đơn, giá và tài khoản cửa hàng; đây là giá mua sách, không phải phí để mở khoản tiền bị giữ.",
        "start": 0,
        "end": 165
      }
    ]
  },
  "relation_assessments": [],
  "uncertainty_reasons": []
}
```


### live/RG-04 — Bản tin trích lời dụ

```json
{
  "text": "Bản tin cảnh báo trích lời kẻ gian: “Mua vé xác thực bằng cách chuyển 900 nghìn cho tôi mới nhận lại số dư”. Đừng chuyển tiền theo lời dụ này. Bài viết không yêu cầu người đọc mua vé hay gửi tiền."
}
```


### live/RG-05 — Hai người nói về hai sự việc

```json
{
  "messages": [
    {
      "id": "m1",
      "speaker": "ban_cung_phong",
      "text": "Trả lại tớ 150 nghìn tiền ăn đã ứng hôm qua nhé."
    },
    {
      "id": "m2",
      "speaker": "quangcao",
      "text": "Chỉ khi đăng ký tham gia buổi đọc sách thì mới nhận quà sách miễn phí."
    }
  ],
  "context": "Tôi xác nhận khoản tiền ăn là khoản bạn cùng phòng đã ứng hộ, đúng số tiền và người nhận. Quảng cáo buổi đọc sách là người khác, không yêu cầu nộp tiền."
}
```

Lượt `review_prompt.txt`:

```json
{
  "review": {
    "risk_links": [],
    "benign_finding_ids": [
      "f1"
    ],
    "uncertain_finding_ids": [],
    "needs_context": false,
    "question_topics": [],
    "context_evidence": [
      {
        "quote": "Tôi xác nhận khoản tiền ăn là khoản bạn cùng phòng đã ứng hộ, đúng số tiền và người nhận. Quảng cáo buổi đọc sách là người khác, không yêu cầu nộp tiền.",
        "start": 0,
        "end": 152
      }
    ]
  },
  "relation_assessments": [
    {
      "request_id": "f1",
      "support_id": "f2",
      "status": "not_supporting_risk",
      "relation_type": "unrelated",
      "relation_evidence": [
        {
          "message_id": "m1",
          "quote": "Trả lại tớ 150 nghìn tiền ăn đã ứng hôm qua nhé.",
          "start": null,
          "end": null
        },
        {
          "message_id": "m2",
          "quote": "Chỉ khi đăng ký tham gia buổi đọc sách thì mới nhận quà sách miễn phí.",
          "start": null,
          "end": null
        }
      ],
      "assessment_note": "Yêu cầu tiền ăn và thông báo quảng cáo là hai sự việc hoàn toàn khác nhau từ hai người gửi khác nhau.",
      "unresolved_reference": null,
      "missing_information": null
    }
  ],
  "uncertainty_reasons": []
}
```

Lượt `review_prompt.txt`:

```json
{
  "review": {
    "risk_links": [],
    "benign_finding_ids": [
      "f1"
    ],
    "uncertain_finding_ids": [],
    "needs_context": false,
    "question_topics": [],
    "context_evidence": [
      {
        "quote": "Tôi xác nhận khoản tiền ăn là khoản bạn cùng phòng đã ứng hộ, đúng số tiền và người nhận. Quảng cáo buổi đọc sách là người khác, không yêu cầu nộp tiền.",
        "start": 0,
        "end": 152
      }
    ]
  },
  "relation_assessments": [],
  "uncertainty_reasons": []
}
```


### live/RG-06 — Chưa rõ đại từ chỉ thao tác nào

```json
{
  "text": "Anh chuyển lại khoản đó giúp tôi. Hoàn tất bước kia thì mới nhận phần còn lại. Tôi chưa giải thích khoản nào hay bước gì."
}
```

Lượt `review_prompt.txt`:

```json
{
  "review": {
    "risk_links": [],
    "benign_finding_ids": [],
    "uncertain_finding_ids": [
      "f1",
      "f2"
    ],
    "needs_context": true,
    "question_topics": [
      "relationship",
      "payment_purpose"
    ],
    "context_evidence": []
  },
  "relation_assessments": [
    {
      "request_id": "f1",
      "support_id": "f2",
      "status": "uncertain",
      "relation_type": "unknown",
      "relation_evidence": [
        {
          "message_id": "m1",
          "quote": "Anh chuyển lại khoản đó giúp tôi. Hoàn tất bước kia thì mới nhận phần còn lại.",
          "start": null,
          "end": null
        }
      ],
      "assessment_note": "Chưa rõ mối quan hệ giữa yêu cầu chuyển tiền và điều kiện hoàn tất bước kia do thiếu ngữ cảnh.",
      "unresolved_reference": "khoản đó, bước kia",
      "missing_information": "Mục đích khoản tiền và nội dung các bước thực hiện"
    }
  ],
  "uncertainty_reasons": [
    {
      "finding_id": "f1",
      "kind": "purpose"
    },
    {
      "finding_id": "f2",
      "kind": "relation"
    }
  ]
}
```


### live/RG-07 — Đại từ nối điều kiện qua hội thoại

```json
{
  "messages": [
    {
      "id": "r1",
      "speaker": "dieu_phoi",
      "text": "Chị chuyển 650 nghìn sang ví của em làm phần đối ứng."
    },
    {
      "id": "r2",
      "speaker": "khach",
      "text": "Phần đối ứng đó để làm gì?"
    },
    {
      "id": "r3",
      "speaker": "dieu_phoi",
      "text": "Không có khoản đó thì bên em chưa giải phóng tiền công 7 triệu cho chị được."
    }
  ]
}
```

Lượt `review_prompt.txt`:

```json
{
  "review": {
    "risk_links": [
      {
        "request_id": "f1",
        "support_id": "f2"
      }
    ],
    "benign_finding_ids": [],
    "uncertain_finding_ids": [],
    "needs_context": false,
    "question_topics": [],
    "context_evidence": []
  },
  "relation_assessments": [
    {
      "request_id": "f1",
      "support_id": "f2",
      "status": "supported",
      "relation_type": "payment_required_before_benefit",
      "relation_evidence": [
        {
          "message_id": "r1",
          "quote": "Chị chuyển 650 nghìn sang ví của em làm phần đối ứng.",
          "start": null,
          "end": null
        },
        {
          "message_id": "r3",
          "quote": "Không có khoản đó thì bên em chưa giải phóng tiền công 7 triệu cho chị được.",
          "start": null,
          "end": null
        }
      ],
      "assessment_note": "Yêu cầu chuyển tiền đối ứng đi kèm điều kiện phải hoàn thành khoản này mới được nhận tiền công.",
      "unresolved_reference": null,
      "missing_information": null
    }
  ],
  "uncertainty_reasons": []
}
```


### live/RG-08 — Một câu nhờ chuyển tiền thiếu bối cảnh

```json
{
  "text": "Bạn chuyển giúp mình 450 nghìn được không?"
}
```

Lượt `review_prompt.txt`:

```json
{
  "review": {
    "risk_links": [],
    "benign_finding_ids": [],
    "uncertain_finding_ids": [
      "f1"
    ],
    "needs_context": true,
    "question_topics": [
      "relationship",
      "payment_purpose"
    ],
    "context_evidence": []
  },
  "relation_assessments": [],
  "uncertainty_reasons": [
    {
      "finding_id": "f1",
      "kind": "purpose"
    },
    {
      "finding_id": "f1",
      "kind": "identity"
    }
  ]
}
```

## checked

| Ca | Kỳ vọng | Thực tế | Lỗi | Giây |
| --- | --- | --- | --- | --- |
| RF-01 | high | error | PROVIDER_INCONSISTENT_OUTPUT | 11.037 |
| RF-02 | high | high |  | 7.511 |
| RF-03 | high | high |  | 7.532 |
| RF-04 | clear | clear |  | 6.819 |
| RF-05 | clear | clear |  | 6.879 |
| RF-06 | clear | error | PROVIDER_UNAVAILABLE | 22.615 |
| RF-07 | need_context | need_context |  | 44.820 |
| RF-08 | need_context | suspicious |  | 25.738 |

### checked/RF-01 — NW-02 hồi quy

```json
{
  "text": "Không gọi là phí đâu anh, đây là dấu xác nhận bằng tiền. Anh gửi 1,2 triệu sang tài khoản em trước; thiếu dấu này thì khoản hoàn 12 triệu chưa thể về."
}
```

Lượt `review_prompt.txt`:

```json
{
  "review": {
    "risk_links": [
      {
        "request_id": "f1",
        "support_id": "f2"
      }
    ],
    "benign_finding_ids": [],
    "uncertain_finding_ids": [],
    "needs_context": true,
    "question_topics": [
      "relationship",
      "payment_purpose"
    ],
    "context_evidence": []
  },
  "relation_assessments": [
    {
      "request_id": "f1",
      "support_id": "f2",
      "status": "supported",
      "relation_type": "payment_required_before_benefit",
      "relation_evidence": [
        {
          "message_id": "m1",
          "quote": "Anh gửi 1,2 triệu sang tài khoản em trước; thiếu dấu này thì khoản hoàn 12 triệu chưa thể về.",
          "start": null,
          "end": null
        }
      ],
      "assessment_note": "Yêu cầu chuyển tiền được gắn liền với điều kiện nhận lại khoản hoàn lớn hơn.",
      "unresolved_reference": null,
      "missing_information": null
    }
  ],
  "uncertainty_reasons": [
    {
      "finding_id": "f1",
      "kind": "identity"
    },
    {
      "finding_id": "f2",
      "kind": "purpose"
    }
  ]
}
```

Lượt `review_prompt.txt`:

```json
{
  "review": {
    "risk_links": [
      {
        "request_id": "f1",
        "support_id": "f2"
      }
    ],
    "benign_finding_ids": [],
    "uncertain_finding_ids": [],
    "needs_context": true,
    "question_topics": [
      "relationship",
      "payment_purpose"
    ],
    "context_evidence": []
  },
  "relation_assessments": [
    {
      "request_id": "f1",
      "support_id": "f2",
      "status": "supported",
      "relation_type": "payment_required_before_benefit",
      "relation_evidence": [
        {
          "message_id": "m1",
          "quote": "Anh gửi 1,2 triệu sang tài khoản em trước; thiếu dấu này thì khoản hoàn 12 triệu chưa thể về.",
          "start": null,
          "end": null
        }
      ],
      "assessment_note": "Yêu cầu chuyển tiền được gắn liền rõ ràng với điều kiện để nhận khoản hoàn lớn hơn.",
      "unresolved_reference": null,
      "missing_information": null
    }
  ],
  "uncertainty_reasons": []
}
```


### checked/RF-02 — Neo đối soát thay tên phí

```json
{
  "text": "Khoản công 11 triệu chỉ được thả sau khi chị chuyển 720 nghìn sang ví em làm neo đối soát. Neo đó chưa đủ thì bên em không cho lấy lại tiền công."
}
```

Lượt `review_prompt.txt`:

```json
{
  "review": {
    "risk_links": [
      {
        "request_id": "f1",
        "support_id": "f2"
      }
    ],
    "benign_finding_ids": [],
    "uncertain_finding_ids": [],
    "needs_context": true,
    "question_topics": [
      "relationship",
      "payment_purpose"
    ],
    "context_evidence": []
  },
  "relation_assessments": [
    {
      "request_id": "f1",
      "support_id": "f2",
      "status": "supported",
      "relation_type": "payment_required_before_benefit",
      "relation_evidence": [
        {
          "message_id": "m1",
          "quote": "chị chuyển 720 nghìn sang ví em làm neo đối soát. Neo đó chưa đủ thì bên em không cho lấy lại tiền công.",
          "start": null,
          "end": null
        }
      ],
      "assessment_note": "Yêu cầu chuyển tiền được gắn liền với điều kiện phải hoàn thành để được lấy lại khoản tiền công.",
      "unresolved_reference": null,
      "missing_information": null
    }
  ],
  "uncertainty_reasons": []
}
```


### checked/RF-03 — Tham chiếu qua hai tin cùng người nói

```json
{
  "messages": [
    {
      "id": "q1",
      "speaker": "quanly",
      "text": "Anh gửi 380 nghìn vào tài khoản cá nhân của tôi làm khoản bảo chứng."
    },
    {
      "id": "q2",
      "speaker": "khach",
      "text": "Tại sao phải có bảo chứng?"
    },
    {
      "id": "q3",
      "speaker": "quanly",
      "text": "Chỉ khi có khoản vừa nói thì tôi mới mở rút 5 triệu tiền hoa hồng cho anh."
    }
  ]
}
```

Lượt `review_prompt.txt`:

```json
{
  "review": {
    "risk_links": [
      {
        "request_id": "f1",
        "support_id": "f2"
      }
    ],
    "benign_finding_ids": [],
    "uncertain_finding_ids": [],
    "needs_context": false,
    "question_topics": [],
    "context_evidence": []
  },
  "relation_assessments": [
    {
      "request_id": "f1",
      "support_id": "f2",
      "status": "supported",
      "relation_type": "payment_required_before_benefit",
      "relation_evidence": [
        {
          "message_id": "q1",
          "quote": "Anh gửi 380 nghìn vào tài khoản cá nhân của tôi làm khoản bảo chứng.",
          "start": null,
          "end": null
        },
        {
          "message_id": "q3",
          "quote": "Chỉ khi có khoản vừa nói thì tôi mới mở rút 5 triệu tiền hoa hồng cho anh.",
          "start": null,
          "end": null
        }
      ],
      "assessment_note": "Yêu cầu chuyển tiền bảo chứng được gắn liền với điều kiện rút hoa hồng.",
      "unresolved_reference": null,
      "missing_information": null
    }
  ],
  "uncertainty_reasons": []
}
```


### checked/RF-04 — Mua sách trả trước có đối chiếu

```json
{
  "text": "Chuyển 185 nghìn giá đơn sách đã đặt, nhận đủ thanh toán thì cửa hàng giao sách.",
  "context": "Tôi chủ động đặt sách trên cửa hàng chính thức. Đã kiểm tra đơn hàng, hóa đơn và đúng tài khoản cửa hàng. Đây là giá sách đã thỏa thuận, không phải tiền để mở khoản hoàn hay rút."
}
```

Lượt `review_prompt.txt`:

```json
{
  "review": {
    "risk_links": [],
    "benign_finding_ids": [
      "f1",
      "f2"
    ],
    "uncertain_finding_ids": [],
    "needs_context": false,
    "question_topics": [],
    "context_evidence": [
      {
        "quote": "Tôi chủ động đặt sách trên cửa hàng chính thức. Đã kiểm tra đơn hàng, hóa đơn và đúng tài khoản cửa hàng. Đây là giá sách đã thỏa thuận, không phải tiền để mở khoản hoàn hay rút.",
        "start": 0,
        "end": 178
      }
    ]
  },
  "relation_assessments": [
    {
      "request_id": "f1",
      "support_id": "f2",
      "status": "not_supporting_risk",
      "relation_type": "ordinary_transaction",
      "relation_evidence": [
        {
          "message_id": "m1",
          "quote": "Chuyển 185 nghìn giá đơn sách đã đặt, nhận đủ thanh toán thì cửa hàng giao sách.",
          "start": null,
          "end": null
        }
      ],
      "assessment_note": "Đây là giao dịch thương mại điện tử thông thường theo đơn hàng người dùng chủ động đặt, không phải yêu cầu nộp tiền rủi ro.",
      "unresolved_reference": null,
      "missing_information": null
    }
  ],
  "uncertainty_reasons": []
}
```


### checked/RF-05 — Lời dụ trong bài cảnh báo

```json
{
  "text": "Cảnh giác với lời dụ “chuyển tiền bảo chứng trước thì mới rút được hoa hồng”. Đây là ví dụ phòng tránh trong bản tin. Người đọc không được yêu cầu gửi khoản tiền nào; đừng chuyển theo lời dụ."
}
```

Lượt `review_prompt.txt`:

```json
{
  "review": {
    "risk_links": [],
    "benign_finding_ids": [],
    "uncertain_finding_ids": [],
    "needs_context": false,
    "question_topics": [],
    "context_evidence": []
  },
  "relation_assessments": [],
  "uncertainty_reasons": []
}
```


### checked/RF-06 — Tiền thuê và quà miễn phí khác người nói

```json
{
  "messages": [
    {
      "id": "u1",
      "speaker": "chunha",
      "text": "Gửi tiền thuê phòng tháng này như hợp đồng nhé."
    },
    {
      "id": "u2",
      "speaker": "thuvien",
      "text": "Chỉ khi tới dự buổi giới thiệu thì mới nhận sách tặng miễn phí, không nộp phí."
    }
  ],
  "context": "Tôi đã kiểm tra hợp đồng thuê và tài khoản chủ nhà qua kênh đã biết. Thông báo thư viện do người khác gửi, không liên quan việc trả tiền thuê."
}
```


### checked/RF-07 — Bước nọ và khoản kia chưa xác định

```json
{
  "text": "Chuyển lại khoản kia trước nhé. Sau bước nọ tôi mới xử lý phần còn lại. Chưa có tin nào giải thích khoản kia hay bước nọ."
}
```

Lượt `review_prompt.txt`:

```json
{
  "review": {
    "risk_links": [],
    "benign_finding_ids": [],
    "uncertain_finding_ids": [
      "f1",
      "f2"
    ],
    "needs_context": true,
    "question_topics": [
      "payment_purpose",
      "relationship"
    ],
    "context_evidence": []
  },
  "relation_assessments": [
    {
      "request_id": "f1",
      "support_id": "f2",
      "status": "uncertain",
      "relation_type": "unknown",
      "relation_evidence": [
        {
          "message_id": "m1",
          "quote": "Chuyển lại khoản kia trước nhé. Sau bước nọ tôi mới xử lý phần còn lại.",
          "start": null,
          "end": null
        }
      ],
      "assessment_note": "Mối quan hệ giữa khoản tiền cần chuyển và bước xử lý phía sau chưa được làm rõ do thiếu ngữ cảnh cụ thể.",
      "unresolved_reference": "khoản kia hay bước nọ",
      "missing_information": "Thiếu thông tin giải thích bản chất của khoản tiền và nội dung của bước xử lý."
    }
  ],
  "uncertainty_reasons": [
    {
      "finding_id": "f1",
      "kind": "purpose"
    },
    {
      "finding_id": "f2",
      "kind": "relation"
    }
  ]
}
```


### checked/RF-08 — Quyền nào chưa biết

```json
{
  "text": "Một người nhắn bảo tôi bấm đồng ý cấp quyền, nhưng tôi chưa biết đó là quyền thông báo hay quyền điều khiển máy."
}
```

Lượt `review_prompt.txt`:

```json
{
  "review": {
    "risk_links": [],
    "benign_finding_ids": [],
    "uncertain_finding_ids": [
      "f1"
    ],
    "needs_context": true,
    "question_topics": [
      "permission_purpose",
      "source_of_request"
    ],
    "context_evidence": []
  },
  "relation_assessments": [],
  "uncertainty_reasons": [
    {
      "finding_id": "f1",
      "kind": "purpose"
    }
  ]
}
```

## focused

| Ca | Kỳ vọng | Thực tế | Lỗi | Giây |
| --- | --- | --- | --- | --- |
| RF-01 | high | error | PROVIDER_UNAVAILABLE | 8.260 |
| RF-05 | clear | clear |  | 20.922 |

### focused/RF-01 — NW-02 hồi quy

```json
{
  "text": "Không gọi là phí đâu anh, đây là dấu xác nhận bằng tiền. Anh gửi 1,2 triệu sang tài khoản em trước; thiếu dấu này thì khoản hoàn 12 triệu chưa thể về."
}
```


### focused/RF-05 — Lời dụ trong bài cảnh báo

```json
{
  "text": "Cảnh giác với lời dụ “chuyển tiền bảo chứng trước thì mới rút được hoa hồng”. Đây là ví dụ phòng tránh trong bản tin. Người đọc không được yêu cầu gửi khoản tiền nào; đừng chuyển theo lời dụ."
}
```

Lượt `review_prompt.txt`:

```json
{
  "review": {
    "risk_links": [],
    "benign_finding_ids": [],
    "uncertain_finding_ids": [],
    "needs_context": false,
    "question_topics": [],
    "context_evidence": []
  },
  "relation_assessments": [],
  "uncertainty_reasons": []
}
```
