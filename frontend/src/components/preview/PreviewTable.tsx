import React, { useState } from 'react';
import { ActionItem } from '../../types';

interface PreviewTableProps {
  actions: ActionItem[];
  selectedIndices: Set<number>;
  onToggleSelection: (index: number) => void;
  onToggleSelectAll: (select: boolean) => void;
}

export const PreviewTable: React.FC<PreviewTableProps> = ({
  actions,
  selectedIndices,
  onToggleSelection,
  onToggleSelectAll,
}) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [categoryFilter, setCategoryFilter] = useState('');

  const categories = Array.from(new Set(actions.map((a) => a.category)));

  const filteredActions = actions.filter((action) => {
    const matchSearch =
      action.file_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      action.destination.toLowerCase().includes(searchTerm.toLowerCase());
    const matchCat = !categoryFilter || action.category === categoryFilter;
    return matchSearch && matchCat;
  });

  const allFilteredSelected =
    filteredActions.length > 0 &&
    filteredActions.every((action) => selectedIndices.has(actions.indexOf(action)));

  const handleMasterCheckbox = (checked: boolean) => {
    onToggleSelectAll(checked);
  };

  return (
    <div className="tab-pane active">
      <div className="table-toolbar">
        <div className="search-box">
          <i className="ri-search-line search-icon"></i>
          <input
            type="text"
            className="form-control-sm"
            placeholder="Filtrer par nom ou destination..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
        </div>

        <div className="filter-box">
          <select
            className="form-control-sm"
            value={categoryFilter}
            onChange={(e) => setCategoryFilter(e.target.value)}
          >
            <option value="">Toutes les catégories</option>
            {categories.map((cat) => (
              <option key={cat} value={cat}>
                {cat}
              </option>
            ))}
          </select>
        </div>

        <div className="selection-stats">
          <span>
            {selectedIndices.size} / {actions.length} sélectionné(s)
          </span>
        </div>
      </div>

      <div className="table-wrapper">
        <table className="preview-table">
          <thead>
            <tr>
              <th style={{ width: '40px' }}>
                <input
                  type="checkbox"
                  checked={allFilteredSelected}
                  onChange={(e) => handleMasterCheckbox(e.target.checked)}
                />
              </th>
              <th>Nom du Fichier</th>
              <th>Catégorie / Explication</th>
              <th>Taille</th>
              <th>Destination Proposée</th>
            </tr>
          </thead>
          <tbody>
            {filteredActions.length === 0 ? (
              <tr className="empty-row">
                <td colSpan={5}>
                  <div className="empty-state">
                    <i className="ri-inbox-line"></i>
                    <p>Aucune action de réorganisation détectée pour ce dossier.</p>
                  </div>
                </td>
              </tr>
            ) : (
              filteredActions.map((action) => {
                const originalIndex = actions.indexOf(action);
                const isChecked = selectedIndices.has(originalIndex);

                return (
                  <tr key={originalIndex}>
                    <td>
                      <input
                        type="checkbox"
                        checked={isChecked}
                        onChange={(e) => onToggleSelection(originalIndex)}
                      />
                    </td>
                    <td>
                      <strong>{action.file_name}</strong>
                      {action.has_collision && (
                        <span className="badge-warning" title="Fichier existant - sera renommé automatiquement">
                          ⚠️ Conflit
                        </span>
                      )}
                    </td>
                    <td>
                      <span className="badge-category">{action.category}</span>
                      {action.explanation && (
                        <div className="ai-explanation-badge">
                          <i className="ri-brain-line"></i> {action.explanation}
                        </div>
                      )}
                    </td>
                    <td>{action.size_formatted}</td>
                    <td className="path-text">{action.destination}</td>
                  </tr>
                );
              })
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
};
