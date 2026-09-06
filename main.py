import sys
from pathlib import Path

# Thêm thư mục gốc vào PYTHONPATH tự động
sys.path.insert(0, str(Path(__file__).resolve().parent))

# Sau đó import bình thường
from src.core.translator import Translator