let currentFileId = null;

// Khi người dùng bấm nút "Bắt Đầu Dịch"
document.getElementById('btnTranslateFile').addEventListener('click', async () => {
    const fileInput = document.getElementById('batchFile');
    if (fileInput.files.length === 0) {
        alert("Vui lòng chọn một file .txt trước!");
        return;
    }

    const formData = new FormData();
    formData.append('file', fileInput.files[0]);

    const progressContainer = document.getElementById('progressContainer');
    const progressBar = document.getElementById('progressBar');

    progressContainer.classList.remove('d-none');
    progressBar.style.width = '0%';
    progressBar.innerText = 'Đang khởi tạo tiến trình dịch...';

    try {
        // 1. Gửi request bắt đầu dịch ngầm
        const res = await fetch('/api/translate-file', {
            method: 'POST',
            body: formData
        });
        const data = await res.json();

        if (!data.success) {
            alert("Lỗi: " + data.error);
            progressContainer.classList.add('d-none');
            return;
        }

        const taskId = data.task_id;
        const totalLines = data.total_lines;

        // 2. Dùng setInterval để kiểm tra tiến độ mỗi 500ms
        const intervalId = setInterval(async () => {
            try {
                const progressRes = await fetch(`/api/translate-progress?task_id=${taskId}`);
                const progressData = await progressRes.json();

                if (progressData.success) {
                    const current = progressData.current;
                    const percent = Math.round((current / totalLines) * 100);

                    // Cập nhật thanh progress bar chạy thực tế
                    progressBar.style.width = percent + '%';
                    progressBar.innerText = `Đang dịch: ${current} / ${totalLines} dòng (${percent}%)`;

                    if (progressData.status === 'completed') {
                        clearInterval(intervalId);
                        window.currentFilePath = progressData.file_path;
                        progressBar.innerText = `Đã dịch xong ${totalLines} dòng!`;
                        
                        document.getElementById('resultActions').classList.remove('d-none');
                        document.getElementById('btnDownloadTxt').href = progressData.download_txt_url;
                    } else if (progressData.status === 'error') {
                        clearInterval(intervalId);
                        alert("Lỗi trong quá trình dịch: " + progressData.error);
                        progressContainer.classList.add('d-none');
                    }
                }
            } catch (err) {
                console.error("Lỗi khi kiểm tra tiến độ:", err);
            }
        }, 500);

    } catch (err) {
        alert("Lỗi kết nối: " + err.message);
        progressContainer.classList.add('d-none');
    }
});

// Xử lý bật/tắt popup EPUB
document.getElementById('btnOpenEpubModal').addEventListener('click', () => {
    document.getElementById('epubModal').classList.remove('d-none');
});

document.getElementById('btnCloseModal').addEventListener('click', () => {
    document.getElementById('epubModal').classList.add('d-none');
});

// Gửi yêu cầu tạo EPUB khi người dùng nhập xong thông tin trên popup
document.getElementById('btnSubmitEpub').addEventListener('click', async () => {
    const title = document.getElementById('epubTitle').value.trim();
    const author = document.getElementById('epubAuthor').value.trim();

    if (!title) {
        alert("Vui lòng nhập tên sách!");
        return;
    }

    try {
        const res = await fetch('/api/export-epub', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ 
                file_path: window.currentFilePath, // Sửa từ currentFileId thành window.currentFilePath
                title: document.getElementById('epubTitle').value, 
                author: document.getElementById('epubAuthor').value 
            })
        });
        const data = await res.json();

        if (data.success) {
            alert("Tạo file EPUB thành công!");
            document.getElementById('epubModal').classList.add('d-none');
            // Tự động tải file EPUB về
            window.location.href = data.download_epub_url;
        } else {
            alert("Lỗi tạo EPUB: " + data.error);
        }
    } catch (err) {
        alert("Lỗi kết nối: " + err.message);
    }
});
