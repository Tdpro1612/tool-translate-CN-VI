document.addEventListener("DOMContentLoaded", () => {
    loadGlobalDictionaries();
    loadProjectsList();

    // Lắng nghe sự kiện phím tắt toàn cục cho popup
    document.addEventListener("keydown", (e) => {
        if ((e.ctrlKey || e.metaKey) && e.key === 's') {
            const modal = document.getElementById("nameDetailModal");
            if (modal && !modal.classList.contains("hidden")) {
                e.preventDefault();
                saveProjectDetails();
            }
        }
    });

    // Khởi tạo các sự kiện cho popup câu dịch (Sentence Modal)
    initSentenceModalEvents();
    
    // Khởi tạo tương tác click đúp ở ô văn bản gốc
    initTextInteractions();
});

// Biến lưu trữ trạng thái popup
let currentEditingProject = null;
let originalProjectEntriesJson = "";

// ==========================================
// KHỐI 1: GLOBAL DICTIONARIES
// ==========================================

async function loadGlobalDictionaries() {
    try {
        const res = await fetch('/api/dictionaries/global');
        const data = await res.json();
        if (!data.success) throw new Error(data.error);

        const tbody = document.querySelector("#globalTableBody");
        if (!tbody) return;
        tbody.innerHTML = "";

        data.dictionaries.forEach(dict => {
            const tr = document.createElement("tr");
            
            // Kiểm tra xem có phải file cố định không (ví dụ LuatNhan.txt hoặc VietPhrase.txt)
            const isCoreFile = (dict.name === "LuatNhan.txt" || dict.name === "VietPhrase.txt");

            tr.innerHTML = `
                <td>
                    <strong>${dict.name}</strong>
                    <div class="sub-info">${dict.count} entries · ${dict.size} · Priority: ${dict.priority}</div>
                </td>
                <td>
                    ${isCoreFile ? 
                        `<span style="color: #4a5568; font-weight: 500;">${dict.priority} (Cố định)</span>` : 
                        `<select class="form-control" style="width: 120px;" onchange="updatePriority('${dict.name}', this.value)">
                            <option value="15" ${dict.priority === 15 ? 'selected' : ''}>15 - Luật nhân xưng</option>
                            <option value="10" ${dict.priority === 10 ? 'selected' : ''}>10 - VietPhrase</option>
                            <option value="5" ${dict.priority === 5 ? 'selected' : ''}>5 - Hán Việt</option>
                        </select>`
                    }
                </td>
                <td>
                    <button class="btn btn-secondary" onclick="triggerImportGlobal('${dict.name}')">Import Đè</button>
                    ${dict.is_deletable ? `<button class="btn btn-danger" onclick="deleteGlobal('${dict.name}')">Xóa</button>` : ''}
                </td>
            `;
            tbody.appendChild(tr);
        });
    } catch (err) {
        alert("Lỗi tải từ điển Global: " + err.message);
    }
}

async function updatePriority(name, priority) {
    try {
        const res = await fetch('/api/dictionaries/global/priority', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name, priority: parseInt(priority) })
        });
        const data = await res.json();
        if (!data.success) alert("Lỗi cập nhật priority: " + data.error);
    } catch (err) {
        alert("Lỗi kết nối: " + err.message);
    }
}

async function restoreDefaults() {
    if (!confirm("Bạn có chắc chắn muốn khôi phục lại bộ từ điển gốc không?")) return;
    try {
        const res = await fetch('/api/dictionaries/global/restore', { method: 'POST' });
        const data = await res.json();
        if (data.success) {
            loadGlobalDictionaries();
        } else {
            alert("Lỗi: " + data.error);
        }
    } catch (err) {
        alert("Lỗi kết nối: " + err.message);
    }
}

async function deleteGlobal(name) {
    if (!confirm(`Bạn có chắc muốn xóa từ điển ${name}?`)) return;
    try {
        const res = await fetch('/api/dictionaries/global/delete', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name })
        });
        const data = await res.json();
        if (data.success) {
            loadGlobalDictionaries();
        } else {
            alert("Lỗi: " + data.error);
        }
    } catch (err) {
        alert("Lỗi kết nối: " + err.message);
    }
}

function addNewGlobalDict() {
    const input = document.createElement('input');
    input.type = 'file';
    input.accept = '.txt';
    input.onchange = async e => {
        const file = e.target.files[0];
        if (!file) return;
        const formData = new FormData();
        formData.append('file', file);

        try {
            const res = await fetch('/api/dictionaries/global/import', {
                method: 'POST',
                body: formData
            });
            const data = await res.json();
            if (data.success) {
                loadGlobalDictionaries();
            } else {
                alert("Lỗi import: " + data.error);
            }
        } catch (err) {
            alert("Lỗi kết nối: " + err.message);
        }
    };
    input.click();
}

function triggerImportGlobal(name) {
    addNewGlobalDict(); 
}


// ==========================================
// KHỐI 2: NAME MANAGER (PROJECTS)
// ==========================================

async function loadProjectsList() {
    try {
        const res = await fetch('/api/projects/list');
        const data = await res.json();
        if (!data.success) throw new Error(data.error);

        const tbody = document.querySelector("#projectsTableBody");
        if (!tbody) return;
        tbody.innerHTML = "";

        data.projects.forEach(proj => {
            const tr = document.createElement("tr");
            tr.innerHTML = `
                <td>
                    <input type="checkbox" ${proj.is_active ? 'checked' : ''} onchange="toggleProject('${proj.name}', this.checked)">
                </td>
                <td>
                    <a class="name-link" onclick="openProjectDetails('${proj.name}')">${proj.name}</a>
                    <div class="sub-info">${proj.count} entries · ${proj.size} · Priority: 20</div>
                </td>
                <td>
                    <button class="btn btn-danger" onclick="deleteProject('${proj.name}')">Xóa</button>
                </td>
            `;
            tbody.appendChild(tr);
        });
    } catch (err) {
        alert("Lỗi tải danh sách Project: " + err.message);
    }
}

async function toggleProject(name, isActive) {
    try {
        await fetch('/api/projects/toggle', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name, is_active: isActive })
        });
    } catch (err) {
        alert("Lỗi kết nối: " + err.message);
    }
}

async function createNewProject() {
    const name = prompt("Nhập tên file Name mới (ví dụ: nhan_vat.txt):");
    if (!name) return;

    try {
        const res = await fetch('/api/projects/create', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name })
        });
        const data = await res.json();
        if (data.success) {
            loadProjectsList();
        } else {
            alert("Lỗi: " + data.error);
        }
    } catch (err) {
        alert("Lỗi kết nối: " + err.message);
    }
}

async function deleteProject(name) {
    if (!confirm(`Bạn có chắc muốn xóa file Name ${name}?`)) return;
    try {
        const res = await fetch('/api/projects/delete', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name })
        });
        const data = await res.json();
        if (data.success) {
            loadProjectsList();
        } else {
            alert("Lỗi: " + data.error);
        }
    } catch (err) {
        alert("Lỗi kết nối: " + err.message);
    }
}


// ==========================================
// KHỐI 3: POPUP CHI TIẾT FILE NAME & DUPLICATE CHECK
// ==========================================

async function openProjectDetails(projectName) {
    currentEditingProject = projectName;
    const titleEl = document.getElementById("modalTitle");
    if (titleEl) titleEl.innerText = `Quản lý chi tiết: ${projectName}`;
    
    try {
        const res = await fetch(`/api/project/details?name=${encodeURIComponent(projectName)}`);
        const data = await res.json();
        if (!data.success) throw new Error(data.error);

        const sortedEntries = data.entries.sort((a, b) => a.dst.localeCompare(b.dst, 'vi'));
        originalProjectEntriesJson = JSON.stringify(sortedEntries);

        renderPopupTable(sortedEntries);
        const modal = document.getElementById("nameDetailModal");
        if (modal) modal.classList.remove("hidden");
    } catch (err) {
        alert("Không thể tải chi tiết file: " + err.message);
    }
}

// Hàm phụ trợ để escape dấu ngoặc kép tránh vỡ HTML
function escapeHtml(str) {
    if (!str) return '';
    return str.replace(/"/g, '&quot;');
}

function renderPopupTable(entries) {
    const tbody = document.getElementById("popupTableBody");
    if (!tbody) return;
    tbody.innerHTML = "";

    entries.forEach((entry) => {
        const tr = document.createElement("tr");
        tr.innerHTML = `
            <td><input type="text" class="form-control" value="${escapeHtml(entry.src)}" readonly></td>
            <td><input type="text" class="form-control" value="${escapeHtml(entry.dst)}"></td>
            <td><button class="btn btn-danger" onclick="this.closest('tr').remove()">Xóa</button></td>
        `;
        tbody.appendChild(tr);
    });
}

function closeProjectModal() {
    const currentEntries = getCurrentPopupEntries();
    if (JSON.stringify(currentEntries) !== originalProjectEntriesJson) {
        if (!confirm("Bạn có thay đổi chưa được lưu. Bạn có chắc muốn đóng?")) return;
    }
    const modal = document.getElementById("nameDetailModal");
    if (modal) modal.classList.add("hidden");
    currentEditingProject = null;
}

function getCurrentPopupEntries() {
    const rows = document.querySelectorAll("#popupTableBody tr");
    let entries = [];
    rows.forEach(row => {
        const inputs = row.querySelectorAll("input");
        if (inputs.length >= 2) {
            entries.push({ src: inputs[0].value, dst: inputs[1].value });
        }
    });
    return entries;
}

function addNewRowToPopup() {
    const tbody = document.getElementById("popupTableBody");
    if (!tbody) return;
    const tr = document.createElement("tr");
    tr.innerHTML = `
        <td>
            <input type="text" class="form-control new-src-input" placeholder="Nhập tiếng Trung..." onblur="checkDuplicateAndUnlock(this)">
            <div class="error-msg"></div>
        </td>
        <td>
            <input type="text" class="form-control new-dst-input" placeholder="Nghĩa tiếng Việt..." disabled>
        </td>
        <td><button class="btn btn-danger" onclick="this.closest('tr').remove()">Xóa</button></td>
    `;
    tbody.prepend(tr);
    tr.querySelector(".new-src-input").focus();
}

async function checkDuplicateAndUnlock(inputElement) {
    const srcText = inputElement.value.trim();
    const row = inputElement.closest("tr");
    const dstInput = row.querySelector(".new-dst-input");
    const errorDiv = row.querySelector(".error-msg");

    if (!srcText) {
        dstInput.disabled = true;
        errorDiv.innerText = "";
        return;
    }

    try {
        const res = await fetch('/api/project/check-duplicate', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name: currentEditingProject, src: srcText })
        });
        const data = await res.json();

        if (data.exists) {
            errorDiv.innerText = "Cụm từ này đã tồn tại trong file Name!";
            dstInput.disabled = true;
            dstInput.value = "";
        } else {
            errorDiv.innerText = "";
            dstInput.disabled = false;
            dstInput.focus();
        }
    } catch (err) {
        console.error(err);
    }
}

async function saveProjectDetails() {
    const entries = getCurrentPopupEntries();
    try {
        const res = await fetch('/api/project/save-details', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name: currentEditingProject, entries })
        });
        const data = await res.json();
        if (data.success) {
            alert("Lưu thành công!");
            originalProjectEntriesJson = JSON.stringify(entries);
            document.getElementById("nameDetailModal").classList.add("hidden");
            loadProjectsList();
        } else {
            alert("Lỗi khi lưu: " + data.error);
        }
    } catch (err) {
        alert("Lỗi kết nối: " + err.message);
    }
}

function importProjectFile() {
    const input = document.createElement('input');
    input.type = 'file';
    input.accept = '.txt';
    input.onchange = async e => {
        const file = e.target.files[0];
        if (!file) return;
        const formData = new FormData();
        formData.append('file', file);

        try {
            const res = await fetch('/api/projects/import', {
                method: 'POST',
                body: formData
            });
            const data = await res.json();
            if (data.success) {
                loadProjectsList();
            } else {
                alert("Lỗi import project: " + data.error);
            }
        } catch (err) {
            alert("Lỗi kết nối: " + err.message);
        }
    };
    input.click();
}


// ==========================================
// KHỐI 4: SENTENCE EDIT MODAL & SMART PROJECT ROUTING
// ==========================================

let originalSentenceText = "";
let currentSentenceContext = {
    sourceText: "",
    targetText: "",
    existingFileName: null 
};

// Hàm lấy câu hoặc đoạn bôi đen từ textarea
function getSelectedSentenceOrSelection(textarea) {
    const text = textarea.value;
    const start = textarea.selectionStart;
    const end = textarea.selectionEnd;

    if (start !== end) {
        return text.substring(start, end).trim();
    }

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

// Hàm khởi tạo tương tác click đúp ở ô văn bản gốc
function initTextInteractions() {
    const sourceTextarea = document.getElementById("sourceChapterContent");
    if (!sourceTextarea) return;

    sourceTextarea.addEventListener("dblclick", () => {
        const sentence = getSelectedSentenceOrSelection(sourceTextarea);
        if (sentence) {
            openSentenceModal(sentence, "Đang phân tích...");
            fetchSentenceTranslationAndTokens(sentence);
        }
    });
}

// Gọi API phân tích câu sang tokens và hiển thị bản dịch
async function fetchSentenceTranslationAndTokens(sentence) {
    try {
        const res = await fetch('/api/sidebar/analyze', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ sentence })
        });
        const data = await res.json();
        
        if (data.success && data.tokens) {
            const translatedText = data.tokens.map(t => t.dst).join(" ");
            const targetInput = document.getElementById('modalTargetSentence');
            if (targetInput) {
                targetInput.value = translatedText;
                originalSentenceText = translatedText;
            }
            renderModalTokens(data.tokens);
        } else {
            const targetInput = document.getElementById('modalTargetSentence');
            if (targetInput) targetInput.value = "Lỗi phân tích từ điển!";
        }
    } catch (err) {
        console.error("Lỗi kết nối phân tích câu:", err);
    }
}

// Render các dòng token vào popup để sửa nghĩa từng từ
function renderModalTokens(tokens) {
    const container = document.getElementById("modalTokensContainer");
    if (!container) return;
    container.innerHTML = "";

    if (!tokens || tokens.length === 0) {
        container.innerHTML = `<div style="color: #718096; font-size: 13px; text-align: center;">Không có từ nào được bóc tách.</div>`;
        return;
    }

    tokens.forEach(token => {
        const row = document.createElement("div");
        row.className = "token-row";
        row.style.cssText = "display: flex; gap: 8px; margin-bottom: 6px; align-items: center;";
        row.innerHTML = `
            <input type="text" class="form-control" value="${token.src}" readonly style="background: #edf2f7; width: 35%;">
            <input type="text" class="form-control" value="${token.dst}" 
                   data-src="${token.src}" onblur="autoSavePopupWord(this)" style="width: 50%;">
            <span style="font-size: 11px; color: #718096; width: 15%;">[${token.source || 'dict'}]</span>
        `;
        container.appendChild(row);
    });
}

// Tự động lưu nghĩa của từng từ bóc tách khi onblur
async function autoSavePopupWord(inputElement) {
    const src = inputElement.getAttribute("data-src");
    const dst = inputElement.value.trim();
    const targetSelect = document.getElementById('popupTargetFileSelect');
    
    let targetFileName = currentSentenceContext.existingFileName;
    if (!targetFileName && targetSelect) {
        targetFileName = targetSelect.value;
    }

    if (!targetFileName) {
        alert("Vui lòng bật ít nhất 1 file Name ở UI 3 để có chỗ lưu từ!");
        return;
    }

    try {
        await fetch('/api/sidebar/save-word', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ file_name: targetFileName, src, dst })
        });
    } catch (err) {
        console.error("Lỗi auto-save từ trong popup:", err);
    }
}

// Hàm mở popup khi click vào câu
async function openSentenceModal(sourceText, targetText) {
    currentSentenceContext.sourceText = sourceText;
    currentSentenceContext.targetText = targetText;
    originalSentenceText = targetText;
    
    const sourceEl = document.getElementById('modalSourceSentence');
    const targetInput = document.getElementById('modalTargetSentence');
    const saveBtn = document.getElementById('btnSaveSentence');
    const tokensContainer = document.getElementById('modalTokensContainer');

    if (sourceEl) sourceEl.innerText = sourceText;
    if (targetInput) targetInput.value = targetText;
    if (saveBtn) saveBtn.style.display = 'none';
    if (tokensContainer) tokensContainer.innerHTML = '<div style="color: #718096; font-size: 13px; text-align: center;">Đang phân tích từ...</div>';

    // 1. Kiểm tra xem câu/từ này đã thuộc file Name nào đang có sẵn chưa
    currentSentenceContext.existingFileName = null;
    try {
        const checkRes = await fetch('/api/sentence/check-source', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ text: sourceText })
        });
        const checkData = await checkRes.json();
        if (checkData.success && checkData.file_name) {
            currentSentenceContext.existingFileName = checkData.file_name;
        }
    } catch (err) {
        console.error("Không thể check file nguồn của câu:", err);
    }

    // 2. Tải danh sách các file Name đang active (được check ở UI 3) vào dropdown
    await populateActiveProjectsDropdown(currentSentenceContext.existingFileName);

    // 3. Hiển thị overlay popup lên
    const overlay = document.getElementById('sentenceModalOverlay');
    if (overlay) overlay.style.display = 'flex';
}

// Đổ danh sách các Project đang bật vào dropdown chọn nơi lưu
async function populateActiveProjectsDropdown(preferredFile) {
    const select = document.getElementById('popupTargetFileSelect');
    if (!select) return;
    select.innerHTML = "";

    try {
        const res = await fetch('/api/projects/list');
        const data = await res.json();

        if (data.success && data.projects) {
            const activeProjects = data.projects.filter(p => p.is_active);

            if (activeProjects.length === 0) {
                select.innerHTML = `<option value="">-- Chưa bật Project nào (Vào UI 3 để bật) --</option>`;
                select.disabled = true;
                return;
            }

            select.disabled = false;
            activeProjects.forEach(p => {
                const opt = document.createElement('option');
                opt.value = p.name;
                opt.textContent = p.name;
                select.appendChild(opt);
            });

            if (preferredFile && activeProjects.some(p => p.name === preferredFile)) {
                select.value = preferredFile;
            } else if (activeProjects.length === 1) {
                select.value = activeProjects[0].name;
            }
        }
    } catch (err) {
        console.error("Lỗi tải danh sách project active:", err);
    }
}

// Hàm đóng popup
function closeSentenceModal() {
    const overlay = document.getElementById('sentenceModalOverlay');
    if (overlay) overlay.style.display = 'none';
}

// Đăng ký các sự kiện lắng nghe cho Sentence Modal
function initSentenceModalEvents() {
    const targetInput = document.getElementById('modalTargetSentence');
    const saveBtn = document.getElementById('btnSaveSentence');

    if (targetInput) {
        targetInput.addEventListener('input', () => {
            if (targetInput.value !== originalSentenceText) {
                if (saveBtn) saveBtn.style.display = 'inline-block';
            } else {
                if (saveBtn) saveBtn.style.display = 'none';
            }
        });
    }

    const overlay = document.getElementById('sentenceModalOverlay');
    if (overlay) {
        overlay.addEventListener('click', (e) => {
            if (e.target === overlay) {
                closeSentenceModal();
            }
        });
    }

    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') {
            closeSentenceModal();
        }
    });
}

// Hàm xử lý khi bấm nút Save thay đổi câu / từ
async function saveSentenceChange() {
    const newText = document.getElementById('modalTargetSentence').value.trim();
    const targetSelect = document.getElementById('popupTargetFileSelect');
    
    let targetFileName = currentSentenceContext.existingFileName;

    if (!targetFileName) {
        if (!targetSelect || !targetSelect.value) {
            alert("Chưa có file Name nào được bật hoặc được chọn! Vui lòng sang UI 3 bật ít nhất 1 file Name để lưu trữ.");
            return;
        }
        targetFileName = targetSelect.value;
    }

    try {
        const res = await fetch('/api/sentence/save', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                file_name: targetFileName,
                src: currentSentenceContext.sourceText,
                dst: newText
            })
        });
        const data = await res.json();

        if (data.success) {
            alert(`Đã lưu thành công vào file: ${targetFileName}`);
            
            const saveBtn = document.getElementById('btnSaveSentence');
            if (saveBtn) saveBtn.style.display = 'none';
            closeSentenceModal();
            loadProjectsList();
        } else {
            alert("Lỗi khi lưu: " + data.error);
        }
    } catch (err) {
        alert("Lỗi kết nối khi lưu: " + err.message);
    }
}

// Kích hoạt ô nghĩa và nút Lưu khi người dùng gõ từ tiếng Trung
function checkNewWordReady(srcInput) {
    const val = srcInput.value.trim();
    const dstInput = document.getElementById('newWordDstInput');
    const saveBtn = document.getElementById('btnSaveNewWord');
    
    if (val) {
        dstInput.disabled = false;
        dstInput.setAttribute('data-src', val);
        if (dstInput.value.trim()) {
            saveBtn.disabled = false;
        }
    } else {
        dstInput.disabled = true;
        dstInput.value = "";
        dstInput.setAttribute('data-src', "");
        saveBtn.disabled = true;
    }
}

// Lắng nghe khi gõ nghĩa tiếng Việt để bật nút Lưu
document.addEventListener("DOMContentLoaded", () => {
    const dstInput = document.getElementById('newWordDstInput');
    if (dstInput) {
        dstInput.addEventListener('input', () => {
            const saveBtn = document.getElementById('btnSaveNewWord');
            if (dstInput.value.trim() && document.getElementById('newWordSrcInput').value.trim()) {
                saveBtn.disabled = false;
            } else {
                saveBtn.disabled = true;
            }
        });
    }
});

// Hàm bấm nút "Lưu từ" tường minh
async function manualSaveQuickNewWord() {
    const srcInput = document.getElementById('newWordSrcInput');
    const dstInput = document.getElementById('newWordDstInput');
    const targetSelect = document.getElementById('popupTargetFileSelect');

    const src = srcInput.value.trim();
    const dst = dstInput.value.trim();

    if (!src || !dst) {
        alert("Vui lòng điền đủ từ tiếng Trung và nghĩa tiếng Việt!");
        return;
    }

    let targetFileName = currentSentenceContext.existingFileName;
    if (!targetFileName && targetSelect) {
        targetFileName = targetSelect.value;
    }

    if (!targetFileName) {
        alert("Bạn chưa chọn file Name để lưu! Hãy bấm nút '+ Tạo file mới' ở bên dưới trước.");
        return;
    }

    try {
        const res = await fetch('/api/sidebar/save-word', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ file_name: targetFileName, src, dst })
        });
        const data = await res.json();
        
        if (data.success) {
            alert(`Đã lưu thành công từ "${src} -> ${dst}" vào file ${targetFileName}!`);
            
            // Reset trắng các ô nhập để tiếp tục thêm từ khác
            srcInput.value = "";
            dstInput.value = "";
            dstInput.disabled = true;
            dstInput.setAttribute('data-src', "");
            document.getElementById('btnSaveNewWord').disabled = true;
            
            srcInput.focus();
            if (typeof loadProjectsList === 'function') loadProjectsList();
        } else {
            alert("Lỗi lưu từ: " + data.error);
        }
    } catch (err) {
        alert("Lỗi kết nối khi lưu từ mới: " + err.message);
    }
}

// Tính năng tạo nhanh file Name ngay trong popup
async function quickCreateProjectFromModal() {
    const name = prompt("Nhập tên file Name mới cần tạo (ví dụ: nhan_vat.txt):");
    if (!name) return;

    try {
        const res = await fetch('/api/projects/create', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name })
        });
        const data = await res.json();
        
        if (data.success) {
            // Tự động bật (is_active) luôn file vừa tạo
            await fetch('/api/projects/toggle', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ name, is_active: true })
            });

            alert(`Đã tạo và kích hoạt file Name: ${name}`);
            await populateActiveProjectsDropdown(name);
            
            if (typeof loadProjectsList === 'function') loadProjectsList();
        } else {
            alert("Lỗi tạo file: " + data.error);
        }
    } catch (err) {
        alert("Lỗi kết nối: " + err.message);
    }
}