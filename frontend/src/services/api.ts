import axios from 'axios';
import type { 
  SessionSummary, 
  SessionDetail, 
  Finding, 
  Source, 
  Contradiction, 
  QueryResult 
} from '../types';

const API_URL = (import.meta as any).env?.VITE_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const startResearch = async (question: string): Promise<{session_id: string, status: string}> => {
  const { data } = await api.post('/research', { question });
  return data;
};

export const getSession = async (id: string): Promise<SessionDetail> => {
  const { data } = await api.get(`/research/${id}`);
  return data;
};

export const getSessions = async (page = 1, limit = 10): Promise<{sessions: SessionSummary[], total: number, page: number}> => {
  const { data } = await api.get('/sessions', { params: { page, limit } });
  return data;
};

export const getFinding = async (id: string): Promise<Finding> => {
  const { data } = await api.get(`/findings/${id}`);
  return data;
};

export const getFindings = async (filters?: {classification?: string, session_id?: string}): Promise<{findings: Finding[]}> => {
  const { data } = await api.get('/findings', { params: filters });
  return data;
};

export const getSource = async (id: string): Promise<Source> => {
  const { data } = await api.get(`/sources/${id}`);
  return data;
};

export const getContradiction = async (id: string): Promise<Contradiction> => {
  const { data } = await api.get(`/contradictions/${id}`);
  return data;
};

export const getContradictions = async (session_id?: string): Promise<{contradictions: Contradiction[]}> => {
  const { data } = await api.get('/contradictions', { params: { session_id } });
  return data;
};

export const queryKnowledge = async (question: string): Promise<QueryResult> => {
  const { data } = await api.post('/query', { question });
  return data;
};

export const getHealth = async (): Promise<{status: string, db: string, vector_store: string, provider: string}> => {
  const { data } = await api.get('/health');
  return data;
};
