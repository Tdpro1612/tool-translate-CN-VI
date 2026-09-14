# -*- coding: utf-8 -*-
"""
Module dùng chung để tạo file EPUB từ văn bản thuần đã dịch.
Được tách riêng để cả script chạy tay (txt_to_epub.py) và API web
(api_translate_and_export_epub_file.py) đều dùng chung 1 logic, tránh
lặp code và tránh sửa 1 nơi quên sửa nơi kia.
"""
import os
import re
import uuid
import html
from ebooklib import epub

# Marker chương: dấu "=" lặp lại >= 2 lần, CHO PHÉP có khoảng trắng xen giữa
# từng dấu "=" (thực tế gặp cả 2 kiểu: "===" liền nhau lẫn "= = =" cách nhau
# bởi dấu cách). (?:=[ \t]*){2,} khớp cả hai.
_MARKER = r'(?:=[ \t]*){2,}'

# Nhận diện tiêu đề chương dạng: === Chương 1: ABC ===  hoặc  = = = Chương 1 = = =
# - QUAN TRỌNG: KHÔNG bắt buộc "=== ... ===" nằm trên cùng 1 dòng, vì có file
#   trải tiêu đề trên 3 dòng riêng (===, tên chương, ===). \s* ở 2 đầu title
#   (bao gồm cả xuống dòng) cho phép khớp cả kiểu 1 dòng lẫn kiểu 3 dòng.
#   (.*?) không DOTALL nên bản thân tiêu đề vẫn chỉ nằm trên 1 dòng, tránh
#   nuốt nhầm cả đoạn văn phía sau nếu file không chia chương theo kiểu này.
# - Dùng finditer + vị trí (start/end) thay vì re.split + đếm index thủ công
#   (cách cũ dễ lệch mảng nếu có dòng trống/định dạng lạ ở đầu file).
CHAPTER_PATTERN = re.compile(_MARKER + r'\s*(.*?)\s*' + _MARKER)

# Fallback khi không tìm thấy (đủ) marker "=": tách theo các dòng có chứa
# chữ "chương" + số, phòng trường hợp 1 số chương trong sách không được bọc
# dấu "=" đúng chuẩn (lỗi dịch/nguồn không đồng nhất).
FALLBACK_CHAPTER_PATTERN = re.compile(
    r'^[^\n]*ch\u01b0\u01a1ng\s*\d+[^\n]*$', re.IGNORECASE | re.MULTILINE
)

CSS_CONTENT = '''
    body { font-family: sans-serif; line-height: 1.6; padding: 5px; }
    h2 { text-align: center; font-size: 1.4em; color: #333; margin-top: 1em; margin-bottom: 1em; }
    p { text-indent: 1.5em; margin-top: 0; margin-bottom: 0.8em; text-align: justify; }
'''


def _chapters_from_matches(matches, content, clean_title):
    chapters = []
    for idx, m in enumerate(matches):
        title = clean_title(m)
        start = m.end()
        end = matches[idx + 1].start() if idx + 1 < len(matches) else len(content)
        body = content[start:end].strip()
        # Bỏ qua các "chương" rỗng hoàn toàn (không tiêu đề, không nội dung)
        if not title and not body:
            continue
        chapters.append((title, body))
    return chapters


def _split_chapters(content):
    """
    Tách nội dung thành list[(tiêu_đề, nội_dung)].
    Thử lần lượt 2 kiểu nhận diện, dùng kết quả đầu tiên tách ra được từ
    2 chương trở lên:
      1) Marker "=" (=== hoặc = = =, có/không trải nhiều dòng).
      2) Dòng chứa "chương <số>" (dự phòng khi marker "=" không nhất quán).
    Trả về [] nếu không tách được (file không có định dạng chia chương).
    """
    by_marker = _chapters_from_matches(
        list(CHAPTER_PATTERN.finditer(content)), content,
        clean_title=lambda m: m.group(1).strip()
    )
    if len(by_marker) >= 2:
        return by_marker

    by_fallback = _chapters_from_matches(
        list(FALLBACK_CHAPTER_PATTERN.finditer(content)), content,
        clean_title=lambda m: m.group(0).strip(" \t=-_*")
    )
    if len(by_fallback) >= 2:
        return by_fallback

    # Không kiểu nào tách được >= 2 chương -> ưu tiên trả kết quả của marker
    # "=" (có thể là [] hoặc đúng 1 chương), để build_epub tự lo nhánh gộp 1
    # chương duy nhất.
    return by_marker


def _body_to_html(body_text):
    """
    Chuyển nội dung 1 chương thành các thẻ <p>, escape ký tự đặc biệt
    (&, <, >, ...) để không làm hỏng cấu trúc XHTML nếu văn bản gốc chứa
    các ký tự đó (lỗi có trong bản gốc: nối thẳng text vào HTML không escape).
    Giữ nguyên logic "mỗi dòng là 1 đoạn" như bản gốc.
    """
    parts = []
    for line in body_text.splitlines():
        line_clean = line.strip()
        if line_clean and not line_clean.startswith("==="):
            parts.append(f"<p>{html.escape(line_clean)}</p>")
    return "\n".join(parts)


def build_epub(content, output_path, title="Truyện Dịch", author="Unknown",
                language="vi", cover_path=None):
    """
    Tạo file EPUB từ văn bản thuần.

    Args:
        content: Toàn bộ nội dung file txt (str).
        output_path: Đường dẫn file .epub sẽ ghi ra.
        title: Tên sách.
        author: Tác giả (có thể để trống).
        language: Mã ngôn ngữ ISO, mặc định 'vi'.
        cover_path: Đường dẫn ảnh bìa (jpg/png), tuỳ chọn.

    Returns:
        int: số chương đã đóng gói.

    Raises:
        ValueError: nếu nội dung rỗng.
    """
    if not content or not content.strip():
        raise ValueError("Nội dung rỗng, không thể tạo EPUB.")

    # Chuẩn hoá xuống dòng kiểu Windows (\r\n) / Mac cũ (\r) về \n để việc
    # nhận diện \s* quanh dấu === không bị lệch vì ký tự \r thừa.
    content = content.replace('\r\n', '\n').replace('\r', '\n')

    book = epub.EpubBook()
    # Dùng uuid thay vì dựa vào tên file để tránh trùng identifier giữa
    # các lần dịch lại / các file trùng tên.
    book.set_identifier(f"urn:uuid:{uuid.uuid4()}")
    book.set_title(title)
    book.set_language(language)
    if author:
        book.add_author(author)

    if cover_path and os.path.exists(cover_path):
        with open(cover_path, 'rb') as f:
            book.set_cover("cover.jpg", f.read())

    css_item = epub.EpubItem(
        uid="style_nav", file_name="style/nav.css",
        media_type="text/css", content=CSS_CONTENT,
    )
    book.add_item(css_item)

    spine = ["nav"]
    toc = []

    chapters = _split_chapters(content)
    if not chapters:
        # Không có định dạng === -> gom toàn bộ vào 1 chương để không lỗi
        chapters = [("", content)]

    chapter_count = 0
    for chap_title, body_text in chapters:
        chapter_count += 1
        heading = html.escape(chap_title) if chap_title else f"Chương {chapter_count}"
        html_body = f"<h2>{heading}</h2>\n" + _body_to_html(body_text)

        chap_item = epub.EpubHtml(
            title=chap_title or f"Chương {chapter_count}",
            file_name=f"chap_{chapter_count}.xhtml",
            lang=language,
        )
        chap_item.content = html_body
        chap_item.add_item(css_item)

        book.add_item(chap_item)
        toc.append(chap_item)
        spine.append(chap_item)

    book.toc = toc
    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())
    book.spine = spine

    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    epub.write_epub(output_path, book, {})
    return chapter_count