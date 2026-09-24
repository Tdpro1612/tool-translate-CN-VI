```
translation_tool/
│
│── .gitignore
├── README.md
├── constants.py
├── danh_sach_chuong.txt
├── dicts
│   ├── default_data
│   │   ├── dictionary
│   │   │   ├── Han_Viet.txt
│   │   │   ├── LuatNhan.txt
│   │   │   └── VietPhrase.txt
│   │   └── names
│   │       ├── names_harry_potter.txt
│   │       └── names_yugioh_full_card.txt
│   ├── dict_action.json
│   ├── global
│   │   ├── Han_Viet.txt
│   │   ├── LuatNhan.txt
│   │   └── VietPhrase.txt
│   └── projects
│       ├── name_call_yugioh.txt
│       ├── name_card_yugioh_global.txt
│       ├── names_harry_potter.txt
│       └── names_yugioh_full_card.txt
├── main.py
├── requirements.txt
├── src
│   ├── __init__.py
│   ├── core
│   │   ├── Epub_builder.py
│   │   ├── __init__.py
│   │   ├── dict_loader.py
│   │   ├── text_processor.py
│   │   └── translator.py
│   └── ui
│       ├── api
│       │   ├── api_import_export_dictionary.py
│       │   ├── api_translate_and_export_epub_file.py
│       │   └── api_translate_chapter.py
│       ├── index.html
│       ├── main_window.py
│       └── static
│           ├── css
│           │   ├── import_export_dictionary.css
│           │   ├── translate_and_export_epub_file.css
│           │   └── translate_chapter.css
│           └── js
│               ├── import_export_dictionary.js
│               ├── translate_and_export_epub_file.js
│               └── translate_chapter.js
├── test_translation.py
├── tests
│   ├── __init__.py
│   └── test_translation.py
└── track_err.py