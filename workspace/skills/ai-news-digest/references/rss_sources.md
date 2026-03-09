<!-- references/rss_sources.md -->
# RSS Sources - AI & Tech News

Cập nhật: 2026-02-12

## Tier 1 — Nguồn chính (ưu tiên cao, weight 1.5x)
| Nguồn | RSS URL | Ghi chú |
|-------|---------|---------|
| Techmeme | https://www.techmeme.com/feed.xml | Tổng hợp tin hot nhất |
| Hacker News (Best) | https://hnrss.org/best | Top stories, ít noise |
| TechCrunch AI | https://techcrunch.com/category/artificial-intelligence/feed/ | Chuyên mục AI |
| The Verge AI | https://www.theverge.com/rss/ai-artificial-intelligence/index.xml | AI coverage |

## Tier 2 — Nguồn bổ sung (weight 1.0x)
| Nguồn | RSS URL | Ghi chú |
|-------|---------|---------|
| Ars Technica | https://feeds.arstechnica.com/arstechnica/technology-lab | Deep tech |
| MIT Tech Review | https://www.technologyreview.com/feed/ | Nghiên cứu AI |
| OpenAI Blog | https://openai.com/blog/rss.xml | Tin từ OpenAI |
| Anthropic News | https://www.anthropic.com/rss.xml | Tin từ Anthropic |
| VentureBeat AI | https://venturebeat.com/category/ai/feed/ | AI business |

## Tier 3 — Chuyên sâu (weight 0.8x)  
| Nguồn | RSS URL | Ghi chú |
|-------|---------|---------|
| ArXiv CS.AI | http://export.arxiv.org/rss/cs.AI | Papers mới nhất |
| Hugging Face Blog | https://huggingface.co/blog/feed.xml | Open source AI |
| AI News (Sebastian Raschka) | https://magazine.sebastianraschka.com/feed | Phân tích sâu |

## Tier 4 — Tin tức Việt Nam (weight 1.0x) - TỐI ĐA 5 BÀI
| Nguồn | RSS URL | Ghi chú |
|-------|---------|---------|
| VNExpress - Công nghệ | https://vnexpress.net/rss/so-hoa.rss | Tin công nghệ VN |
| Genk - Công nghệ | https://genk.vn/rss/cong-nghe.rss | Tin tech Genk |
| Tinh tế - Công nghệ | https://tinhte.vn/rss/cong-nghe.rss | Tin tech Tinh tế |
| TechZ - Công nghệ | https://techz.vn/rss.xml | Tin AI/tech TechZ |

## Cách thêm nguồn mới
Thêm 1 dòng vào bảng phù hợp, đảm bảo URL là RSS/Atom feed hợp lệ.
Script sẽ tự nhận khi chạy lần tiếp theo.

## Cấu hình báo cáo
- **Tổng bài**: 20 bài (15 nước ngoài Tier 1-3 + 5 bài Việt Nam Tier 4)
- **Ưu tiên**: Nước ngoài 75%, Việt Nam 25%
- **Format**: Giữ nguyên (tiêu đề + tóm tắt + link)