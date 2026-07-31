import React, { useState, useEffect } from 'react';
import { AiConfig } from '../../types';
import { api } from '../../services/api';

interface AiModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSaved: () => void;
  showToast: (msg: string, type?: 'info' | 'success' | 'warning' | 'error') => void;
}

export const AiModal: React.FC<AiModalProps> = ({ isOpen, onClose, onSaved, showToast }) => {
  const [provider, setProvider] = useState<'deepseek' | 'ollama' | 'openai' | 'custom'>('deepseek');
  const [apiKey, setApiKey] = useState('');
  const [model, setModel] = useState('deepseek-chat');
  const [ollamaEndpoint, setOllamaEndpoint] = useState('http://localhost:11434');
  const [prompt, setPrompt] = useState('');
  const [contentAware, setContentAware] = useState(true);
  const [testResult, setTestResult] = useState<{ success: boolean; message: string } | null>(null);
  const [isTesting, setIsTesting] = useState(false);

  useEffect(() => {
    if (isOpen) {
      loadConfig();
    }
  }, [isOpen]);

  const loadConfig = async () => {
    try {
      const data = await api.fetchAiConfig();
      if (data.success) {
        setProvider(data.ai_provider || 'deepseek');
        setPrompt(data.custom_prompt || '');
        if (data.ollama_endpoint) setOllamaEndpoint(data.ollama_endpoint);
        if (data.content_aware_parsing !== undefined) setContentAware(data.content_aware_parsing);

        if (data.ai_provider === 'openai') {
          setModel(data.openai_model || 'gpt-4o-mini');
        } else if (data.ai_provider === 'ollama') {
          setModel(data.ollama_model || 'llama3:latest');
        } else {
          setModel(data.deepseek_model || 'deepseek-chat');
        }
      }
    } catch (err) {
      console.error(err);
    }
  };

  const handleProviderChange = (newProvider: 'deepseek' | 'ollama' | 'openai' | 'custom') => {
    setProvider(newProvider);
    if (newProvider === 'ollama') {
      setModel('llama3:latest');
    } else if (newProvider === 'openai') {
      setModel('gpt-4o-mini');
    } else if (newProvider === 'deepseek') {
      setModel('deepseek-chat');
    }
  };

  const handleTest = async () => {
    setIsTesting(true);
    setTestResult(null);
    try {
      const res = await api.testAiConnection({
        provider,
        api_key: apiKey,
        model,
        endpoint: ollamaEndpoint,
      });
      setTestResult(res);
    } catch (err: any) {
      setTestResult({ success: false, message: `Erreur réseau : ${err.message}` });
    } finally {
      setIsTesting(false);
    }
  };

  const handleSave = async () => {
    const payload: Partial<AiConfig> = {
      ai_provider: provider,
      custom_prompt: prompt,
      content_aware_parsing: contentAware,
    };

    if (provider === 'openai') {
      if (apiKey) payload.openai_masked_key = apiKey;
      payload.openai_model = model;
    } else if (provider === 'ollama') {
      payload.ollama_endpoint = ollamaEndpoint;
      payload.ollama_model = model;
    } else {
      if (apiKey) payload.masked_key = apiKey;
      payload.deepseek_model = model;
    }

    try {
      const res = await api.saveAiConfig(payload);
      if (res.success) {
        showToast(`✅ Configuration IA (${provider.toUpperCase()}) enregistrée !`, 'success');
        onSaved();
        onClose();
      } else {
        showToast('❌ Erreur sauvegarde IA', 'error');
      }
    } catch (err: any) {
      showToast(`❌ Erreur: ${err.message}`, 'error');
    }
  };

  if (!isOpen) return null;

  return (
    <div className="modal-overlay">
      <div className="modal-card">
        <div className="modal-header">
          <h3><i className="ri-brain-line"></i> Configuration Intelligence Artificielle (Multi-Fournisseurs)</h3>
          <button className="btn-close" onClick={onClose}>&times;</button>
        </div>

        <div className="modal-body">
          <p className="help-text">Choisissez votre fournisseur d'IA : DeepSeek, OpenAI, ou <strong>Ollama (100% Offline &amp; Gratuit)</strong>.</p>

          <div className="form-group mt-3">
            <label>Fournisseur IA :</label>
            <select
              className="form-control"
              value={provider}
              onChange={(e) => handleProviderChange(e.target.value as any)}
            >
              <option value="deepseek">🤖 DeepSeek API (Ultra-rapide &amp; Économique)</option>
              <option value="ollama">📴 Ollama Local (100% Offline - LLM sur votre machine)</option>
              <option value="openai">🧠 OpenAI API (GPT-4o-mini / GPT-4o)</option>
              <option value="custom">⚙️ Custom REST Endpoint (LM Studio, LocalAI)</option>
            </select>
          </div>

          {provider !== 'ollama' && (
            <div className="form-group mt-3">
              <label>Clé API (sk-...) :</label>
              <input
                type="password"
                className="form-control"
                placeholder="Entrez votre clé API"
                value={apiKey}
                onChange={(e) => setApiKey(e.target.value)}
              />
            </div>
          )}

          {provider === 'ollama' && (
            <div className="form-group mt-3">
              <label>URL Serveur Ollama Local :</label>
              <input
                type="text"
                className="form-control"
                value={ollamaEndpoint}
                onChange={(e) => setOllamaEndpoint(e.target.value)}
                placeholder="http://localhost:11434"
              />
            </div>
          )}

          <div className="form-group mt-3">
            <label>Nom du Modèle LLM :</label>
            <input
              type="text"
              className="form-control"
              placeholder="ex: deepseek-chat, llama3:latest, gpt-4o-mini"
              value={model}
              onChange={(e) => setModel(e.target.value)}
            />
          </div>

          <div className="form-group mt-3">
            <label>Instruction Système par défaut :</label>
            <textarea
              className="form-control"
              rows={2}
              placeholder="Ex: Classer les fichiers par sujet sémantique et type de projet..."
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
            />
          </div>

          <div className="toggle-group mt-3">
            <div className="toggle-item">
              <div>
                <strong>Analyse de Contenu (Content-Aware Parsing)</strong>
                <p className="help-text">Transmet un aperçu texte des fichiers au LLM pour un tri sémantique par contenu</p>
              </div>
              <label className="switch">
                <input
                  type="checkbox"
                  checked={contentAware}
                  onChange={(e) => setContentAware(e.target.checked)}
                />
                <span className="slider round"></span>
              </label>
            </div>
          </div>

          {testResult && (
            <div className={`test-result-badge show ${testResult.success ? 'success' : 'error'} mt-2`}>
              {testResult.success ? '✅' : '❌'} {testResult.message}
            </div>
          )}
        </div>

        <div className="modal-footer">
          <button className="btn btn-secondary" onClick={handleTest} disabled={isTesting}>
            <i className="ri-wifi-line"></i> {isTesting ? 'Test en cours...' : 'Tester la connexion'}
          </button>
          <button className="btn btn-primary" onClick={handleSave}>
            <i className="ri-save-line"></i> Enregistrer
          </button>
        </div>
      </div>
    </div>
  );
};
