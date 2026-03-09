<!-- references/otofun_selectors.md -->
# OtoFun CSS Selectors

Cập nhật lần cuối: 2026-02-10
OtoFun chạy XenForo 2.x

## Listing page
- Thread item: `.structItem--thread`
- Tiêu đề: `.structItem-title a:not(.labelLink)`
- Tác giả: `.username`
- Ngày đăng: `.structItem-startDate time[datetime]`
- Label/tag: `.labelLink`
- Snippet: `.structItem-minor`

## URLs 
- Chợ Giời (tổng): `/forums/cho-gioi.89/`
- Đồ điện tử: `/forums/do-dien-tu.312/`
- Bất Động Sản: `/forums/cho-bat-dong-san.423/`
- Trang N: `/page-{N}` append vào URL forum

## Cập nhật lần cuối: 2026-02-11
- Sửa forum ID: .89 (không phải .98) 

## Login
- Form action: `/login/login`
- CSRF: `input[name="_xfToken"]`
- Fields: `login`, `password`, `remember`

## Ghi chú
- Nếu selectors thay đổi, cập nhật file này 
  VÀ script scrape_otofun.py