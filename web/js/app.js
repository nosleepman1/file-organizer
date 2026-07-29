let currentActions = [];
let selectedActionIndices = new Set();
let categoryChart = null;
let currentRules = {};

document.addEventListener('DOMContentLoaded', () => {
    initTheme();
    initDefaultPath();
    setupEventListeners();
    initChart();
    runScan();
    fetchHistory();
    fetchRules();
    checkWatcherStatus();
});

// --------------------------------------------------------------------------
// Theme Switcher System
// --------------------------------------------------------------------------
function initTheme() {
    const savedTheme = localStorage.getItem('sfo_theme') || 'dark';
    setTheme(savedTheme);
    const select = document.getElementById('themeSelect');
    if (select) select.value = savedTheme;
}

function setTheme(theme) {
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem('sfo_theme', theme);
}

// --------------------------------------------------------------------------
// Default Folder & Event Listeners
// --------------------------------------------------------------------------
function initDefaultPath() {
    const input = document.getElementById('targetDirInput');
    if (!input.value) {
        input.value = "DOWNLOADS";
    }
}

function setupEventListeners() {
    // Theme switch
    document.getElementById('themeSelect').addEventListener('change', (e) => {
        setTheme(e.target.value);
    });

    // Scan button
    document.getElementById('btnScan').addEventListener('click', runScan);

    // Execute button
    document.getElementById('btnExecute').addEventListener('click', runExecute);

    // Undo button
    document.getElementById('btnUndo').addEventListener('click', () => runUndo());

    // Presets
    document.querySelectorAll('.btn-preset').forEach(btn => {
        btn.addEventListener('click', (e) => {
            const path = e.currentTarget.getAttribute('data-path');
            document.getElementById('targetDirInput').value = path;
            runScan();
        });
    });

    // Watcher Toggle
    document.getElementById('toggleWatcher').addEventListener('change', (e) => {
        toggleWatcher(e.target.checked);
    });

    // Sort Mode Select & Recursive Toggle
    document.getElementById('sortModeSelect').addEventListener('change', runScan);
    document.getElementById('toggleRecursive').addEventListener('change', runScan);

    // Tabs Navigation
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
            document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
            document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));

            const tabId = e.currentTarget.getAttribute('data-tab');
            e.currentTarget.classList.add('active');
            document.getElementById(tabId).classList.add('active');
        });
    });

    // Search and Category Filter
    document.getElementById('searchInput').addEventListener('input', renderPreviewTable);
    document.getElementById('categoryFilter').addEventListener('change', renderPreviewTable);

    // Select All Checkbox
    document.getElementById('selectAllCheckbox').addEventListener('change', (e) => {
        const isChecked = e.target.checked;
        const rows = document.querySelectorAll('.preview-row-checkbox');
        rows.forEach(cb => {
            cb.checked = isChecked;
            const idx = parseInt(cb.getAttribute('data-index'));
            if (isChecked) {
                selectedActionIndices.add(idx);
            } else {
                selectedActionIndices.delete(idx);
            }
        });
        updateSelectionCounters();
    });

    // Duplicates tab
    document.getElementById('btnScanDuplicates').addEventListener('click', runScanDuplicates);
    document.getElementById('btnDeleteSelectedDuplicates').addEventListener('click', runDeleteDuplicates);

    // Rename tab
    document.getElementById('btnApplyRename').addEventListener('click', runApplyRename);

    // Rules tab
    document.getElementById('btnSaveRules').addEventListener('click', runSaveRules);
    document.getElementById('btnAddCategoryBtn').addEventListener('click', promptAddCategory);
}

// --------------------------------------------------------------------------
// Scan & Preview
// --------------------------------------------------------------------------
async function runScan() {
    const targetDir = document.getElementById('targetDirInput').value.trim();
    const mode = document.getElementById('sortModeSelect').value;
    const recursive = document.getElementById('toggleRecursive').checked;

    if (!targetDir) {
        showToast("⚠️ Veuillez spécifier un dossier.", "warning");
        return;
    }

    showToast("🔍 Analyse du dossier en cours...", "info");

    try {
        const response = await fetch('/api/scan', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ target_dir: targetDir, mode: mode, recursive: recursive })
        });

        const data = await response.json();

        if (!data.success) {
            showToast(`❌ Erreur: ${data.message}`, "error");
            return;
        }

        currentActions = data.actions || [];
        selectedActionIndices = new Set(currentActions.map((_, i) => i));

        updateCategoryFilterOptions();
        updateUIWithScanResults(data);
        showToast(`✅ Analyse terminée (${currentActions.length} actions détectées).`, "success");

    } catch (err) {
        showToast(`❌ Erreur de communication serveur: ${err.message}`, "error");
    }
}

function updateCategoryFilterOptions() {
    const select = document.getElementById('categoryFilter');
    const categories = Array.from(new Set(currentActions.map(a => a.category)));
    
    select.innerHTML = `<option value="">Toutes les catégories (${categories.length})</option>` +
        categories.map(cat => `<option value="${escapeHtml(cat)}">${escapeHtml(cat)}</option>`).join('');
}

function updateUIWithScanResults(data) {
    const stats = data.stats || {};
    document.getElementById('kpiTotalFiles').innerText = stats.total_files || 0;
    document.getElementById('kpiTotalSize').innerText = stats.total_size_formatted || "0 B";
    document.getElementById('previewCount').innerText = currentActions.length;

    renderPreviewTable();
    updateChart(stats.categories || []);
}

function renderPreviewTable() {
    const tbody = document.getElementById('previewTableBody');
    const search = document.getElementById('searchInput').value.toLowerCase();
    const categoryFilter = document.getElementById('categoryFilter').value;

    const filteredActions = currentActions.filter((action, index) => {
        const matchSearch = action.file_name.toLowerCase().includes(search) || action.destination.toLowerCase().includes(search);
        const matchCat = !categoryFilter || action.category === categoryFilter;
        return matchSearch && matchCat;
    });

    if (filteredActions.length === 0) {
        tbody.innerHTML = `
            <tr class="empty-row">
                <td colspan="5">
                    <div class="empty-state">
                        <i class="ri-checkbox-circle-line"></i>
                        <p>Aucun fichier à trier pour ces critères.</p>
                    </div>
                </td>
            </tr>
        `;
    } else {
        tbody.innerHTML = filteredActions.map((action) => {
            const originalIndex = currentActions.indexOf(action);
            const isChecked = selectedActionIndices.has(originalIndex);
            return `
                <tr>
                    <td>
                        <input type="checkbox" class="preview-row-checkbox" data-index="${originalIndex}" ${isChecked ? 'checked' : ''} onchange="toggleActionSelection(${originalIndex}, this.checked)">
                    </td>
                    <td><strong>${escapeHtml(action.file_name)}</strong></td>
                    <td><span class="badge-category">${escapeHtml(action.category)}</span></td>
                    <td>${action.size_formatted}</td>
                    <td class="path-text">${escapeHtml(action.destination)}</td>
                </tr>
            `;
        }).join('');
    }

    updateSelectionCounters();
}

function toggleActionSelection(index, checked) {
    if (checked) {
        selectedActionIndices.add(index);
    } else {
        selectedActionIndices.delete(index);
    }
    updateSelectionCounters();
}

function updateSelectionCounters() {
    const count = selectedActionIndices.size;
    document.getElementById('kpiActionsCount').innerText = count;
    document.getElementById('executeSelectedCount').innerText = count;
    document.getElementById('selectedCountBadge').innerText = `${count} sélectionné(s)`;
    document.getElementById('btnExecute').disabled = (count === 0);
}

// --------------------------------------------------------------------------
// Execute & Undo
// --------------------------------------------------------------------------
async function runExecute() {
    const targetDir = document.getElementById('targetDirInput').value.trim();

    const selectedActions = currentActions.filter((_, i) => selectedActionIndices.has(i));
    if (selectedActions.length === 0) {
        showToast("⚠️ Aucune action sélectionnée.", "warning");
        return;
    }

    showToast("🚀 Organisation en cours...", "info");

    try {
        const response = await fetch('/api/organize', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ target_dir: targetDir, actions: selectedActions })
        });

        const data = await response.json();

        if (data.success) {
            showToast(`🎉 ${data.message}`, "success");
            runScan();
            fetchHistory();
        } else {
            showToast(`❌ ${data.message}`, "error");
        }
    } catch (err) {
        showToast(`❌ Erreur lors du tri: ${err.message}`, "error");
    }
}

async function runUndo(batchId = null) {
    const targetDir = document.getElementById('targetDirInput').value.trim();

    try {
        const response = await fetch('/api/undo', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ target_dir: targetDir, batch_id: batchId })
        });

        const data = await response.json();

        if (data.success) {
            showToast(`↩️ ${data.message}`, "success");
            runScan();
            fetchHistory();
        } else {
            showToast(`⚠️ ${data.message}`, "warning");
        }
    } catch (err) {
        showToast(`❌ Erreur lors de l'annulation: ${err.message}`, "error");
    }
}

// --------------------------------------------------------------------------
// Duplicates Finder
// --------------------------------------------------------------------------
async function runScanDuplicates() {
    const targetDir = document.getElementById('targetDirInput').value.trim();
    const recursive = document.getElementById('toggleRecursive').checked;

    showToast("🔎 Analyse des doublons par hash SHA256...", "info");

    try {
        const response = await fetch('/api/duplicates', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ target_dir: targetDir, recursive: recursive })
        });

        const data = await response.json();
        if (!data.success) {
            showToast(`❌ Erreur: ${data.message}`, "error");
            return;
        }

        renderDuplicates(data.groups || []);
    } catch (err) {
        showToast(`❌ Erreur scan doublons: ${err.message}`, "error");
    }
}

function renderDuplicates(groups) {
    const container = document.getElementById('duplicatesList');
    const banner = document.getElementById('duplicateStatsBanner');

    if (groups.length === 0) {
        banner.classList.add('hidden');
        container.innerHTML = `
            <div class="empty-state">
                <i class="ri-checkbox-circle-line"></i>
                <p>Aucun doublon binaire exact détecté dans ce dossier !</p>
            </div>
        `;
        return;
    }

    let totalWastedBytes = 0;
    groups.forEach(g => totalWastedBytes += g.wasted_bytes);

    document.getElementById('dupGroupsCount').innerText = groups.length;
    document.getElementById('dupWastedSpace').innerText = formatSize(totalWastedBytes);
    banner.classList.remove('hidden');

    container.innerHTML = groups.map((g, groupIdx) => `
        <div class="duplicate-group-card">
            <div class="group-header">
                <span><i class="ri-fingerprint-line"></i> Groupe #${g.hash} (${g.count} fichiers identiques - ${g.size_formatted} chacun)</span>
                <span class="badge-info">Gâchis: ${g.wasted_formatted}</span>
            </div>
            ${g.files.map((file, fileIdx) => `
                <div class="duplicate-file-row">
                    <input type="checkbox" class="duplicate-checkbox" data-path="${escapeHtml(file.path)}" ${fileIdx > 0 ? 'checked' : ''} onchange="updateSelectedDuplicatesCount()">
                    <strong>${escapeHtml(file.file_name)}</strong>
                    <span class="path-text">(${escapeHtml(file.path)})</span>
                </div>
            `).join('')}
        </div>
    `).join('');

    updateSelectedDuplicatesCount();
}

function updateSelectedDuplicatesCount() {
    const selected = document.querySelectorAll('.duplicate-checkbox:checked');
    const btn = document.getElementById('btnDeleteSelectedDuplicates');
    btn.disabled = (selected.length === 0);
    btn.innerText = `Supprimer (${selected.length}) doublons sélectionnés`;
}

async function runDeleteDuplicates() {
    const targetDir = document.getElementById('targetDirInput').value.trim();
    const selectedCbs = document.querySelectorAll('.duplicate-checkbox:checked');
    const filePaths = Array.from(selectedCbs).map(cb => cb.getAttribute('data-path'));

    if (filePaths.length === 0) return;

    showToast("🗑️ Suppression des doublons...", "info");

    try {
        const response = await fetch('/api/duplicates/delete', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ target_dir: targetDir, file_paths: filePaths })
        });

        const data = await response.json();
        if (data.success) {
            showToast(`✅ ${data.message}`, "success");
            runScanDuplicates();
            runScan();
        } else {
            showToast(`❌ ${data.message}`, "error");
        }
    } catch (err) {
        showToast(`❌ Erreur suppression doublons: ${err.message}`, "error");
    }
}

// --------------------------------------------------------------------------
// Bulk Rename
// --------------------------------------------------------------------------
async function runApplyRename() {
    const targetDir = document.getElementById('targetDirInput').value.trim();
    const replaceSpaces = document.getElementById('replaceSpacesSelect').value;
    const lowercase = document.getElementById('renameLowercase').checked;
    const addDatePrefix = document.getElementById('renameAddDate').checked;
    const recursive = document.getElementById('toggleRecursive').checked;

    showToast("✏️ Application du renommage...", "info");

    try {
        const response = await fetch('/api/rename', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                target_dir: targetDir,
                replace_spaces: replaceSpaces,
                lowercase: lowercase,
                add_date_prefix: addDatePrefix,
                recursive: recursive
            })
        });

        const data = await response.json();
        if (data.success) {
            showToast(`🎉 ${data.message}`, "success");
            runScan();
        } else {
            showToast(`❌ ${data.message}`, "error");
        }
    } catch (err) {
        showToast(`❌ Erreur renommage: ${err.message}`, "error");
    }
}

// --------------------------------------------------------------------------
// Rules Manager
// --------------------------------------------------------------------------
async function fetchRules() {
    const targetDir = document.getElementById('targetDirInput').value.trim();
    try {
        const response = await fetch(`/api/rules?target_dir=${encodeURIComponent(targetDir)}`);
        const data = await response.json();
        if (data.success) {
            currentRules = data.rules || {};
            renderRules();
        }
    } catch (err) {
        console.error("Erreur chargement règles:", err);
    }
}

function renderRules() {
    const container = document.getElementById('rulesContainer');
    container.innerHTML = Object.entries(currentRules).map(([cat, exts]) => `
        <div class="rule-card">
            <div class="rule-header">
                <span>📁 ${escapeHtml(cat)}</span>
                <i class="ri-delete-bin-line remove-tag" style="cursor:pointer;" onclick="deleteCategory('${escapeHtml(cat)}')"></i>
            </div>
            <div class="tag-container">
                ${exts.map(ext => `
                    <span class="ext-tag">
                        .${escapeHtml(ext)}
                        <i class="ri-close-line remove-tag" onclick="removeExtension('${escapeHtml(cat)}', '${escapeHtml(ext)}')"></i>
                    </span>
                `).join('')}
                <button class="add-tag-btn" onclick="promptAddExtension('${escapeHtml(cat)}')">+ Ajouter</button>
            </div>
        </div>
    `).join('');
}

function removeExtension(category, ext) {
    if (currentRules[category]) {
        currentRules[category] = currentRules[category].filter(e => e !== ext);
        renderRules();
    }
}

function promptAddExtension(category) {
    const ext = prompt(`Saisissez une extension à ajouter à '${category}' (ex: webp) :`);
    if (ext) {
        const cleaned = ext.trim().toLowerCase().replace(/^\./, '');
        if (cleaned && !currentRules[category].includes(cleaned)) {
            currentRules[category].push(cleaned);
            renderRules();
        }
    }
}

function promptAddCategory() {
    const cat = prompt("Nom de la nouvelle catégorie (ex: Design & 3D) :");
    if (cat && cat.trim()) {
        const catName = cat.trim();
        if (!currentRules[catName]) {
            currentRules[catName] = [];
            renderRules();
        }
    }
}

function deleteCategory(category) {
    if (confirm(`Voulez-vous vraiment supprimer la catégorie '${category}' ?`)) {
        delete currentRules[category];
        renderRules();
    }
}

async function runSaveRules() {
    const targetDir = document.getElementById('targetDirInput').value.trim();
    showToast("💾 Sauvegarde des règles...", "info");

    try {
        const response = await fetch('/api/rules', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ target_dir: targetDir, rules: currentRules })
        });

        const data = await response.json();
        if (data.success) {
            showToast(`✅ ${data.message}`, "success");
            runScan();
        } else {
            showToast(`❌ ${data.message}`, "error");
        }
    } catch (err) {
        showToast(`❌ Erreur sauvegarde règles: ${err.message}`, "error");
    }
}

// --------------------------------------------------------------------------
// History
// --------------------------------------------------------------------------
async function fetchHistory() {
    const targetDir = document.getElementById('targetDirInput').value.trim();
    try {
        const response = await fetch(`/api/history?target_dir=${encodeURIComponent(targetDir)}`);
        const data = await response.json();

        const history = data.history || [];
        document.getElementById('kpiHistoryBatches').innerText = history.length;

        const tbody = document.getElementById('historyTableBody');
        if (history.length === 0) {
            tbody.innerHTML = `
                <tr class="empty-row">
                    <td colspan="4">
                        <div class="empty-state">
                            <i class="ri-inbox-archive-line"></i>
                            <p>Aucun historique de tri pour l'instant.</p>
                        </div>
                    </td>
                </tr>
            `;
        } else {
            tbody.innerHTML = history.map(batch => `
                <tr>
                    <td><code>#${batch.batch_id}</code></td>
                    <td>${batch.timestamp}</td>
                    <td>${batch.count} fichier(s)</td>
                    <td>
                        <button class="btn btn-warning" style="padding: 4px 10px; font-size: 0.75rem;" onclick="runUndo('${batch.batch_id}')">
                            <i class="ri-arrow-go-back-line"></i> Annuler ce lot
                        </button>
                    </td>
                </tr>
            `).join('');
        }
    } catch (err) {
        console.error("Erreur historique:", err);
    }
}

// --------------------------------------------------------------------------
// Watcher Status
// --------------------------------------------------------------------------
async function toggleWatcher(enable) {
    const targetDir = document.getElementById('targetDirInput').value.trim();
    const mode = document.getElementById('sortModeSelect').value;

    const endpoint = enable ? '/api/watcher/start' : '/api/watcher/stop';

    try {
        const response = await fetch(endpoint, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ target_dir: targetDir, mode: mode })
        });
        const data = await response.json();
        updateWatcherBadge(data.is_running);
        showToast(data.message, data.is_running ? "success" : "info");
    } catch (err) {
        showToast("Erreur lors de la modification du Watcher.", "error");
    }
}

async function checkWatcherStatus() {
    try {
        const response = await fetch('/api/watcher/status');
        const data = await response.json();
        updateWatcherBadge(data.is_running);
        document.getElementById('toggleWatcher').checked = data.is_running;
    } catch (err) {
        console.error(err);
    }
}

function updateWatcherBadge(isRunning) {
    const badge = document.getElementById('watcherStatusBadge');
    const text = document.getElementById('watcherStatusText');
    if (isRunning) {
        badge.classList.add('active');
        text.innerText = "Surveillance Active";
    } else {
        badge.classList.remove('active');
        text.innerText = "Watcher Inactif";
    }
}

// --------------------------------------------------------------------------
// Chart.js & Utilities
// --------------------------------------------------------------------------
function initChart() {
    const ctx = document.getElementById('categoryChart').getContext('2d');
    categoryChart = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: [],
            datasets: [{
                data: [],
                backgroundColor: [
                    '#06b6d4', '#10b981', '#f43f5e', '#f59e0b', 
                    '#a855f7', '#6366f1', '#f97316', '#94a3b8'
                ],
                borderWidth: 0
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'right',
                    labels: { color: '#94a3b8', font: { family: 'Plus Jakarta Sans', size: 11 } }
                }
            },
            cutout: '70%'
        }
    });
}

function updateChart(categories) {
    if (!categoryChart) return;
    categoryChart.data.labels = categories.map(c => c.category);
    categoryChart.data.datasets[0].data = categories.map(c => c.count);
    categoryChart.update();
}

function showToast(message, type = "info") {
    const toast = document.getElementById('toast');
    toast.innerText = message;
    toast.className = `toast show ${type}`;
    setTimeout(() => {
        toast.classList.remove('show');
    }, 3500);
}

function escapeHtml(str) {
    return String(str)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;");
}

function formatSize(bytes) {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    if (bytes < 1024 * 1024 * 1024) return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
    return (bytes / (1024 * 1024 * 1024)).toFixed(2) + ' GB';
}
