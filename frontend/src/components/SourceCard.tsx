import React from 'react';
import { ExternalLink, FileText, Globe, Activity } from 'lucide-react';
import type { Source } from '../types';

interface SourceCardProps {
  source: Source;
  findingCount?: number;
}

export const SourceCard: React.FC<SourceCardProps> = ({ source, findingCount }) => {
  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
      <div className="flex items-start justify-between mb-2">
        <div className="flex gap-2 mb-2">
          <span className="inline-flex items-center gap-1 bg-gray-100 text-gray-700 text-xs px-2 py-0.5 rounded">
            <Globe className="w-3 h-3" />
            {source.domain}
          </span>
          <span className="inline-flex items-center gap-1 bg-gray-100 text-gray-700 text-xs px-2 py-0.5 rounded">
            <FileText className="w-3 h-3" />
            {source.source_type}
          </span>
        </div>
        {findingCount !== undefined && (
          <span className="bg-sky-100 text-sky-800 text-xs px-2 py-0.5 rounded-full font-medium">
            {findingCount} findings
          </span>
        )}
      </div>
      
      <a 
        href={source.url} 
        target="_blank" 
        rel="noopener noreferrer"
        className="text-base font-medium text-sky-600 hover:text-sky-800 line-clamp-2 mb-3 flex items-start gap-1"
      >
        <span>{source.title}</span>
        <ExternalLink className="w-4 h-4 flex-shrink-0 mt-1" />
      </a>
      
      <div className="flex flex-wrap items-center justify-between text-xs text-gray-500 pt-3 border-t border-gray-100">
        <span>{new Date(source.retrieved_at).toLocaleDateString()}</span>
        <span>{source.word_count.toLocaleString()} words</span>
        <div className="flex items-center gap-1">
          <Activity className="w-3 h-3" />
          <span>Reliability: {Math.round(source.reliability_score * 100)}%</span>
        </div>
      </div>
    </div>
  );
};
