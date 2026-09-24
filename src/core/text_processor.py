import re

class TextProcessor:
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
            '·': '-', '「': '"', '」': '"', '『': '"', '』': '"',
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