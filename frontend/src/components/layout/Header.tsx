import React from 'react';
import { ThemeName } from '../../types';

interface HeaderProps {
  currentTheme: ThemeName;
  onThemeChange: (theme: ThemeName) => void;
  autostartEnabled: boolean;
  autostartDesc: string;
  onToggleAutostart: () => void;
  hasAiKey: boolean;
  onOpenAiModal: () => void;
}

export const Header: React.FC<HeaderProps> = ({
  currentTheme,
  onThemeChange,
  autostartEnabled,
  autostartDesc,
  onToggleAutostart,
  hasAiKey,
  onOpenAiModal,
}) => {
  return (
    <header className="app-header">
      <div className="logo-container">
        <i className="ri-folder-shield-2-line logo-icon"></i>
        <div>
          <h1>Smart File Organizer <span className="version-badge">PRO</span></h1>
          <p className="subtitle">Tri Chirurgical, IA DeepSeek/Ollama &amp; Démarrage Automatique au Boot</p>
        </div>
      </div>
      
      <div className="header-right-controls">
        <div 
          className={`status-badge-autostart ${autostartEnabled ? 'active' : ''}`} 
          onClick={onToggleAutostart}
          title={autostartDesc || "Cliquez pour basculer l'autostart Boot OS"}
        >
          <span className="dot"></span>
          <span>{autostartEnabled ? 'Boot OS : Actif 🟢' : 'Boot OS : Inactif 🔴'}</span>
        </div>

        <div className="theme-selector-wrapper">
          <i className="ri-palette-line"></i>
          <select 
            value={currentTheme} 
            onChange={(e) => onThemeChange(e.target.value as ThemeName)}
            className="theme-select"
          >
            <option value="glass">Sombre Glass</option>
            <option value="light">Clair Professionnel</option>
            <option value="cyberpunk">Cyberpunk Neon</option>
            <option value="emerald">Émeraude Nature</option>
          </select>
        </div>

        <button className="btn btn-secondary btn-sm" onClick={onOpenAiModal}>
          <i className="ri-brain-line"></i> Configuration IA
          <span className={`badge-dot ${hasAiKey ? 'green' : 'orange'}`}></span>
        </button>
      </div>
    </header>
  );
};
