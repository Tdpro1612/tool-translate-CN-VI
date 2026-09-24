import asyncio
import os
import random
from playwright.async_api import async_playwright
from crawl.constants import USER_AGENTS, fetch_free_proxies

INDEX_URL = "https://www.69shuba.com/book/53446/"
OUTPUT_DIR = "output"
LIST_CHAPTER_FILE = "danh_sach_chuong.txt"
ERR_CHAPTER_FILE = "err_chapter.txt"
MAX_RETRIES = 3

def load_chapters_from_file():
    """Đọc danh sách chương từ file danh_sach_chuong.txt nếu đã tồn tại"""
    chapter_links = []
    if os.path.exists(LIST_CHAPTER_FILE):
        with open(LIST_CHAPTER_FILE, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or " : " not in line:
                    continue
                # Tách title và url dựa vào định dạng: "Chương X: {title} : {url}"
                parts = line.split(" : ")
                if len(parts) >= 2:
                    url = parts[-1].strip()
                    # Lấy phần title đằng trước (bỏ bớt phần tiền tố 'Chương X: ' nếu có)
                    title_part = " : ".join(parts[:-1]).strip()
                    if ":" in title_part:
                        title = title_part.split(":", 1)[1].strip()
                    else:
                        title = title_part
                    chapter_links.append((title, url))
    return chapter_links

async def crawl_chapter_with_retry(context, url, max_retries=MAX_RETRIES):
    """Hàm tải nội dung chương với cơ chế Retry"""
    for attempt in range(1, max_retries + 1):
        page = None
        try:
            page = await context.new_page()
            await page.goto(url, timeout=10000, wait_until="domcontentloaded")
            await page.wait_for_selector("div.txtnav", timeout=5000)
            
            # Xóa các phần tử dư thừa trong DOM
            await page.evaluate("""() => {
                const contentDiv = document.querySelector('div.txtnav');
                if (contentDiv) {
                    const extras = contentDiv.querySelectorAll('div, script, style, h1');
                    extras.forEach(el => el.remove());
                }
            }""")

            content_text = await page.locator("div.txtnav").text_content()
            await page.close()
            
            if content_text and content_text.strip():
                return content_text.strip()
        except Exception as e:
            if page:
                await page.close()
            if attempt < max_retries:
                await asyncio.sleep(1)
            else:
                raise e

async def crawl_novel():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    chapter_links = []
    
    # ------------------------------------------------------------------
    # CHẾ ĐỘ 1: Kiểm tra xem file danh sách chương đã có sẵn chưa
    # ------------------------------------------------------------------
    if os.path.exists(LIST_CHAPTER_FILE) and os.path.getsize(LIST_CHAPTER_FILE) > 0:
        print(f"⚡ Phát hiện file '{LIST_CHAPTER_FILE}' đã tồn tại!")
        print("🚀 Đang đọc danh sách chương từ file để bắt đầu cào ngay...")
        chapter_links = load_chapters_from_file()
        print(f"✅ Đã tải {len(chapter_links)} chương từ file có sẵn.")
    
    async with async_playwright() as p:
        # Nếu chưa có file danh sách chương thì mới mở trình duyệt quét mục lục
        if not chapter_links:
            print("📂 Chưa có danh sách chương. Đang khởi chạy browser để quét mục lục...")
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(
                user_agent=random.choice(USER_AGENTS),
                extra_http_headers={"Accept-Language": "vi-VN,vi;q=0.9,en-US;q=0.8"}
            )
            page = await context.new_page()
            await page.goto(INDEX_URL, timeout=30000, wait_until="domcontentloaded")
            await page.wait_for_selector("div#catalog.catalog")

            chapter_elements = await page.locator("div#catalog.catalog ul li[data-num] a").all()
            for element in chapter_elements:
                title = await element.text_content()
                href = await element.get_attribute("href")
                if href:
                    full_url = href if href.startswith("http") else f"https://www.69shuba.com{href}"
                    chapter_links.append((title.strip(), full_url))

            print(f"✅ Đã quét thành công {len(chapter_links)} chương.")
            await browser.close()

            # Lưu lại file danh_sach_chuong.txt để dùng cho các lần sau
            with open(LIST_CHAPTER_FILE, "w", encoding="utf-8") as f:
                for idx, (title, url) in enumerate(chapter_links, 1):
                    f.write(f"Chương {idx}: {title} : {url}\n")
            print(f"💾 Đã lưu danh sách chương vào file: {LIST_CHAPTER_FILE}")

        total_chapters = len(chapter_links)
        
        # ------------------------------------------------------------------
        # CHẾ ĐỘ 2: Bắt đầu cào nội dung từng chương (có Skip file đã cào)
        # ------------------------------------------------------------------
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(user_agent=random.choice(USER_AGENTS))

        print("\n🔥 Bắt đầu tiến trình tải nội dung các chương...")
        
        for index, (title, url) in enumerate(chapter_links, 1):
            chapter_file_path = os.path.join(OUTPUT_DIR, f"{index}.txt")
            
            # KIỂM TRA FILE: Nếu file chương đã tồn tại và không rỗng => Skip
            if os.path.exists(chapter_file_path) and os.path.getsize(chapter_file_path) > 0:
                print(f"\r⏭️  [Skip] Chương {index}/{total_chapters} đã tồn tại, bỏ qua...", end="", flush=True)
                continue

            print(f"\r progress: Đang tải {index}/{total_chapters} - {title}", end="", flush=True)
            
            try:
                content = await crawl_chapter_with_retry(context, url)
                with open(chapter_file_path, "w", encoding="utf-8") as f_out:
                    f_out.write(f"=== {title} ===\n\n{content}")
            except Exception as e:
                print(f"\n⚠️ Lỗi chương {index} ({title}): {e}")
                with open(ERR_CHAPTER_FILE, "a", encoding="utf-8") as f_err:
                    f_err.write(f"Chương {index} | {title} | {url} | Error: {e}\n")
            
            await asyncio.sleep(0.3)

        await browser.close()
        print(f"\n\n🎉 Hoàn thành kiểm tra và tải dữ liệu! Các chương lưu tại thư mục '{OUTPUT_DIR}'.")

if __name__ == "__main__":
    asyncio.run(crawl_novel())