import React from 'react';
import { SurgicalFilters } from '../../types';
import { SurgicalFiltersCard } from '../surgical/SurgicalFiltersCard';

interface SidebarProps {
  targetDir: string;
  onTargetDirChange: (dir: string) => void;
  sortMode: string;
  onSortModeChange: (mode: string) => void;
  recursive: boolean;
  onRecursiveChange: (val: boolean) => void;
  surgicalFilters: SurgicalFilters;
  onSurgicalFiltersChange: (filters: SurgicalFilters) => void;
  aiPrompt: string;
  onAiPromptChange: (prompt: string) => void;
  watcherActive: boolean;
  onToggleWatcher: (active: boolean) => void;
  selectedActionsCount: number;
  onExecute: () => void;
  onUndo: () => void;
  onScan: () => void;
}

export const Sidebar: React.FC<SidebarProps> = ({
  targetDir,
  onTargetDirChange,
  sortMode,
  onSortModeChange,
  recursive,
  onRecursiveChange,
  surgicalFilters,
  onSurgicalFiltersChange,
  aiPrompt,
  onAiPromptChange,
  watcherActive,
  onToggleWatcher,
  selectedActionsCount,
  onExecute,
  onUndo,
  onScan,
}) => {
  return (
    <aside className="panel-left">
      <div className="card control-card">
        <h3><i className="ri-settings-4-line"></i> Configuration du Tri</h3>

        <div className="form-group">
          <label>Dossier Cible :</label>
          <div className="input-group">
            <input
              type="text"
              className="form-control"
              placeholder="Ex: DOWNLOADS ou C:\Users\..."
              value={targetDir}
              onChange={(e) => onTargetDirChange(e.target.value)}
            />
            <button className="btn btn-primary btn-icon" onClick={onScan} title="Scanner le dossier">
              <i className="ri-search-line"></i>
            </button>
          </div>
          <p className="help-text">Raccourcis: DOWNLOADS, DESKTOP, DOCUMENTS</p>
        </div>

        <div className="form-group mt-2">
          <label>Mode de Réorganisation :</label>
          <select
            className="form-control"
            value={sortMode}
            onChange={(e) => onSortModeChange(e.target.value)}
          >
            <option value="type">📁 Par Type (Documents, Images, Code...)</option>
            <option value="date">📅 Par Date (Année / Mois)</option>
            <option value="size">⚖️ Par Taille (&lt;10MB, 10-100MB...)</option>
            <option value="ai">🤖 Tri IA Sémantique (DeepSeek/Ollama/OpenAI)</option>
          </select>
        </div>

        <div className="toggle-group mt-2">
          <div className="toggle-item">
            <span>Inclure les sous-dossiers (Récursif)</span>
            <label className="switch">
              <input
                type="checkbox"
                checked={recursive}
                onChange={(e) => onRecursiveChange(e.target.checked)}
              />
              <span className="slider round"></span>
            </label>
          </div>
        </div>

        {sortMode === 'ai' && (
          <div className="form-group mt-2">
            <label>Instruction Système IA (Prompt court) :</label>
            <textarea
              className="form-control-sm"
              rows={2}
              placeholder="Ex: Regrouper les factures par année, et le code par langage..."
              value={aiPrompt}
              onChange={(e) => onAiPromptChange(e.target.value)}
            />
          </div>
        )}

        <SurgicalFiltersCard filters={surgicalFilters} onChange={onSurgicalFiltersChange} />

        <div className="toggle-group mt-3">
          <div className="toggle-item">
            <div>
              <strong>Surveillance Arrière-Plan (Watcher)</strong>
              <p className="help-text">Auto-classement continu des nouveaux fichiers</p>
            </div>
            <label className="switch">
              <input
                type="checkbox"
                checked={watcherActive}
                onChange={(e) => onToggleWatcher(e.target.checked)}
              />
              <span className="slider round"></span>
            </label>
          </div>
        </div>

        <div className="action-buttons">
          <button
            className="btn btn-success btn-block"
            disabled={selectedActionsCount === 0}
            onClick={onExecute}
          >
            <i className="ri-rocket-line"></i> Lancer l'Organisation ({selectedActionsCount})
          </button>
          <button className="btn btn-warning btn-block" onClick={onUndo}>
            <i className="ri-arrow-go-back-line"></i> Annuler Dernier Tri (Undo)
          </button>
        </div>
      </div>
    </aside>
  );
};
