// Report Types for Frontend

export interface ClaimRequest {
  text: string;
  url?: string;
  language?: string;
  metadata?: Record<string, any>;
}

export interface EvidenceItem {
  source: string;
  title?: string;
  snippet: string;
  score?: number;
  source_type?: string;
  provenance_timestamp?: string;
  provenance_id?: string;
}

export interface VerificationResult {
  method: string;
  confidence: number;
  notes?: string;
  sources?: string[];
}

export interface FallacyItem {
  type: string;
  explanation?: string;
  span?: string;
  confidence?: number;
  severity?: 'low' | 'medium' | 'high';
}

export interface AIDetectionResult {
  is_ai_generated: boolean;
  confidence: number;
  method: string;
  scores?: Record<string, number>;
  metadata?: Record<string, any>;
}

export interface MultilingualData {
  detected_language: string;
  processing_language: string;
  translation_info?: {
    source_language: string;
    target_language: string;
    confidence: number;
  };
  cross_lingual_evidence?: boolean;
}

export interface SAGData {
  analysis_id: string;
  language: string;
  nodes: SAGNode[];
  edges: SAGEdge[];
  rdf_graph: Record<string, string>;
  metadata?: {
    format?: string;
    version?: string;
    created_at?: string;
  };
}

export interface SAGNode {
  id: string;
  type: string;
  label: string;
  properties?: Record<string, any>;
}

export interface SAGEdge {
  source: string;
  target: string;
  relation: string;
  properties?: Record<string, any>;
}

export interface ProvenanceData {
  analysis_id: string;
  timestamp: string;
  source: string;
  chain: ProvenanceEntry[];
}

export interface ProvenanceEntry {
  id: string;
  timestamp: string;
  type: string;
  source_id?: string;
  parent_ids?: string[];
  metadata?: Record<string, any>;
  data_hash?: string;
  confidence_score?: number;
  processing_time_ms?: number;
}

export interface ReportResponse {
  claim_id: string | null;
  verdict: string;
  confidence: number;
  evidence: EvidenceItem[];
  verification: VerificationResult;
  fallacies: FallacyItem[];
  ai_detection?: AIDetectionResult;
  multilingual?: MultilingualData;
  sag?: SAGData;
  provenance?: ProvenanceData;
  processing_time_ms?: number;
  created_at?: string;
}

// UI State Types
export interface UIState {
  isLoading: boolean;
  error: string | null;
  selectedTab: string;
  expandedSections: Set<string>;
  selectedNode: string | null;
  selectedEdge: string | null;
}

// Feedback Types
export interface UserFeedback {
  id?: string;
  timestamp?: string;
  user_id?: string;
  analysis_id: string;
  feedback_type: 'accuracy' | 'source_quality' | 'logical_flow' | 'overall';
  rating: number;
  comment?: string;
  specific_element?: string;
  metadata?: Record<string, any>;
}

export interface UserOverride {
  id?: string;
  timestamp?: string;
  user_id?: string;
  analysis_id: string;
  override_type: 'verdict' | 'confidence' | 'evidence' | 'fallacy';
  original_value: any;
  new_value: any;
  reason: string;
  metadata?: Record<string, any>;
}

// API Response Types
export interface APIResponse<T> {
  success: boolean;
  data?: T;
  error?: string;
  message?: string;
}

export interface AnalysisRequest {
  text: string;
  url?: string;
  language?: string;
  options?: {
    include_ai_detection?: boolean;
    include_sag?: boolean;
    include_provenance?: boolean;
    confidence_threshold?: number;
  };
  metadata?: Record<string, any>;
}

// Error Types
export interface APIError {
  code: string;
  message: string;
  details?: Record<string, any>;
  timestamp: string;
}

// Configuration Types
export interface AppConfig {
  api_url: string;
  default_language: string;
  confidence_threshold: number;
  enable_ai_detection: boolean;
  enable_sag: boolean;
  enable_provenance: boolean;
  theme: 'light' | 'dark';
  auto_analyze: boolean;
}

// Browser Extension Types
export interface ExtensionMessage {
  type: 'analyze_text' | 'analyze_url' | 'get_selection' | 'show_popup';
  data?: any;
}

export interface ExtensionResponse {
  success: boolean;
  data?: any;
  error?: string;
}

// Chart/Visualization Types
export interface ChartData {
  labels: string[];
  datasets: ChartDataset[];
}

export interface ChartDataset {
  label: string;
  data: number[];
  backgroundColor?: string | string[];
  borderColor?: string | string[];
  borderWidth?: number;
}

// Notification Types
export interface Notification {
  id: string;
  type: 'success' | 'error' | 'warning' | 'info';
  title: string;
  message: string;
  duration?: number;
  actions?: NotificationAction[];
}

export interface NotificationAction {
  label: string;
  action: () => void;
  style?: 'primary' | 'secondary' | 'danger';
}






