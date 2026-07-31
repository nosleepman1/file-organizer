import React, { useState } from 'react';

interface RulesCardProps {
  rules: Record<string, string[]>;
  onSaveRules: (rules: Record<string, string[]>) => void;
}

export const RulesCard: React.FC<RulesCardProps> = ({ rules, onSaveRules }) => {
  const [localRules, setLocalRules] = useState<Record<string, string[]>>(rules);
  const [newCatName, setNewCatName] = useState('');

  const handleExtChange = (cat: string, value: string) => {
    const exts = value.split(',').map((s) => s.trim().replace(/^\./, ''));
    setLocalRules({ ...localRules, [cat]: exts });
  };

  const handleAddCategory = () => {
    if (!newCatName.trim()) return;
    const cat = newCatName.trim();
    if (!localRules[cat]) {
      setLocalRules({ ...localRules, [cat]: [] });
      setNewCatName('');
    }
  };

  const handleDeleteCategory = (cat: string) => {
    const updated = { ...localRules };
    delete updated[cat];
    setLocalRules(updated);
  };

  const handleSave = () => {
    onSaveRules(localRules);
  };

  return (
    <div className="tab-pane active">
      <div className="rules-header">
        <div>
          <h3><i className="ri-equalizer-line"></i> Gestionnaire de Catégories &amp; Extensions</h3>
          <p className="subtitle">Personnalisez les associations d'extensions de fichiers par catégorie</p>
        </div>
        <button className="btn btn-success" onClick={handleSave}>
          <i className="ri-save-line"></i> Sauvegarder les Règles
        </button>
      </div>

      <div className="add-category-row mt-3">
        <input
          type="text"
          className="form-control"
          placeholder="Nom de la nouvelle catégorie (ex: Ebooks)..."
          value={newCatName}
          onChange={(e) => setNewCatName(e.target.value)}
        />
        <button className="btn btn-secondary" onClick={handleAddCategory}>
          <i className="ri-add-line"></i> Ajouter Catégorie
        </button>
      </div>

      <div className="rules-grid mt-3">
        {Object.entries(localRules).map(([cat, exts]) => (
          <div key={cat} className="rule-card">
            <div className="rule-card-header">
              <strong>{cat}</strong>
              <button
                className="btn-icon btn-danger-text"
                onClick={() => handleDeleteCategory(cat)}
                title="Supprimer la catégorie"
              >
                <i className="ri-delete-bin-line"></i>
              </button>
            </div>
            <div className="rule-card-body">
              <label>Extensions (séparées par virgules) :</label>
              <input
                type="text"
                className="form-control-sm"
                value={exts.join(', ')}
                onChange={(e) => handleExtChange(cat, e.target.value)}
                placeholder="ex: pdf, epub, mobi"
              />
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
