document.addEventListener("DOMContentLoaded", () => {
    initTextInteractions();
});

// 1. Tương tác bắt sự kiện click đúp để phân tích câu đưa sang Sidebar[cite: 5, 8]
function initTextInteractions() {
    const sourceTextarea = document.getElementById("sourceChapterContent");

    sourceTextarea.addEventListener("dblclick", () => {
        const sentence = getSelectedSentenceOrSelection(sourceTextarea);
        if (sentence) {
            openSidebarWithSentence(sentence);
        }
    });
}

function getSelectedSentenceOrSelection(textarea) {
    const text = textarea.value;
    const start = textarea.selectionStart;
    const end = textarea.selectionEnd;

    // Nếu người dùng bôi đen một đoạn ngắn[cite: 5, 8]
    if (start !== end) {
        return text.substring(start, end).trim();
    }

    // Nếu chỉ click đúp tại 1 điểm, tự động quét trọn vẹn câu dựa theo dấu ngắt câu[cite: 5, 8]
    let left = start;
    let right = start;
    const puncts = ['。', '！', '？', '\n', '.', '!', '?'];

    while (left > 0 && !puncts.includes(text[left - 1])) {
        left--;
    }
    while (right < text.length && !puncts.includes(text[right])) {
        right++;
    }

    return text.substring(left, right).trim();
}

async function openSidebarWithSentence(sentence) {
    document.getElementById("sidebarOriginalSentence").innerText = sentence;

    try {
        const res = await fetch('/api/sidebar/analyze', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ sentence })
        });
        const data = await res.json();
        
        if (data.success) {
            renderSidebarTokens(data.tokens);
            // Gán hiển thị nhanh toàn bộ bản dịch câu hoàn chỉnh nếu cần
            document.getElementById("sidebarTranslatedSentence").innerText = data.tokens.map(t => t.dst).join(" ");
        } else {
            alert("Lỗi phân tích: " + data.error);
        }
    } catch (err) {
        console.error("Lỗi kết nối:", err);
    }
}

function renderSidebarTokens(tokens) {
    const container = document.getElementById("sidebarTokensContainer");
    container.innerHTML = "";

    tokens.forEach(token => {
        const row = document.createElement("div");
        row.className = "token-row";
        row.innerHTML = `
            <input type="text" class="token-input" value="${token.src}" readonly>
            <input type="text" class="token-input" value="${token.dst}" 
                   data-src="${token.src}" onblur="autoSaveWord(this)">
            <span class="source-badge">[${token.source}]</span>
        `;
        container.appendChild(row);
    });
}

// 2. Cơ chế Auto-save on blur khi chỉnh sửa nghĩa ở Sidebar[cite: 5, 8]
async function autoSaveWord(inputElement) {
    const src = inputElement.getAttribute("data-src");
    const dst = inputElement.value.trim();
    const targetFile = document.getElementById("targetProjectSelect").value; // File Name mục tiêu chọn sẵn

    if (!targetFile) {
        alert("Chưa chọn file Name mục tiêu để lưu từ[cite: 5, 8]!");
        return;
    }

    try {
        await fetch('/api/sidebar/save-word', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ file_name: targetFile, src, dst })
        });
    } catch (err) {
        console.error("Lỗi auto-save từ:", err);
    }
}

// 3. Thực hiện dịch thủ công toàn bộ chương[cite: 5, 8]
async function handleManualTranslate() {
    const content = document.getElementById("sourceChapterContent").value;
    try {
        const res = await fetch('/api/translate', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ content })
        });
        const data = await res.json();
        
        if (data.success) {
            document.getElementById("targetChapterContent").innerText = data.translated_content;
        } else {
            alert("Lỗi dịch: " + data.error);
        }
    } catch (err) {
        alert("Lỗi kết nối: " + err.message);
    }
}

// 4. Thêm nhanh thủ công 1 cặp từ mới ở đáy Sidebar[cite: 5, 8]
async function handleQuickAddWord() {
    const src = document.getElementById("quickAddSrc").value.trim();
    const dst = document.getElementById("quickAddDst").value.trim();
    const targetFile = document.getElementById("targetProjectSelect").value;

    if (!targetFile) {
        alert("Vui lòng chọn file Name mục tiêu ở thanh công cụ trước[cite: 5, 8]!");
        return;
    }
    if (!src || !dst) {
        alert("Vui lòng điền đủ Hán tự và Nghĩa tiếng Việt!");
        return;
    }

    try {
        const res = await fetch('/api/sidebar/save-word', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ file_name: targetFile, src, dst })
        });
        const data = await res.json();
        
        if (data.success) {
            alert("Thêm từ mới thành công!");
            document.getElementById("quickAddSrc").value = "";
            document.getElementById("quickAddDst").value = "";
        } else {
            alert("Lỗi: " + data.error);
        }
    } catch (err) {
        alert("Lỗi kết nối: " + err.message);
    }
}