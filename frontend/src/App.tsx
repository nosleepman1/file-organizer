import React, { useState, useEffect } from 'react';
import { 
  ActionItem, 
  SurgicalFilters, 
  DuplicateGroup, 
  Digest24hData, 
  FolderStats, 
  ThemeName 
} from './types';
import { api } from './services/api';
import { Header } from './components/layout/Header';
import { Sidebar } from './components/layout/Sidebar';
import { AiModal } from './components/ai/AiModal';
import { PreviewTable } from './components/preview/PreviewTable';
import { Digest24hCard } from './components/digest/Digest24hCard';
import { DuplicatesCard } from './components/duplicates/DuplicatesCard';
import { BulkRenameCard } from './components/rename/BulkRenameCard';
import { RulesCard } from './components/rules/RulesCard';
import { ChartCard } from './components/ChartCard';

export const App: React.FC = () => {
  const [theme, setTheme] = useState<ThemeName>('glass');
  const [targetDir, setTargetDir] = useState('DOWNLOADS');
  const [sortMode, setSortMode] = useState('type');
  const [recursive, setRecursive] = useState(false);
  const [aiPrompt, setAiPrompt] = useState('');
  const [surgicalFilters, setSurgicalFilters] = useState<SurgicalFilters>({
    regex: '',
    min_size_mb: 0,
    max_size_mb: 0,
    date_days: 0,
  });

  const [actions, setActions] = useState<ActionItem[]>([]);
  const [selectedIndices, setSelectedIndices] = useState<Set<number>>(new Set());
  const [activeTab, setActiveTab] = useState<'preview' | 'digest24h' | 'duplicates' | 'rename' | 'rules'>('preview');

  const [stats, setStats] = useState<FolderStats | null>(null);
  const [digest, setDigest] = useState<Digest24hData | null>(null);
  const [duplicates, setDuplicates] = useState<DuplicateGroup[]>([]);
  const [rules, setRules] = useState<Record<string, string[]>>({});
  const [isDupLoading, setIsDupLoading] = useState(false);

  const [autostartEnabled, setAutostartEnabled] = useState(false);
  const [autostartDesc, setAutostartDesc] = useState('');
  const [hasAiKey, setHasAiKey] = useState(false);
  const [isAiModalOpen, setIsAiModalOpen] = useState(false);
  const [watcherActive, setWatcherActive] = useState(false);

  const [toast, setToast] = useState<{ message: string; type: string; show: boolean }>({
    message: '',
    type: 'info',
    show: false,
  });

  const showToast = (message: string, type = 'info') => {
    setToast({ message, type, show: true });
    setTimeout(() => {
      setToast((prev) => ({ ...prev, show: false }));
    }, 4000);
  };

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme);
  }, [theme]);

  useEffect(() => {
    loadInitialData();
  }, []);

  const loadInitialData = async () => {
    try {
      const autostart = await api.fetchAutostartStatus();
      setAutostartEnabled(autostart.enabled);
      setAutostartDesc(autostart.description);

      const aiConf = await api.fetchAiConfig();
      setHasAiKey(Boolean(aiConf.has_key || aiConf.ai_provider === 'ollama'));

      const rulesRes = await api.fetchRules(targetDir);
      if (rulesRes.success) setRules(rulesRes.rules);

      runScan();
    } catch (err) {
      console.error(err);
    }
  };

  const runScan = async () => {
    showToast(sortMode === 'ai' ? '🤖 IA en cours d\'analyse...' : '🔍 Analyse du dossier...', 'info');
    try {
      const res = await api.runScan({
        target_dir: targetDir,
        mode: sortMode,
        recursive,
        surgical_filters: surgicalFilters,
        ai_custom_prompt: aiPrompt,
      });

      if (res.success) {
        setActions(res.actions || []);
        setSelectedIndices(new Set((res.actions || []).map((_, i) => i)));
        showToast(`✅ Scan terminé (${res.actions.length} actions proposées).`, 'success');
        refreshStats();
      } else {
        showToast(`⚠️ ${res.message}`, 'warning');
      }
    } catch (err: any) {
      showToast(`❌ Erreur scan: ${err.message}`, 'error');
    }
  };

  const refreshStats = async () => {
    try {
      const st = await api.fetchStats(targetDir);
      setStats(st);
    } catch (err) {
      console.error(err);
    }
  };

  const handleExecute = async () => {
    const selectedActions = actions.filter((_, i) => selectedIndices.has(i));
    if (selectedActions.length === 0) return;

    showToast('⚡ Exécution de la réorganisation...', 'info');
    try {
      const res = await api.executeActions({
        target_dir: targetDir,
        actions: selectedActions,
      });
      if (res.success) {
        showToast(`🎉 ${res.message}`, 'success');
        runScan();
      }
    } catch (err: any) {
      showToast(`❌ Erreur exécution: ${err.message}`, 'error');
    }
  };

  const handleUndo = async () => {
    try {
      const res = await api.undoBatch(targetDir);
      if (res.success) {
        showToast(`✅ ${res.message}`, 'success');
        runScan();
      } else {
        showToast(`⚠️ ${res.message}`, 'warning');
      }
    } catch (err: any) {
      showToast(`❌ Erreur Undo: ${err.message}`, 'error');
    }
  };

  const handleToggleAutostart = async () => {
    try {
      const res = await api.toggleAutostartService(!autostartEnabled);
      setAutostartEnabled(res.enabled);
      showToast(res.message, res.enabled ? 'success' : 'info');
    } catch (err) {
      showToast('Erreur autostart OS', 'error');
    }
  };

  const handleToggleWatcher = async (enable: boolean) => {
    setWatcherActive(enable);
    try {
      const res = await api.toggleWatcher(targetDir, sortMode, enable);
      showToast(res.message, res.success ? 'success' : 'warning');
    } catch (err) {
      showToast('Erreur watcher', 'error');
    }
  };

  const handleFetchDuplicates = async () => {
    setIsDupLoading(true);
    try {
      const res = await api.fetchDuplicates(targetDir, recursive);
      if (res.success) {
        setDuplicates(res.duplicate_groups || []);
        showToast(`🔍 ${res.duplicate_groups.length} groupe(s) de doublons trouvés.`, 'info');
      }
    } catch (err: any) {
      showToast(`❌ Erreur doublons: ${err.message}`, 'error');
    } finally {
      setIsDupLoading(false);
    }
  };

  const handleDeleteDuplicates = async (paths: string[]) => {
    try {
      const res = await api.deleteDuplicates(targetDir, paths);
      if (res.success) {
        showToast(`✅ ${res.message}`, 'success');
        handleFetchDuplicates();
        refreshStats();
      }
    } catch (err: any) {
      showToast(`❌ Erreur suppression: ${err.message}`, 'error');
    }
  };

  const handleFetch24hDigest = async () => {
    try {
      const res = await api.fetch24hDigest(targetDir);
      if (res.success) {
        setDigest(res.digest);
      }
    } catch (err) {
      console.error(err);
    }
  };

  const handleRunRename = async (params: any) => {
    try {
      const res = await api.bulkRename({ target_dir: targetDir, ...params });
      if (res.success) {
        showToast(`✅ ${res.message}`, 'success');
        runScan();
      }
    } catch (err: any) {
      showToast(`❌ Erreur renommage: ${err.message}`, 'error');
    }
  };

  const handleSaveRules = async (newRules: Record<string, string[]>) => {
    try {
      const res = await api.saveRules(targetDir, newRules);
      if (res.success) {
        setRules(newRules);
        showToast('✅ Règles enregistrées !', 'success');
      }
    } catch (err: any) {
      showToast(`❌ Erreur sauvegarde règles: ${err.message}`, 'error');
    }
  };

  return (
    <div className="app-container">
      <Header
        currentTheme={theme}
        onThemeChange={setTheme}
        autostartEnabled={autostartEnabled}
        autostartDesc={autostartDesc}
        onToggleAutostart={handleToggleAutostart}
        hasAiKey={hasAiKey}
        onOpenAiModal={() => setIsAiModalOpen(true)}
      />

      <div className="main-layout">
        <Sidebar
          targetDir={targetDir}
          onTargetDirChange={setTargetDir}
          sortMode={sortMode}
          onSortModeChange={setSortMode}
          recursive={recursive}
          onRecursiveChange={setRecursive}
          surgicalFilters={surgicalFilters}
          onSurgicalFiltersChange={setSurgicalFilters}
          aiPrompt={aiPrompt}
          onAiPromptChange={setAiPrompt}
          watcherActive={watcherActive}
          onToggleWatcher={handleToggleWatcher}
          selectedActionsCount={selectedIndices.size}
          onExecute={handleExecute}
          onUndo={handleUndo}
          onScan={runScan}
        />

        <main className="panel-right">
          <ChartCard categories={stats?.categories || []} />

          <div className="card tabs-card mt-3">
            <div className="tab-header">
              <button
                className={`tab-btn ${activeTab === 'preview' ? 'active' : ''}`}
                onClick={() => setActiveTab('preview')}
              >
                <i className="ri-list-check-2"></i> Aperçu ({actions.length})
              </button>
              <button
                className={`tab-btn ${activeTab === 'digest24h' ? 'active' : ''}`}
                onClick={() => {
                  setActiveTab('digest24h');
                  handleFetch24hDigest();
                }}
              >
                <i className="ri-calendar-check-line"></i> Rapport 24H
              </button>
              <button
                className={`tab-btn ${activeTab === 'duplicates' ? 'active' : ''}`}
                onClick={() => setActiveTab('duplicates')}
              >
                <i className="ri-file-copy-2-line"></i> Doublons Hash
              </button>
              <button
                className={`tab-btn ${activeTab === 'rename' ? 'active' : ''}`}
                onClick={() => setActiveTab('rename')}
              >
                <i className="ri-edit-line"></i> Renommage
              </button>
              <button
                className={`tab-btn ${activeTab === 'rules' ? 'active' : ''}`}
                onClick={() => setActiveTab('rules')}
              >
                <i className="ri-equalizer-line"></i> Règles &amp; Catégories
              </button>
            </div>

            <div className="tab-content">
              {activeTab === 'preview' && (
                <PreviewTable
                  actions={actions}
                  selectedIndices={selectedIndices}
                  onToggleSelection={(idx) => {
                    const next = new Set(selectedIndices);
                    if (next.has(idx)) next.delete(idx);
                    else next.add(idx);
                    setSelectedIndices(next);
                  }}
                  onToggleSelectAll={(select) => {
                    if (select) setSelectedIndices(new Set(actions.map((_, i) => i)));
                    else setSelectedIndices(new Set());
                  }}
                />
              )}

              {activeTab === 'digest24h' && (
                <Digest24hCard digest={digest} onRefresh={handleFetch24hDigest} />
              )}

              {activeTab === 'duplicates' && (
                <DuplicatesCard
                  groups={duplicates}
                  isLoading={isDupLoading}
                  onScanDuplicates={handleFetchDuplicates}
                  onDeleteGroup={handleDeleteDuplicates}
                />
              )}

              {activeTab === 'rename' && <BulkRenameCard onRunRename={handleRunRename} />}

              {activeTab === 'rules' && (
                <RulesCard rules={rules} onSaveRules={handleSaveRules} />
              )}
            </div>
          </div>
        </main>
      </div>

      <AiModal
        isOpen={isAiModalOpen}
        onClose={() => setIsAiModalOpen(false)}
        onSaved={() => api.fetchAiConfig().then((c) => setHasAiKey(Boolean(c.has_key || c.ai_provider === 'ollama')))}
        showToast={showToast}
      />

      {toast.show && <div className="toast show">{toast.message}</div>}
    </div>
  );
};
export default App;
