import { 
  ActionItem, 
  SurgicalFilters, 
  AiConfig, 
  DuplicateGroup, 
  Digest24hData, 
  FolderStats 
} from '../types';

export const api = {
  async fetchHealth() {
    const res = await fetch('/api/health');
    return res.json();
  },

  async fetchStats(targetDir: string): Promise<FolderStats> {
    const res = await fetch(`/api/stats?target_dir=${encodeURIComponent(targetDir)}`);
    return res.json();
  },

  async fetchAiConfig(): Promise<AiConfig & { success: boolean }> {
    const res = await fetch('/api/ai/config');
    return res.json();
  },

  async saveAiConfig(config: Partial<AiConfig>): Promise<{ success: boolean; message: string }> {
    const res = await fetch('/api/ai/config', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(config),
    });
    return res.json();
  },

  async testAiConnection(payload: { provider: string; api_key?: string; model?: string; endpoint?: string }) {
    const res = await fetch('/api/ai/test', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    return res.json();
  },

  async fetchAutostartStatus(): Promise<{ enabled: boolean; description: string }> {
    const res = await fetch('/api/service/autostart');
    return res.json();
  },

  async toggleAutostartService(enable: boolean): Promise<{ enabled: boolean; message: string }> {
    const res = await fetch('/api/service/autostart', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ enable }),
    });
    return res.json();
  },

  async runScan(params: {
    target_dir: string;
    mode: string;
    recursive: boolean;
    surgical_filters: SurgicalFilters;
    ai_custom_prompt: string;
  }): Promise<{ success: boolean; actions: ActionItem[]; message?: string }> {
    const res = await fetch('/api/scan', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(params),
    });
    return res.json();
  },

  async executeActions(params: {
    target_dir: string;
    actions: ActionItem[];
  }): Promise<{ success: boolean; count: number; batch_id: string; message: string }> {
    const res = await fetch('/api/execute', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(params),
    });
    return res.json();
  },

  async undoBatch(targetDir: string, batchId?: string): Promise<{ success: boolean; message: string; restored_count: number }> {
    const res = await fetch('/api/undo', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ target_dir: targetDir, batch_id: batchId }),
    });
    return res.json();
  },

  async fetch24hDigest(targetDir: string): Promise<{ success: boolean; digest: Digest24hData }> {
    const res = await fetch(`/api/history/24h?target_dir=${encodeURIComponent(targetDir)}`);
    return res.json();
  },

  async fetchDuplicates(targetDir: string, recursive: boolean): Promise<{ success: boolean; duplicate_groups: DuplicateGroup[] }> {
    const res = await fetch(`/api/duplicates?target_dir=${encodeURIComponent(targetDir)}&recursive=${recursive}`);
    return res.json();
  },

  async deleteDuplicates(targetDir: string, filePaths: string[]): Promise<{ success: boolean; deleted_count: number; freed_formatted: string; message: string }> {
    const res = await fetch('/api/duplicates/delete', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ target_dir: targetDir, file_paths: filePaths }),
    });
    return res.json();
  },

  async bulkRename(params: {
    target_dir: string;
    replace_spaces: string;
    lowercase: boolean;
    add_date_prefix: boolean;
    recursive: boolean;
  }): Promise<{ success: boolean; renamed_count: number; message: string }> {
    const res = await fetch('/api/rename', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(params),
    });
    return res.json();
  },

  async fetchRules(targetDir: string): Promise<{ success: boolean; rules: Record<string, string[]> }> {
    const res = await fetch(`/api/rules?target_dir=${encodeURIComponent(targetDir)}`);
    return res.json();
  },

  async saveRules(targetDir: string, rules: Record<string, string[]>): Promise<{ success: boolean; message: string }> {
    const res = await fetch('/api/rules', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ target_dir: targetDir, rules }),
    });
    return res.json();
  },

  async toggleWatcher(targetDir: string, mode: string, enable: boolean) {
    const endpoint = enable ? '/api/watcher/start' : '/api/watcher/stop';
    const res = await fetch(endpoint, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ target_dir: targetDir, mode }),
    });
    return res.json();
  }
};
