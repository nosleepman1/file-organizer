import React, { useState } from 'react';
import { SurgicalFilters } from '../../types';

interface SurgicalFiltersCardProps {
  filters: SurgicalFilters;
  onChange: (filters: SurgicalFilters) => void;
}

export const SurgicalFiltersCard: React.FC<SurgicalFiltersCardProps> = ({ filters, onChange }) => {
  const [isOpen, setIsOpen] = useState(false);

  const updateField = (field: keyof SurgicalFilters, val: any) => {
    onChange({ ...filters, [field]: val });
  };

  return (
    <div className="surgical-filters-card mt-2">
      <div className="surgical-filters-header" onClick={() => setIsOpen(!isOpen)}>
        <span><i className="ri-filter-3-line"></i> Filtres Chirurgicaux</span>
        <i className={isOpen ? 'ri-arrow-up-s-line' : 'ri-arrow-down-s-line'}></i>
      </div>

      {isOpen && (
        <div className="surgical-filters-body">
          <div className="form-group-sm mt-2">
            <label>Expression Régulière (Regex nom) :</label>
            <input
              type="text"
              className="form-control-sm"
              placeholder="ex: .*\.pdf$"
              value={filters.regex}
              onChange={(e) => updateField('regex', e.target.value)}
            />
          </div>

          <div className="filter-row">
            <div className="form-group-sm">
              <label>Taille min (Mo) :</label>
              <input
                type="number"
                className="form-control-sm"
                placeholder="0"
                value={filters.min_size_mb || ''}
                onChange={(e) => updateField('min_size_mb', parseFloat(e.target.value) || 0)}
              />
            </div>
            <div className="form-group-sm">
              <label>Taille max (Mo) :</label>
              <input
                type="number"
                className="form-control-sm"
                placeholder="0"
                value={filters.max_size_mb || ''}
                onChange={(e) => updateField('max_size_mb', parseFloat(e.target.value) || 0)}
              />
            </div>
          </div>

          <div className="form-group-sm mt-2">
            <label>Derniers jours (Modifié il y a X jours) :</label>
            <input
              type="number"
              className="form-control-sm"
              placeholder="Ex: 30"
              value={filters.date_days || ''}
              onChange={(e) => updateField('date_days', parseInt(e.target.value) || 0)}
            />
          </div>
        </div>
      )}
    </div>
  );
};
