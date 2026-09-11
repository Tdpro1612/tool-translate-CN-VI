from src.core.text_processor import TextProcessor

class Translator:
    def __init__(self, dict_loader):
        self.loader = dict_loader

    def translate_with_mapping(self, line):
        """Dịch 1 dòng và trả về danh sách chi tiết từng cụm từ"""
        if not line.strip():
            return [], ""

        i = 0
        n = len(line)
        segments = []  # Lưu dạng: [{"src": "游戏", "trans": "Yuya", "type": "Project Name"}, ...]
        max_len = 15

        while i < n:
            matched = False
            
            for l in range(min(max_len, n - i), 0, -1):
                sub = line[i:i+l]

                # 1. Project Name
                if sub in self.loader.project_names:
                    segments.append({"src": sub, "trans": self.loader.project_names[sub].capitalize(), "type": "Project Name"})
                    i += l
                    matched = True
                    break
                
                # 2. Global Name
                elif sub in self.loader.global_names:
                    segments.append({"src": sub, "trans": self.loader.global_names[sub].capitalize(), "type": "Global Name"})
                    i += l
                    matched = True
                    break

                # 3. VietPhrase
                elif sub in self.loader.vietphrase:
                    segments.append({"src": sub, "trans": self.loader.vietphrase[sub], "type": "VietPhrase"})
                    i += l
                    matched = True
                    break

            if not matched:
                char = line[i]
                trans_char = self.loader.han_viet.get(char, char)
                segments.append({"src": char, "trans": trans_char, "type": "Hán Việt / Dấu câu"})
                i += 1

        raw_translated = " ".join([s["trans"] for s in segments])
        clean_translated = TextProcessor.normalize_punct(raw_translated)
        
        return segments, clean_translated

    def translate(self, text):
        lines = text.splitlines()
        translated_lines = []
        for line in lines:
            _, clean = self.translate_with_mapping(line)
            translated_lines.append(clean)
        return "\n".join(translated_lines)