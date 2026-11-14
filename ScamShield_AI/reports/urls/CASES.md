# Dự đoán URL và văn bản từng phiên

Các URL dưới đây là đầu vào tổng hợp; hệ thống không mở trang đích. Không phải danh sách website đã xác minh độc hại.

## live

| Ca | Kỳ vọng | Thực tế | HTTP | Giây |
| --- | --- | --- | --- | --- |
| URL-01 | high | high | 200 | 23.961 |
| URL-02 | clear | clear | 200 | 13.087 |
| URL-03 | clear | error | 502 | 10.432 |
| URL-04 | suspicious | suspicious | 200 | 12.419 |
| URL-05 | clear | clear | 200 | 11.276 |
| URL-06 | clear | error | 502 | 14.036 |

### live/URL-01 — Yêu cầu OTP và miền gần giống

```json
{
  "text": "Tôi là hỗ trợ YouTube. Gửi mã OTP đăng nhập của bạn tại đây để tôi ngăn khóa tài khoản.",
  "links": [
    {
      "id": "u1",
      "message_id": "m1",
      "url": "https://youtubee.com/auth?token=SYNTHETIC",
      "display_text": "tại đây",
      "origin": "user_supplied"
    }
  ]
}
```

```json
{
  "risk_status": "high",
  "url_analysis": [
    {
      "link_id": "u1",
      "message_id": "m1",
      "origin": "user_supplied",
      "status": "parsed",
      "display_url": "https://youtubee.com/",
      "hostname": "youtubee.com",
      "unicode_hostname": "youtubee.com",
      "registered_domain": "youtubee.com",
      "reference_domain": null,
      "label_status": "grounded",
      "signals": [
        {
          "code": "lookalike_reference_domain",
          "level": "review",
          "detail": "Tên miền gần giống youtube.com theo khoảng cách ký tự, không phải xác suất lừa đảo."
        }
      ],
      "reputation_status": "not_checked"
    }
  ],
  "url_uses": [
    {
      "link_id": "u1",
      "signal_codes": [
        "lookalike_reference_domain"
      ],
      "finding_refs": [
        "f2"
      ],
      "relation": "supports_request_risk"
    }
  ],
  "code": null,
  "diagnostic": null
}
```


### live/URL-02 — Bài cảnh báo nhắc tên gần giống

```json
{
  "text": "Cảnh báo: link https://youtubee.com là ví dụ tên gần giống. Đừng đăng nhập hoặc gửi mã qua đó. Đây là bài phòng tránh, không yêu cầu làm theo."
}
```

```json
{
  "risk_status": "clear",
  "url_analysis": [
    {
      "link_id": "auto-url-0-0",
      "message_id": "m1",
      "origin": "text",
      "status": "parsed",
      "display_url": "https://youtubee.com/",
      "hostname": "youtubee.com",
      "unicode_hostname": "youtubee.com",
      "registered_domain": "youtubee.com",
      "reference_domain": null,
      "label_status": "grounded",
      "signals": [
        {
          "code": "lookalike_reference_domain",
          "level": "review",
          "detail": "Tên miền gần giống youtube.com theo khoảng cách ký tự, không phải xác suất lừa đảo."
        }
      ],
      "reputation_status": "not_checked"
    }
  ],
  "url_uses": [
    {
      "link_id": "auto-url-0-0",
      "signal_codes": [
        "lookalike_reference_domain"
      ],
      "finding_refs": [
        "f1"
      ],
      "relation": "quoted_warning"
    }
  ],
  "code": null,
  "diagnostic": null
}
```


### live/URL-03 — Tự đọc nội dung tại miền tham chiếu

```json
{
  "text": "Tôi tự mở https://www.youtube.com để xem video học. Không ai yêu cầu tôi đăng nhập hay cung cấp mã."
}
```

```json
{
  "risk_status": null,
  "url_analysis": null,
  "url_uses": null,
  "code": "PROVIDER_INVALID_OUTPUT",
  "diagnostic": {
    "stage": "review",
    "kind": "validation",
    "attempts": 1,
    "output_format": "json_schema",
    "issues": [
      {
        "path": "url_uses.0.signal_codes",
        "type": "too_short"
      }
    ]
  }
}
```


### live/URL-04 — Đích ẩn khác nhãn và yêu cầu đăng nhập

```json
{
  "text": "Đăng nhập tài khoản để xác minh tại https://youtube.com.",
  "links": [
    {
      "id": "u4",
      "message_id": "m1",
      "url": "https://youtube.com.account-check.net/login",
      "display_text": "https://youtube.com",
      "origin": "user_supplied"
    }
  ]
}
```

```json
{
  "risk_status": "suspicious",
  "url_analysis": [
    {
      "link_id": "u4",
      "message_id": "m1",
      "origin": "user_supplied",
      "status": "parsed",
      "display_url": "https://youtube.com.account-check.net/",
      "hostname": "youtube.com.account-check.net",
      "unicode_hostname": "youtube.com.account-check.net",
      "registered_domain": "account-check.net",
      "reference_domain": null,
      "label_status": "grounded",
      "signals": [
        {
          "code": "display_target_mismatch",
          "level": "review",
          "detail": "Tên miền hiển thị youtube.com khác tên miền đích youtube.com.account-check.net"
        },
        {
          "code": "brand_in_subdomain",
          "level": "review",
          "detail": "Tên tham chiếu youtube.com chỉ xuất hiện ở phần miền phụ của youtube.com.account-check.net"
        }
      ],
      "reputation_status": "not_checked"
    }
  ],
  "url_uses": [
    {
      "link_id": "u4",
      "signal_codes": [
        "display_target_mismatch",
        "brand_in_subdomain"
      ],
      "finding_refs": [
        "f1"
      ],
      "relation": "supports_request_risk"
    }
  ],
  "code": null,
  "diagnostic": null
}
```


### live/URL-05 — Tên miền tiếng Việt không tự thành độc hại

```json
{
  "text": "Tôi đang đọc bài hướng dẫn ngôn ngữ tại https://vídụ.vn, không làm thao tác đăng nhập hay thanh toán."
}
```

```json
{
  "risk_status": "clear",
  "url_analysis": [
    {
      "link_id": "auto-url-0-0",
      "message_id": "m1",
      "origin": "text",
      "status": "parsed",
      "display_url": "https://xn--vd-nja3081a.vn/",
      "hostname": "xn--vd-nja3081a.vn",
      "unicode_hostname": "vídụ.vn",
      "registered_domain": "xn--vd-nja3081a.vn",
      "reference_domain": null,
      "label_status": "grounded",
      "signals": [
        {
          "code": "punycode_hostname",
          "level": "info",
          "detail": "Tên miền có dạng Punycode; không tự chứng minh độc hại."
        }
      ],
      "reputation_status": "not_checked"
    }
  ],
  "url_uses": [
    {
      "link_id": "auto-url-0-0",
      "signal_codes": [
        "punycode_hostname"
      ],
      "finding_refs": [
        "f1"
      ],
      "relation": "quoted_warning"
    }
  ],
  "code": null,
  "diagnostic": null
}
```


### live/URL-06 — Bài cảnh báo có nhãn và đích không khớp

```json
{
  "text": "Bài cảnh báo đưa ví dụ: https://youtube.com. Đích thật của liên kết mẫu là một miền khác; đừng bấm đăng nhập.",
  "links": [
    {
      "id": "u6",
      "message_id": "m1",
      "url": "https://help.example.net/check",
      "display_text": "https://youtube.com",
      "origin": "user_supplied"
    }
  ]
}
```

```json
{
  "risk_status": null,
  "url_analysis": null,
  "url_uses": null,
  "code": "EVIDENCE_INVALID",
  "diagnostic": null
}
```

## checked

| Ca | Kỳ vọng | Thực tế | HTTP | Giây |
| --- | --- | --- | --- | --- |
| URL-01 | high | high | 200 | 13.860 |
| URL-02 | clear | clear | 200 | 14.719 |
| URL-03 | clear | clear | 200 | 14.352 |
| URL-04 | suspicious | suspicious | 200 | 10.847 |
| URL-05 | clear | clear | 200 | 9.681 |
| URL-06 | clear | clear | 200 | 15.142 |

### checked/URL-01 — Yêu cầu OTP và miền gần giống

```json
{
  "text": "Tôi là hỗ trợ YouTube. Gửi mã OTP đăng nhập của bạn tại đây để tôi ngăn khóa tài khoản.",
  "links": [
    {
      "id": "u1",
      "message_id": "m1",
      "url": "https://youtubee.com/auth?token=SYNTHETIC",
      "display_text": "tại đây",
      "origin": "user_supplied"
    }
  ]
}
```

```json
{
  "risk_status": "high",
  "url_analysis": [
    {
      "link_id": "u1",
      "message_id": "m1",
      "origin": "user_supplied",
      "status": "parsed",
      "display_url": "https://youtubee.com/",
      "hostname": "youtubee.com",
      "unicode_hostname": "youtubee.com",
      "registered_domain": "youtubee.com",
      "reference_domain": null,
      "label_status": "grounded",
      "signals": [
        {
          "code": "lookalike_reference_domain",
          "level": "review",
          "detail": "Tên miền gần giống youtube.com theo khoảng cách ký tự, không phải xác suất lừa đảo."
        }
      ],
      "reputation_status": "not_checked"
    }
  ],
  "url_uses": [
    {
      "link_id": "u1",
      "signal_codes": [
        "lookalike_reference_domain"
      ],
      "finding_refs": [
        "f1"
      ],
      "relation": "supports_request_risk"
    }
  ],
  "code": null,
  "diagnostic": null
}
```


### checked/URL-02 — Bài cảnh báo nhắc tên gần giống

```json
{
  "text": "Cảnh báo: link https://youtubee.com là ví dụ tên gần giống. Đừng đăng nhập hoặc gửi mã qua đó. Đây là bài phòng tránh, không yêu cầu làm theo."
}
```

```json
{
  "risk_status": "clear",
  "url_analysis": [
    {
      "link_id": "auto-url-0-0",
      "message_id": "m1",
      "origin": "text",
      "status": "parsed",
      "display_url": "https://youtubee.com/",
      "hostname": "youtubee.com",
      "unicode_hostname": "youtubee.com",
      "registered_domain": "youtubee.com",
      "reference_domain": null,
      "label_status": "grounded",
      "signals": [
        {
          "code": "lookalike_reference_domain",
          "level": "review",
          "detail": "Tên miền gần giống youtube.com theo khoảng cách ký tự, không phải xác suất lừa đảo."
        }
      ],
      "reputation_status": "not_checked"
    }
  ],
  "url_uses": [
    {
      "link_id": "auto-url-0-0",
      "signal_codes": [
        "lookalike_reference_domain"
      ],
      "finding_refs": [
        "f1"
      ],
      "relation": "quoted_warning"
    }
  ],
  "code": null,
  "diagnostic": null
}
```


### checked/URL-03 — Tự đọc nội dung tại miền tham chiếu

```json
{
  "text": "Tôi tự mở https://www.youtube.com để xem video học. Không ai yêu cầu tôi đăng nhập hay cung cấp mã."
}
```

```json
{
  "risk_status": "clear",
  "url_analysis": [
    {
      "link_id": "auto-url-0-0",
      "message_id": "m1",
      "origin": "text",
      "status": "parsed",
      "display_url": "https://www.youtube.com/",
      "hostname": "www.youtube.com",
      "unicode_hostname": "www.youtube.com",
      "registered_domain": "youtube.com",
      "reference_domain": "youtube.com",
      "label_status": "grounded",
      "signals": [],
      "reputation_status": "not_checked"
    }
  ],
  "url_uses": [
    {
      "link_id": "auto-url-0-0",
      "signal_codes": [],
      "finding_refs": [
        "f1"
      ],
      "relation": "background"
    }
  ],
  "code": null,
  "diagnostic": null
}
```


### checked/URL-04 — Đích ẩn khác nhãn và yêu cầu đăng nhập

```json
{
  "text": "Đăng nhập tài khoản để xác minh tại https://youtube.com.",
  "links": [
    {
      "id": "u4",
      "message_id": "m1",
      "url": "https://youtube.com.account-check.net/login",
      "display_text": "https://youtube.com",
      "origin": "user_supplied"
    }
  ]
}
```

```json
{
  "risk_status": "suspicious",
  "url_analysis": [
    {
      "link_id": "u4",
      "message_id": "m1",
      "origin": "user_supplied",
      "status": "parsed",
      "display_url": "https://youtube.com.account-check.net/",
      "hostname": "youtube.com.account-check.net",
      "unicode_hostname": "youtube.com.account-check.net",
      "registered_domain": "account-check.net",
      "reference_domain": null,
      "label_status": "grounded",
      "signals": [
        {
          "code": "display_target_mismatch",
          "level": "review",
          "detail": "Tên miền hiển thị youtube.com khác tên miền đích youtube.com.account-check.net"
        },
        {
          "code": "brand_in_subdomain",
          "level": "review",
          "detail": "Tên tham chiếu youtube.com chỉ xuất hiện ở phần miền phụ của youtube.com.account-check.net"
        }
      ],
      "reputation_status": "not_checked"
    }
  ],
  "url_uses": [
    {
      "link_id": "u4",
      "signal_codes": [
        "display_target_mismatch",
        "brand_in_subdomain"
      ],
      "finding_refs": [
        "f1"
      ],
      "relation": "supports_request_risk"
    }
  ],
  "code": null,
  "diagnostic": null
}
```


### checked/URL-05 — Tên miền tiếng Việt không tự thành độc hại

```json
{
  "text": "Tôi đang đọc bài hướng dẫn ngôn ngữ tại https://vídụ.vn, không làm thao tác đăng nhập hay thanh toán."
}
```

```json
{
  "risk_status": "clear",
  "url_analysis": [
    {
      "link_id": "auto-url-0-0",
      "message_id": "m1",
      "origin": "text",
      "status": "parsed",
      "display_url": "https://xn--vd-nja3081a.vn/",
      "hostname": "xn--vd-nja3081a.vn",
      "unicode_hostname": "vídụ.vn",
      "registered_domain": "xn--vd-nja3081a.vn",
      "reference_domain": null,
      "label_status": "grounded",
      "signals": [
        {
          "code": "punycode_hostname",
          "level": "info",
          "detail": "Tên miền có dạng Punycode; không tự chứng minh độc hại."
        }
      ],
      "reputation_status": "not_checked"
    }
  ],
  "url_uses": [
    {
      "link_id": "auto-url-0-0",
      "signal_codes": [
        "punycode_hostname"
      ],
      "finding_refs": [
        "f1"
      ],
      "relation": "background"
    }
  ],
  "code": null,
  "diagnostic": null
}
```


### checked/URL-06 — Bài cảnh báo có nhãn và đích không khớp

```json
{
  "text": "Bài cảnh báo đưa ví dụ: https://youtube.com. Đích thật của liên kết mẫu là một miền khác; đừng bấm đăng nhập.",
  "links": [
    {
      "id": "u6",
      "message_id": "m1",
      "url": "https://help.example.net/check",
      "display_text": "https://youtube.com",
      "origin": "user_supplied"
    }
  ]
}
```

```json
{
  "risk_status": "clear",
  "url_analysis": [
    {
      "link_id": "u6",
      "message_id": "m1",
      "origin": "user_supplied",
      "status": "parsed",
      "display_url": "https://help.example.net/",
      "hostname": "help.example.net",
      "unicode_hostname": "help.example.net",
      "registered_domain": "example.net",
      "reference_domain": null,
      "label_status": "grounded",
      "signals": [
        {
          "code": "display_target_mismatch",
          "level": "review",
          "detail": "Tên miền hiển thị youtube.com khác tên miền đích help.example.net"
        }
      ],
      "reputation_status": "not_checked"
    }
  ],
  "url_uses": [
    {
      "link_id": "u6",
      "signal_codes": [
        "display_target_mismatch"
      ],
      "finding_refs": [
        "f1"
      ],
      "relation": "quoted_warning"
    }
  ],
  "code": null,
  "diagnostic": null
}
```
