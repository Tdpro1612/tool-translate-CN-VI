import re

class TextProcessor:
    @staticmethod
    def normalize_punct(text):
        """Dọn dẹp khoảng trắng thừa và chuẩn hóa dấu câu Trung - Việt"""
        # 1. Chuyển đổi dấu câu Trung Quốc sang chuẩn Việt/Anh
        punct_map = {
            '，': ',', '。': '.', '！': '!', '？': '?',
            '：': ':', '；': ';', '“': '"', '”': '"',
            '‘': "'", '’': "'", '（': '(', '）': ')',
            '《': '"', '》': '"', '【': '[', '】': ']'
        }
        for cn_p, vi_p in punct_map.items():
            text = text.replace(cn_p, vi_p)

        # 2. Xóa khoảng trắng đứng TRƯỚC các dấu câu: , . ! ? : ; ) ] " '
        text = re.sub(r'\s+([,\.\!\?\:\;\)\]\"\'])', r'\1', text)

        # 3. Xóa khoảng trắng đứng SAU các dấu mở ngoặc: ( [ " '
        text = re.sub(r'([\(\[\"\'])\s+', r'\1', text)

        # 4. Đảm bảo BẮT BUỘC có 1 khoảng trắng SAU các dấu câu , . ! ? : ; (trừ khi ở cuối dòng)
        text = re.sub(r'([,\.\!\?\:\;])([^\s\d\.\,\!\?])', r'\1 \2', text)

        # 5. Gộp nhiều khoảng trắng liên tiếp thành 1 khoảng trắng đơn
        text = re.sub(r' +', ' ', text)

        return text.strip()