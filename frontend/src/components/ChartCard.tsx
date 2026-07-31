import React from 'react';
import { CategoryStat } from '../types';

interface ChartCardProps {
  categories: CategoryStat[];
}

export const ChartCard: React.FC<ChartCardProps> = ({ categories }) => {
  const total = categories.reduce((sum, c) => sum + c.count, 0);

  return (
    <div className="card chart-card">
      <h3><i className="ri-pie-chart-line"></i> Répartition des Fichiers</h3>
      
      <div className="category-stats-list mt-2">
        {categories.length === 0 ? (
          <p className="help-text text-center">Aucune donnée de catégorie.</p>
        ) : (
          categories.map((cat) => {
            const pct = total > 0 ? ((cat.count / total) * 100).toFixed(1) : 0;
            return (
              <div key={cat.category} className="category-stat-item">
                <div className="stat-label">
                  <span><strong>{cat.category}</strong> ({cat.count} fichiers)</span>
                  <span>{cat.size_formatted} ({pct}%)</span>
                </div>
                <div className="progress-bar-bg">
                  <div
                    className="progress-bar-fill"
                    style={{ width: `${pct}%` }}
                  ></div>
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
};
