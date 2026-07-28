let currentActions = [];
let categoryChart = null;

document.addEventListener('DOMContentLoaded', () => {
    initDefaultPath();
    setupEventListeners();
    initChart();
    fetchHistory();
    checkWatcherStatus();
});

// Initialiser avec un dossier par défaut
function initDefaultPath() {
    const input = document.getElementById('targetDirInput');
    if (!input.value) {
        input.value = "DOWNLOADS"; // Résolu côté serveur vers le vrai dossier Downloads
    }
}

function setupEventListeners() {
    // Bouton Scan
    document.getElementById('btnScan').addEventListener('click', runScan);

    // Bouton Lancer l'organisation
    document.getElementById('btnExecute').addEventListener('click', runExecute);

    // Bouton Undo
    document.getElementById('btnUndo').addEventListener('click', runUndo);

    // Presets
    document.querySelectorAll('.btn-preset').forEach(btn => {
        btn.addEventListener('click', (e) => {
            const path = e.currentTarget.getAttribute('data-path');
            document.getElementById('targetDirInput').value = path;
            runScan();
        });
    });

    // Toggle Watcher
    document.getElementById('toggleWatcher').addEventListener('change', (e) => {
        toggleWatcher(e.target.checked);
    });

    // Changement de mode de tri
    document.getElementById('sortModeSelect').addEventListener('change', () => {
        runScan();
    });

    // Navigation Onglets
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
            document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
            document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));

            const tabId = e.currentTarget.getAttribute('data-tab');
            e.currentTarget.classList.add('active');
            document.getElementById(tabId).classList.add('active');
        });
    });
}

// Lancer le Scan (Aperçu / Dry-Run)
async function runScan() {
    const targetDir = document.getElementById('targetDirInput').value.trim();
    const mode = document.getElementById('sortModeSelect').value;

    if (!targetDir) {
        showToast("⚠️ Veuillez spécifier un dossier.", "warning");
        return;
    }

    showToast("🔍 Analyse du dossier en cours...", "info");

    try {
        const response = await fetch('/api/scan', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ target_dir: targetDir, mode: mode })
        });

        const data = await response.json();

        if (!data.success) {
            showToast(`❌ Erreur: ${data.message}`, "error");
            return;
        }

        currentActions = data.actions || [];
        updateUIWithScanResults(data);
        showToast(`✅ Analyse terminée (${currentActions.length} actions détectées).`, "success");

    } catch (err) {
        showToast(`❌ Erreur de communication serveur: ${err.message}`, "error");
    }
}

// Exécuter l'organisation
async function runExecute() {
    const targetDir = document.getElementById('targetDirInput').value.trim();

    if (!currentActions || currentActions.length === 0) {
        showToast("⚠️ Aucune action à exécuter.", "warning");
        return;
    }

    showToast("🚀 Organisation en cours...", "info");

    try {
        const response = await fetch('/api/organize', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ target_dir: targetDir, actions: currentActions })
        });

        const data = await response.json();

        if (data.success) {
            showToast(`🎉 ${data.message}`, "success");
            currentActions = [];
            runScan(); // Rafraîchir
            fetchHistory();
        } else {
            showToast(`❌ ${data.message}`, "error");
        }
    } catch (err) {
        showToast(`❌ Erreur lors du tri: ${err.message}`, "error");
    }
}

// Annuler la dernière action (Undo)
async function runUndo() {
    const targetDir = document.getElementById('targetDirInput').value.trim();

    try {
        const response = await fetch('/api/undo', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ target_dir: targetDir })
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

// Mettre à jour l'interface avec les résultats de l'analyse
function updateUIWithScanResults(data) {
    const stats = data.stats || {};
    document.getElementById('kpiTotalFiles').innerText = stats.total_files || 0;
    document.getElementById('kpiTotalSize').innerText = stats.total_size_formatted || "0 B";
    document.getElementById('kpiActionsCount').innerText = currentActions.length;
    document.getElementById('previewCount').innerText = currentActions.length;

    // Rendre les actions dans la table d'aperçu
    const tbody = document.getElementById('previewTableBody');
    if (currentActions.length === 0) {
        tbody.innerHTML = `
            <tr class="empty-row">
                <td colspan="4">
                    <div class="empty-state">
                        <i class="ri-checkbox-circle-line"></i>
                        <p>Le dossier est déjà parfaitement organisé ! Aucun déplacement nécessaire.</p>
                    </div>
                </td>
            </tr>
        `;
        document.getElementById('btnExecute').disabled = true;
    } else {
        tbody.innerHTML = currentActions.map(action => `
            <tr>
                <td><strong>${escapeHtml(action.file_name)}</strong></td>
                <td><span class="badge-category badge-${action.category}">${action.category}</span></td>
                <td>${action.size_formatted}</td>
                <td class="path-text">${escapeHtml(action.destination)}</td>
            </tr>
        `).join('');
        document.getElementById('btnExecute').disabled = false;
    }

    // Mettre à jour le graphique des catégories
    updateChart(stats.categories || []);
}

// Récupérer l'historique des lots
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
                        <button class="btn btn-warning" style="padding: 4px 10px; font-size: 0.75rem;" onclick="runUndo()">
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

// Basculer l'état du Watcher
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

// Chart.js - Graphique Beurre Donut
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
                    labels: { color: '#94a3b8', font: { family: 'Inter', size: 11 } }
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
