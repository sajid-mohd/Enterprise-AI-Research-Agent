export type SessionStatus = 'pending' | 'decomposing' | 'searching' | 'extracting' | 'analyzing' | 'synthesizing' | 'completed' | 'failed';

export type Classification = 'supporting' | 'contradicting' | 'emerging' | 'uncertain';

export interface SessionSummary {
  id: string;
  question: string;
  status: SessionStatus;
  created_at: string;
  finding_count?: number;
  source_count?: number;
}

export interface SubQuestion {
  id: string;
  question: string;
  research_intent: string;
  status: string;
}

export interface Source {
  id: string;
  url: string;
  title: string;
  domain: string;
  source_type: string;
  retrieved_at: string;
  word_count: number;
  reliability_score: number;
  cleaned_content?: string;
}

export interface Finding {
  id: string;
  text: string;
  classification: Classification;
  confidence: number;
  created_at: string;
  source?: Source;
}

export interface Contradiction {
  id: string;
  finding_a: Finding;
  finding_b: Finding;
  description: string;
  severity: 'low' | 'medium' | 'high';
  confidence: number;
}

export interface Conclusion {
  id: string;
  text: string;
  confidence: number;
  key_points: string[];
  limitations: string[];
  supporting_findings: Finding[];
  contradicting_findings: Finding[];
}

export interface SessionDetail {
  id: string;
  question: string;
  status: SessionStatus;
  error_message?: string;
  created_at: string;
  updated_at: string;
  subquestions: SubQuestion[];
  sources: Source[];
  findings: Finding[];
  contradictions: Contradiction[];
  conclusion?: Conclusion;
}

export interface QueryResult {
  answer: string;
  findings_used: Array<{finding_id: string; text: string; source_url: string; classification: string}>;
  confidence: number;
}
