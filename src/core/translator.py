from src.core.text_processor import TextProcessor

class Translator:
    def __init__(self, dict_loader):
        self.loader = dict_loader

    def translate_with_mapping(self, line):
        """Dịch 1 dòng và trả về danh sách chi tiết từng cụm từ dựa trên RAM cache động"""
        if not line.strip():
            return [], ""
            
        
        # Áp dụng chuẩn hóa dấu câu và dấu phân cách ngay trước khi bắt đầu dịch
        line = TextProcessor.preprocess_raw_line(line)
        line = TextProcessor.normalize_punct(line)

        i = 0
        n = len(line)
        segments = []  # Lưu dạng: [{"src": "游戏", "trans": "Yuya", "type": "Project Name"}, ...]
        max_len = 15

        # Gom nhóm dữ liệu từ RAM cache để phục vụ thuật toán tra cứu nhanh
        # 1. Lấy tất cả từ điển project đang được load trên RAM (is_checked = True)
        active_projects = self.loader.ram_cache.get("projects", {})
        
        # 2. Lấy tất cả từ điển global đang active trên RAM
        active_globals = self.loader.ram_cache.get("global", {})

        while i < n:
            matched = False
            
            for l in range(min(max_len, n - i), 0, -1):
                sub = line[i:i+l]

                # 1. Ưu tiên tra cứu trong các Project Name đang bật
                found_in_project = False
                for proj_name, p_dict in active_projects.items():
                    if sub in p_dict:
                        segments.append({"src": sub, "trans": p_dict[sub].capitalize(), "type": f"Project ({proj_name})"})
                        i += l
                        matched = True
                        found_in_project = True
                        break
                if found_in_project:
                    break

                # 2. Tra cứu trong các từ điển Global (VietPhrase, LuatNhan,...)
                found_in_global = False
                for g_name, g_dict in active_globals.items():
                    if sub in g_dict:
                        # Phân loại hiển thị nhẹ dựa vào tên file global nếu muốn
                        seg_type = "VietPhrase" if "VietPhrase" in g_name else ("Luật Nhân" if "LuatNhan" in g_name else g_name)
                        segments.append({"src": sub, "trans": g_dict[sub], "type": seg_type})
                        i += l
                        matched = True
                        found_in_global = True
                        break
                if found_in_global:
                    break

            if not matched:
                char = line[i]

                # Nếu KHÔNG phải Hán tự (chữ số, dấu =, chữ Latin, khoảng
                # trắng, v.v...) thì gom cả CỤM liên tiếp lại thành 1 segment
                # duy nhất, thay vì xử lý từng ký tự một. Lý do: bên dưới mọi
                # segment đều được nối lại bằng dấu cách (" ".join). Nếu tách
                # từng ký tự, một chuỗi "===" hay "99" vốn dính liền trong
                # nguyên bản sẽ bị chèn dấu cách vào giữa khi ghép lại, ra
                # kết quả sai như "= = =" hoặc "9 9". Gom nguyên cụm giữ cho
                # nó dính liền như bản gốc, còn khoảng cách với từ phía
                # trước/sau vẫn có nhờ dấu cách join giữa các segment.
                if not ('\u4e00' <= char <= '\u9fff'):
                    j = i
                    while j < n and not ('\u4e00' <= line[j] <= '\u9fff'):
                        j += 1
                    run = line[i:j]
                    segments.append({"src": run, "trans": run, "type": "Giữ nguyên (không phải Hán tự)"})
                    i = j
                else:
                    # Fallback sang Hán Việt từ VietPhrase cốt lõi hoặc giữ nguyên ký tự
                    # Giả định lấy ký tự từ file VietPhrase.txt trong global nếu có, không thì giữ nguyên
                    vietphrase_core = active_globals.get("VietPhrase.txt", {})
                    trans_char = vietphrase_core.get(char, char)
                    segments.append({"src": char, "trans": trans_char, "type": "Hán Việt / Dấu câu"})
                    i += 1

        raw_translated = " ".join([s["trans"] for s in segments])
        clean_translated =  TextProcessor.normalize_punct(raw_translated)
        
        return segments, clean_translated

    def translate(self, text):
        lines = text.splitlines()
        translated_lines = []
        for line in lines:
            _, clean = self.translate_with_mapping(line)
            translated_lines.append(clean)
        return "\n".join(translated_lines)