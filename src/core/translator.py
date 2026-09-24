from src.core.text_processor import TextProcessor
import time
import re

class Translator:
    def __init__(self, dict_loader):
        self.loader = dict_loader
        self._merged_projects_cache = None
        self._merged_projects_cache_key = None

    def _get_merged_projects(self, active_projects):
        cache_key = id(active_projects)
        if self._merged_projects_cache_key != cache_key:
            merged = {}
            for proj_name, p_dict in active_projects.items():
                for k, v in p_dict.items():
                    if k not in merged:  
                        merged[k] = (v, proj_name)
            self._merged_projects_cache = merged
            self._merged_projects_cache_key = cache_key
        return self._merged_projects_cache

    def _gather_candidate_rules(self, text, pattern_data):
        candidates = list(pattern_data["no_literal"])
        if not text:
            return candidates

        found_literals = pattern_data["automaton"].find_present_keywords(text)
        if not found_literals:
            return candidates

        literal_index = pattern_data["literal_index"]
        seen_ids = set()
        for lit in found_literals:
            bucket = literal_index.get(lit)
            if not bucket:
                continue
            for rule in bucket:
                rid = id(rule)
                if rid in seen_ids:
                    continue
                literal_parts = rule[3]
                if len(literal_parts) == 1 or all(lp in found_literals for lp in literal_parts):
                    seen_ids.add(rid)
                    candidates.append(rule)

        return candidates

    def _translate_recursive(self, text, active_projects, active_globals, pattern_data, depth=0):
        segments = []
        if not text:
            return segments

        if depth < 6 and pattern_data is not None:
            candidate_rules = self._gather_candidate_rules(text, pattern_data)

            best_match = None
            best_rule = None
            for compiled_re, val_template, seg_type, _literal_parts in candidate_rules:
                m = compiled_re.search(text)
                if m is None:
                    continue
                if (best_match is None
                        or m.start() < best_match.start()
                        or (m.start() == best_match.start() and (m.end() - m.start()) > (best_match.end() - best_match.start()))):
                    best_match = m
                    best_rule = (val_template, seg_type)

            if best_match is not None:
                before = text[:best_match.start()]
                after = text[best_match.end():]
                val_template, seg_type = best_rule

                if before:
                    segments.extend(self._translate_recursive(before, active_projects, active_globals, pattern_data, depth + 1))

                def repl(m):
                    gname = f"g{m.group(1)}"
                    raw_captured = best_match.group(gname) or ""
                    sub_segments = self._translate_recursive(raw_captured, active_projects, active_globals, pattern_data, depth + 1)
                    return " ".join(s["trans"] for s in sub_segments)

                translated_value = re.sub(r'\{(\d+)\}', repl, val_template)
                segments.append({"src": best_match.group(0), "trans": translated_value, "type": seg_type})

                if after:
                    segments.extend(self._translate_recursive(after, active_projects, active_globals, pattern_data, depth + 1))

                return segments

        segments.extend(self._tokenize_plain(text, active_projects, active_globals))
        return segments

    def _tokenize_plain(self, line, active_projects, active_globals):
        n = len(line)
        if n == 0:
            return []

        covered = [False] * n
        matched_intervals = []

        merged_projects = self._get_merged_projects(active_projects)
        luat_nhan_dicts = {g_name: g_dict for g_name, g_dict in active_globals.items() if "LuatNhan" in g_name}
        vietphrase_dict = active_globals.get("VietPhrase.txt", {})
        other_globals = {g_name: g_dict for g_name, g_dict in active_globals.items() if g_name != "VietPhrase.txt" and "LuatNhan" not in g_name}

        max_len = 15

        def is_free(start, length):
            return not any(covered[start:start + length])

        # Bước 1: Quét Project
        i = 0
        while i < n:
            if covered[i]:
                i += 1
                continue
            matched = False
            for l in range(min(max_len, n - i), 0, -1):
                if is_free(i, l):
                    sub = line[i:i+l]
                    if sub in merged_projects:
                        trans, proj_name = merged_projects[sub]
                        seg = {"src": sub, "trans": trans, "type": f"Project ({proj_name})"}
                        matched_intervals.append((i, i + l, seg))
                        for idx in range(i, i + l):
                            covered[idx] = True
                        i += l
                        matched = True
                        break
            if not matched:
                i += 1

        # Bước 2: Quét Luật Nhân
        i = 0
        while i < n:
            if covered[i]:
                i += 1
                continue
            matched = False
            for l in range(min(max_len, n - i), 0, -1):
                if is_free(i, l):
                    sub = line[i:i+l]
                    found = False
                    for g_name, g_dict in luat_nhan_dicts.items():
                        if sub in g_dict:
                            seg = {"src": sub, "trans": g_dict[sub], "type": g_name}
                            matched_intervals.append((i, i + l, seg))
                            for idx in range(i, i + l):
                                covered[idx] = True
                            i += l
                            found = True
                            matched = True
                            break
                    if found:
                        break
            if not matched:
                i += 1

        # Bước 3: Quét Global khác và VietPhrase
        i = 0
        while i < n:
            if covered[i]:
                i += 1
                continue
            matched = False
            for l in range(min(max_len, n - i), 0, -1):
                if is_free(i, l):
                    sub = line[i:i+l]
                    found = False
                    for g_name, g_dict in other_globals.items():
                        if sub in g_dict:
                            seg = {"src": sub, "trans": g_dict[sub], "type": g_name}
                            matched_intervals.append((i, i + l, seg))
                            for idx in range(i, i + l):
                                covered[idx] = True
                            i += l
                            found = True
                            matched = True
                            break
                    if found:
                        break

                    if sub in vietphrase_dict:
                        seg = {"src": sub, "trans": vietphrase_dict[sub], "type": "VietPhrase"}
                        matched_intervals.append((i, i + l, seg))
                        for idx in range(i, i + l):
                            covered[idx] = True
                        i += l
                        matched = True
                        break
            if not matched:
                i += 1

        # Bước 4: Xử lý ký tự còn sót lại
        i = 0
        while i < n:
            if covered[i]:
                i += 1
                continue

            j = i
            char = line[i]
            if not ('\u4e00' <= char <= '\u9fff'):
                while j < n and not covered[j] and not ('\u4e00' <= line[j] <= '\u9fff'):
                    j += 1
                run = line[i:j]
                seg = {"src": run, "trans": run, "type": "Giữ nguyên (không phải Hán tự)"}
                matched_intervals.append((i, j, seg))
            else:
                j = i + 1
                char_sub = line[i:j]
                trans_char = vietphrase_dict.get(char_sub, char_sub)
                seg = {"src": char_sub, "trans": trans_char, "type": "Hán Việt / Dấu câu"}
                matched_intervals.append((i, j, seg))

            for idx in range(i, j):
                covered[idx] = True
            i = j

        matched_intervals.sort(key=lambda x: x[0])
        return [item[2] for item in matched_intervals]

    def translate_with_mapping(self, line):
        if not line.strip():
            return [], ""
        
        line = TextProcessor.normalize_punct(line)
        active_projects = self.loader.ram_cache.get("projects", {})
        active_globals = self.loader.ram_cache.get("global", {})
        pattern_rules = self.loader.ram_cache.get("pattern_rules")
        segments = self._translate_recursive(line, active_projects, active_globals, pattern_rules)
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