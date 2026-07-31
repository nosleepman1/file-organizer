import React, { useState } from 'react';

interface BulkRenameCardProps {
  onRunRename: (params: {
    replace_spaces: string;
    lowercase: boolean;
    add_date_prefix: boolean;
    recursive: boolean;
  }) => void;
}

export const BulkRenameCard: React.FC<BulkRenameCardProps> = ({ onRunRename }) => {
  const [replaceSpaces, setReplaceSpaces] = useState('_');
  const [lowercase, setLowercase] = useState(false);
  const [addDatePrefix, setAddDatePrefix] = useState(false);
  const [recursive, setRecursive] = useState(false);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onRunRename({
      replace_spaces: replaceSpaces,
      lowercase,
      add_date_prefix: addDatePrefix,
      recursive,
    });
  };

  return (
    <div className="tab-pane active">
      <div className="rename-card">
        <h3><i className="ri-edit-line"></i> Renommage en Masse des Fichiers</h3>
        <p className="subtitle">Appliquez des règles de nettoyage uniformes sur vos fichiers</p>

        <form onSubmit={handleSubmit} className="mt-3">
          <div className="form-group">
            <label>Remplacer les espaces par :</label>
            <select
              className="form-control"
              value={replaceSpaces}
              onChange={(e) => setReplaceSpaces(e.target.value)}
            >
              <option value="_">Tiret bas ( _ )</option>
              <option value="-">Tiret haut ( - )</option>
              <option value="">Supprimer les espaces</option>
              <option value="none">Ne pas modifier les espaces</option>
            </select>
          </div>

          <div className="toggle-group mt-3">
            <div className="toggle-item">
              <span>Convertir les noms en minuscules</span>
              <label className="switch">
                <input
                  type="checkbox"
                  checked={lowercase}
                  onChange={(e) => setLowercase(e.target.checked)}
                />
                <span className="slider round"></span>
              </label>
            </div>

            <div className="toggle-item mt-2">
              <span>Ajouter la date de modification en préfixe (AAAA-MM-JJ_)</span>
              <label className="switch">
                <input
                  type="checkbox"
                  checked={addDatePrefix}
                  onChange={(e) => setAddDatePrefix(e.target.checked)}
                />
                <span className="slider round"></span>
              </label>
            </div>

            <div className="toggle-item mt-2">
              <span>Appliquer récursivement dans les sous-dossiers</span>
              <label className="switch">
                <input
                  type="checkbox"
                  checked={recursive}
                  onChange={(e) => setRecursive(e.target.checked)}
                />
                <span className="slider round"></span>
              </label>
            </div>
          </div>

          <div className="mt-4">
            <button type="submit" className="btn btn-primary">
              <i className="ri-magic-line"></i> Exécuter le Renommage
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
