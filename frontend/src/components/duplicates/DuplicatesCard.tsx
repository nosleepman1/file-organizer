import React from 'react';
import { DuplicateGroup } from '../../types';

interface DuplicatesCardProps {
  groups: DuplicateGroup[];
  isLoading: boolean;
  onScanDuplicates: () => void;
  onDeleteGroup: (filePaths: string[]) => void;
}

export const DuplicatesCard: React.FC<DuplicatesCardProps> = ({
  groups,
  isLoading,
  onScanDuplicates,
  onDeleteGroup,
}) => {
  const totalWastedBytes = groups.reduce((acc, g) => acc + g.wasted_bytes, 0);

  const formatSize = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    if (bytes < 1024 * 1024 * 1024) return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
    return `${(bytes / (1024 * 1024 * 1024)).toFixed(2)} GB`;
  };

  return (
    <div className="tab-pane active">
      <div className="duplicates-header">
        <div>
          <h3><i className="ri-file-copy-2-line"></i> Détections de Doublons Réels (Hash SHA256)</h3>
          <p className="subtitle">Identifiez et nettoyez les fichiers identiques sur votre disque</p>
        </div>
        <button className="btn btn-primary" onClick={onScanDuplicates} disabled={isLoading}>
          <i className="ri-search-eye-line"></i> {isLoading ? 'Scan en cours...' : 'Rechercher Doublons'}
        </button>
      </div>

      {groups.length > 0 && (
        <div className="duplicate-summary-banner mt-3">
          <i className="ri-delete-bin-line icon"></i>
          <div>
            <strong>{groups.length} Groupe(s) de doublons détectés !</strong>
            <p>Espace disque à récupérer : <span>{formatSize(totalWastedBytes)}</span></p>
          </div>
        </div>
      )}

      <div className="duplicates-container mt-3">
        {groups.length === 0 ? (
          <div className="empty-state">
            <i className="ri-checkbox-circle-line"></i>
            <p>Aucun doublon trouvé. Cliquez sur 'Rechercher Doublons' pour scanner.</p>
          </div>
        ) : (
          groups.map((group, idx) => (
            <div key={idx} className="duplicate-group-card mb-3">
              <div className="group-header">
                <span>
                  <i className="ri-fingerprint-line"></i> Groupe #{group.hash} ({group.count} fichiers - {group.size_formatted} chacun)
                </span>
                <button
                  className="btn btn-danger btn-sm"
                  onClick={() => onDeleteGroup(group.files.slice(1).map((f) => f.path))}
                >
                  <i className="ri-delete-bin-5-line"></i> Nettoyer Doublons (Garder le 1er)
                </button>
              </div>

              <div className="group-files">
                {group.files.map((file, fIdx) => (
                  <div key={fIdx} className="duplicate-file-item">
                    <span className="file-name">{file.file_name}</span>
                    <span className="file-path">{file.path}</span>
                    {fIdx === 0 && <span className="badge-primary">Original</span>}
                  </div>
                ))}
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
};
