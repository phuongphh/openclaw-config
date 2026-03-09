---
name: otofun-chogioi
description: >
  Scrape và tóm tắt các bài bán hàng từ diễn đàn OtoFun mục Chợ Giời.
  Đăng nhập, lấy danh sách bài đăng từ nhiều trang, parse thành dữ liệu
  có cấu trúc, tóm tắt bằng tiếng Việt, và gửi báo cáo qua Telegram.
metadata:
  openclaw:
    requires:
      bins: ["python3"]
      env: ["OTOFUN_USERNAME", "OTOFUN_PASSWORD"]
---

# OtoFun Chợ Giời Scraper

## Khi nào sử dụng skill này
- Khi người dùng hỏi về bài bán hàng trên OtoFun, Chợ Giời, 
  hoặc muốn xem tin rao vặt các loại hàng hoá khác nhau như quần áo, thiết bị điện tử từ otofun
- Khi người dùng yêu cầu tóm tắt, theo dõi, hoặc báo cáo 
  từ diễn đàn OtoFun
- Khi có cron job kích hoạt task "otofun daily scan"

## Cách thực hiện

### Bước 1: Chạy script scrape (KHÔNG dùng browser)
Chạy script Python để login và lấy dữ liệu. Script này xử lý 
toàn bộ việc HTTP request, parse HTML, và trả về JSON thuần.
```bash
cd ~/.openclaw/workspace/skills/otofun-chogioi/scripts
python3 scrape_otofun.py --pages 5 --output /tmp/otofun_data.json
```

**QUAN TRỌNG**: KHÔNG dùng browser tool cho bước này. 
Script đã xử lý login và parse. Kết quả là file JSON nhỏ gọn, 
chỉ chứa thông tin cần thiết.

### Bước 2: Đọc dữ liệu JSON và tóm tắt
Đọc file `/tmp/otofun_data.json`. File chứa array các object với 
các trường: title, price, author, date, url, category, description_short.

Tạo báo cáo bằng tiếng Việt theo format:
```
📋 BÁO CÁO OTOFUN CHỢ GIỜI - {ngày}
━━━━━━━━━━━━━━━━━━━━━━━━

🔥 TOP DEALS ĐÁNG CHÚ Ý:
1. [Tên] - [Giá] - [Lý do đáng chú ý]
2. ...
3. ...

📊 TỔNG HỢP {N} BÀI ĐĂNG:
- Thiết bị điện tử: X bài | Khoảng giá: ...
- Đồ thời trang, quần áo, phụ kiện: X bài | Khoảng giá: ...
- Thiết bị gia dụng: X bài
- Các loại khác: X bài

📝 CHI TIẾT:
[Mỗi bài 1 dòng: Tên | Giá | Người bán | Link]
```

### Bước 3: Gửi qua Telegram
Gửi báo cáo trên cho người dùng qua Telegram. 
Nếu quá dài, chia thành nhiều tin nhắn.

## Lưu ý
- Script tự quản lý cookie session, không cần login lại mỗi lần
- Nếu script báo lỗi login, thông báo cho người dùng kiểm tra 
  credentials trong biến môi trường
- Không scrape quá 5 lần/ngày để tránh bị chặn IP
- Dữ liệu JSON đã được làm sạch, KHÔNG cần xử lý thêm HTML
