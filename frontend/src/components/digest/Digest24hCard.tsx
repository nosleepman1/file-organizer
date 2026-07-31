import React from 'react';
import { Digest24hData } from '../../types';

interface Digest24hCardProps {
  digest: Digest24hData | null;
  onRefresh: () => void;
}

export const Digest24hCard: React.FC<Digest24hCardProps> = ({ digest, onRefresh }) => {
  const recentMoves = digest?.recent_moves || [];

  return (
    <div className="tab-pane active">
      <div className="digest-header-card">
        <div>
          <h3><i className="ri-history-line"></i> Rapport d'Activité (Dernières 24h)</h3>
          <p className="subtitle">{digest?.period || 'Synthèse automatique'}</p>
        </div>
        <button className="btn btn-secondary btn-sm" onClick={onRefresh}>
          <i className="ri-refresh-line"></i> Actualiser
        </button>
      </div>

      <div className="digest-metrics-row mt-3">
        <div className="metric-card">
          <i className="ri-file-transfer-line metric-icon"></i>
          <div>
            <h4>{digest?.total_files_moved || 0}</h4>
            <p>Fichiers Réorganisés</p>
          </div>
        </div>
        <div className="metric-card">
          <i className="ri-hard-drive-2-line metric-icon"></i>
          <div>
            <h4>{digest?.total_size_formatted || '0 B'}</h4>
            <p>Volume Données Traitées</p>
          </div>
        </div>
      </div>

      <div className="table-wrapper mt-3">
        <table className="preview-table">
          <thead>
            <tr>
              <th>Horodatage</th>
              <th>Nom du Fichier</th>
              <th>Catégorie</th>
              <th>Destination</th>
            </tr>
          </thead>
          <tbody>
            {recentMoves.length === 0 ? (
              <tr className="empty-row">
                <td colSpan={4}>
                  <div className="empty-state">
                    <i className="ri-calendar-event-line"></i>
                    <p>Aucun déplacement enregistré dans les dernières 24 heures.</p>
                  </div>
                </td>
              </tr>
            ) : (
              recentMoves.map((m, idx) => (
                <tr key={idx}>
                  <td><code>{m.timestamp}</code></td>
                  <td><strong>{m.file_name}</strong></td>
                  <td><span className="badge-category">{m.category}</span></td>
                  <td className="path-text">{m.destination}</td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
};
