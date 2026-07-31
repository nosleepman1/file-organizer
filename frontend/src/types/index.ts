export interface ActionItem {
  source: string;
  destination: string;
  file_name: string;
  dest_file_name?: string;
  category: string;
  size_bytes: number;
  size_formatted: string;
  mtime: string;
  explanation?: string;
  has_collision?: boolean;
  conflict_action?: string;
}

export interface SurgicalFilters {
  regex: string;
  min_size_mb: number;
  max_size_mb: number;
  date_days: number;
}

export interface AiConfig {
  ai_provider: 'deepseek' | 'ollama' | 'openai' | 'custom';
  has_key?: boolean;
  masked_key?: string;
  deepseek_model?: string;
  openai_masked_key?: string;
  openai_model?: string;
  ollama_endpoint?: string;
  ollama_model?: string;
  content_aware_parsing?: boolean;
  custom_prompt?: string;
}

export interface DuplicateFile {
  path: string;
  file_name: string;
  size_bytes: number;
  size_formatted: string;
  mtime: string;
}

export interface DuplicateGroup {
  hash: string;
  count: number;
  size_formatted: string;
  wasted_bytes: number;
  wasted_formatted: string;
  files: DuplicateFile[];
}

export interface RecentMove {
  timestamp: string;
  file_name: string;
  category: string;
  destination: string;
}

export interface Digest24hData {
  period?: string;
  total_files_moved: number;
  total_size_formatted: string;
  categories?: Record<string, number>;
  recent_moves?: RecentMove[];
}

export interface CategoryStat {
  category: string;
  count: number;
  size_bytes: number;
  size_formatted: string;
}

export interface FolderStats {
  target_dir: string;
  total_files: number;
  total_size_bytes: number;
  total_size_formatted: string;
  categories: CategoryStat[];
}

export type ThemeName = 'glass' | 'light' | 'cyberpunk' | 'emerald';
