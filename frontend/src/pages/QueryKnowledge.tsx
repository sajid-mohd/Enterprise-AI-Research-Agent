import React, { useState } from 'react';
import { Search, Loader2, Sparkles, ExternalLink } from 'lucide-react';
import { queryKnowledge } from '../services/api';
import { ConfidenceBar } from '../components/ConfidenceBar';
import { StatusBadge } from '../components/StatusBadge';
import type { QueryResult } from '../types';

export const QueryKnowledge: React.FC = () => {
  const [query, setQuery] = useState('');
  const [isQuerying, setIsQuerying] = useState(false);
  const [result, setResult] = useState<QueryResult | null>(null);

  const exampleQueries = [
    "What are the main risks associated with AI adoption?",
    "Which findings discuss cost reduction strategies?",
    "Show me emerging trends in sustainable packaging"
  ];

  const handleQuery = async (q: string) => {
    if (!q.trim()) return;
    setQuery(q);
    setIsQuerying(true);
    try {
      const data = await queryKnowledge(q);
      setResult(data);
    } catch (err) {
      console.error(err);
      alert('Failed to query knowledge base.');
    } finally {
      setIsQuerying(false);
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    handleQuery(query);
  };

  return (
    <div className="max-w-4xl mx-auto space-y-8">
      <div className="text-center py-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-4 flex items-center justify-center gap-3">
          <Sparkles className="text-sky-500 w-8 h-8" />
          Ask the Knowledge Base
        </h1>
        <p className="text-gray-500 max-w-2xl mx-auto text-lg">
          Query across all accumulated research findings, sources, and synthesis. The AI will cross-reference everything it knows.
        </p>
      </div>

      <div className="bg-white rounded-2xl shadow-lg border border-gray-200 overflow-hidden">
        <form onSubmit={handleSubmit} className="p-2 flex">
          <div className="relative flex-1">
            <Search className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400 w-6 h-6" />
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="E.g., What are the conflicting viewpoints on..."
              className="w-full pl-12 pr-4 py-4 rounded-xl border-none focus:ring-0 text-lg"
              disabled={isQuerying}
            />
          </div>
          <button
            type="submit"
            disabled={!query.trim() || isQuerying}
            className="bg-sky-600 hover:bg-sky-700 text-white px-8 py-4 rounded-xl font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2 m-1"
          >
            {isQuerying ? <Loader2 className="w-5 h-5 animate-spin" /> : 'Search'}
          </button>
        </form>
      </div>

      {!result && !isQuerying && (
        <div className="flex flex-wrap justify-center gap-2">
          {exampleQueries.map((eq, i) => (
            <button
              key={i}
              onClick={() => handleQuery(eq)}
              className="bg-sky-50 text-sky-700 hover:bg-sky-100 px-4 py-2 rounded-full text-sm font-medium transition-colors border border-sky-100"
            >
              "{eq}"
            </button>
          ))}
        </div>
      )}

      {isQuerying && (
        <div className="py-12 flex flex-col items-center justify-center space-y-4 text-sky-600">
          <Loader2 className="w-10 h-10 animate-spin" />
          <p className="font-medium animate-pulse">Scanning vector database and synthesizing answer...</p>
        </div>
      )}

      {result && !isQuerying && (
        <div className="space-y-6 animate-fade-in-up">
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-8 border-t-4 border-t-sky-500">
            <h2 className="text-xl font-bold text-gray-900 mb-6">Answer</h2>
            <div className="prose max-w-none text-gray-800 mb-8 whitespace-pre-wrap">
              {result.answer}
            </div>
            
            <div className="max-w-md bg-gray-50 p-4 rounded-lg border border-gray-100">
              <ConfidenceBar confidence={result.confidence} label="Response Confidence" />
            </div>
          </div>

          {result.findings_used && result.findings_used.length > 0 && (
            <div>
              <h3 className="text-lg font-bold text-gray-900 mb-4">Sources & Findings Referenced</h3>
              <div className="grid md:grid-cols-2 gap-4">
                {result.findings_used.map((ref, i) => (
                  <div key={i} className="bg-white p-4 rounded-lg border border-gray-200 shadow-sm flex flex-col">
                    <div className="mb-2">
                      <StatusBadge status={ref.classification} />
                    </div>
                    <p className="text-sm text-gray-800 mb-4 flex-1">"{ref.text}"</p>
                    <a 
                      href={ref.source_url} 
                      target="_blank" 
                      rel="noopener noreferrer"
                      className="text-xs text-sky-600 hover:text-sky-800 flex items-center gap-1 mt-auto pt-3 border-t border-gray-100"
                    >
                      <ExternalLink className="w-3 h-3" />
                      View Source
                    </a>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
