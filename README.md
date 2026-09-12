translation_tool/
│
├── src/                        # Toàn bộ mã nguồn của ứng dụng
│   ├── core/                   # [Tầng logic] Độc lập hoàn toàn, không dính dáng đến UI
│   │   ├── __init__.py
│   │   ├── dict_loader.py      # Nạp từ điển vào RAM (Hash Map O(1))
│   │   ├── text_processor.py   # Cắt tách đoạn văn, xử lý token
│   │   └── translator.py       # Thuật toán dịch và bóc tách từ vựng
│   │
│   ├── web/                    # [Tầng giao diện] HTML, CSS, JS cho trình duyệt
│   │   ├── static/
│   │   │   ├── css/
│   │   │   │   └── style.css   # Giao diện, bảng bóc tách từ, tối ưu gõ Telex
│   │   │   └── js/
│   │   │       └── app.js      # Xử lý sự kiện, gọi API dịch thuật
│   │   │
│   │   └── templates/
│   │       └── index.html      # Trang giao diện chính
│   │
│   └── server.py               # [Tầng cầu nối] Flask / FastAPI server điều phối
│
├── dicts/                      # [Kho dữ liệu tĩnh] Chứa file VietPhrase, Names, Luật Nhân
│   ├── VietPhrase.txt
│   └── Names.txt
│
├── projects/                   # Thư mục lưu file truyện gốc và bản dịch
│
├── main.py                     # [File khởi chạy chính] Gọi server.py để bật web server cục bộ
├── requirements.txt            # Danh sách thư viện (Flask/FastAPI, uvicorn, v.v.)
└── README.md