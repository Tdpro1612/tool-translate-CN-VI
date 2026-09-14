import re

class TextProcessor:
    @staticmethod
    def preprocess_raw_line(line):
        """Xử lý và chuẩn hóa dòng tiếng Trung TRƯỚC KHI DỊCH"""
        # Mở rộng regex để bắt cả số Ả Rập (\d), số Hán tự (一二三...), và các dấu gạch (- —)
        pattern = r'第\s*([\d一二三四五六七八九十百千零〇\-\—\–]+)\s*章'
        
        def replace_chapter(match):
            num_part = match.group(1).strip()
            # Nếu bạn muốn giữ nguyên dạng (ví dụ: Chương -, Chương 一) hoặc xử lý tiếp tùy ý
            return f"章{num_part}"

        line = re.sub(pattern, replace_chapter, line)
        return line

    @staticmethod
    def normalize_punct(text):
        """Dọn dẹp khoảng trắng thừa và chuẩn hóa dấu câu sau khi dịch"""
        # (Giữ nguyên toàn bộ code normalize_punct cũ của bạn ở đây)
        punct_map = {
            '，': ',', '。': '.', '！': '!', '？': '?',
            '：': ':', '；': ';', '“': '"', '”': '"',
            '‘': "'", '’': "'", '（': '(', '）': ')',
            '《': '"', '》': '"', '【': '[', '】': ']',
            '、': ',', '…': '...', '—': '-', '～': '~',
        }
        for cn_p, vi_p in punct_map.items():
            text = text.replace(cn_p, vi_p)

        text = re.sub(r'\s+([,\.\!\?\:\;\)\]\"\'])', r'\1', text)
        text = re.sub(r'([\(\[\"\'])\s+', r'\1', text)
        text = re.sub(r'([,\.\!\?\:\;])([^\s\d\.\,\!\?])', r'\1 \2', text)
        text = re.sub(r'([^\s])(["\'])', r'\1 \2', text)
        text = re.sub(r'(["\'])([^\s])', r'\1 \2', text)
        text = re.sub(r' +', ' ', text)

        # Lớp phòng vệ thêm: gộp lại các cụm dấu trang trí bị dịch tách rời
        # kiểu "= = =" -> "===", "* * *" -> "***", "- - -" -> "---"...
        # (phòng khi có nguồn dữ liệu khác không đi qua bản vá trong
        # translator.py mà vẫn tạo ra kiểu tách rời này).
        text = re.sub(
            r'([=\-\*~_#])(?: \1)+',
            lambda m: m.group(1) * (1 + m.group(0).count(' ')),
            text
        )

        return text.strip()