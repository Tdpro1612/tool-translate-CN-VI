tool-translate-CN-VI/
├── dicts/                          # THƯ MỤC CHỨA TẤT CẢ TỪ ĐIỂN
│   ├── global/                     # Data dùng chung (Luôn nạp khi mở App)
│   │   ├── VietPhrase.txt          # Từ điển VietPhrase chính
│   │   ├── LuatNhan.txt            # Luật nhân xưng, ngữ cảnh
│   │   ├── HanViet.txt             # Âm Hán Việt đơn từ (Fallback cuối)
│   │   └── Names_Global.txt        # Tên chung (Tông môn, xưng hô, địa danh phổ biến)
│   │
│   └── projects/                   # Data riêng từng bộ truyện (Chỉ nạp khi chọn)
│       ├── DauLaDaiLuc.txt         # Name riêng truyện Đấu La Đại Lục
│       ├── ToanChucCaoThu.txt      # Name riêng truyện Toàn Chức Cao Thủ
│       └── Untitled_Project.txt    # Name riêng mặc định khi chưa chọn dự án
│
├── src/                            # MÃ NGUỒN CHÍNH CỦA TOOL
│   ├── __init__.py
│   │
│   ├── core/                       # ENGINE XỬ LÝ LOGIC DỊCH THUẬT
│   │   ├── __init__.py
│   │   ├── dict_loader.py          # Quản lý đọc/nạp file từ điển (Global & Projects)
│   │   ├── translator.py           # Thuật toán dịch Max Matching (Ưu tiên đè Name)
│   │   └── text_processor.py       # Xử lý dấu câu, viết hoa, xóa khoảng trắng thừa
│   │
│   ├── ui/                         # GIAO DIỆN NGƯỜI DÙNG (PyQt6 / CustomTkinter)
│   │   ├── __init__.py
│   │   ├── main_window.py          # Màn hình chính (Khung dịch 2 bên, chọn Dự án)
│   │   ├── dialog_add_name.py      # Popup "Thêm Name Nhanh" (Lưu vào dự án đang chọn)
│   │   └── dialog_dict_manager.py  # Cửa sổ quản lý / chỉnh sửa file từ điển
│   │
│   └── utils/                      # TIỆN ÍCH PHỤ TRỢ
│       ├── __init__.py
│       └── config_manager.py       # Lưu cài đặt người dùng (Đường dẫn từ điển, Font,...)
│
├── tests/                          # CODE KIỂM THỬ TỰ ĐỘNG
│   └── test_translation.py         # Test thử thuật toán dịch và độ ưu tiên Name
│
├── .gitignore                      # Khai báo các file KHÔNG đưa lên Git
├── main.py                         # File chạy chính khởi động ứng dụng (Entry Point)
├── README.md                       # Hướng dẫn cài đặt và sử dụng tool
└── requirements.txt                # Khai báo thư viện (PyQt6, v.v.)