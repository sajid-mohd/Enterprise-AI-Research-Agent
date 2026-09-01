import React from 'react';
import { ExternalLink } from 'lucide-react';
import type { Finding } from '../types';
import { StatusBadge } from './StatusBadge';
import { ConfidenceBar } from './ConfidenceBar';

interface FindingCardProps {
  finding: Finding;
  showSource?: boolean;
}

export const FindingCard: React.FC<FindingCardProps> = ({ finding, showSource = true }) => {
  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4 hover:shadow-md transition-shadow">
      <div className="flex justify-between items-start mb-3">
        <StatusBadge status={finding.classification} />
        <span className="text-xs text-gray-500">{new Date(finding.created_at).toLocaleDateString()}</span>
      </div>
      <p className="text-sm text-gray-800 mb-4">{finding.text}</p>
      <div className="mb-4">
        <ConfidenceBar confidence={finding.confidence} />
      </div>
      {showSource && finding.source && (
        <div className="pt-3 border-t border-gray-100">
          <a 
            href={finding.source.url} 
            target="_blank" 
            rel="noopener noreferrer"
            className="text-xs text-sky-600 hover:text-sky-800 flex items-center gap-1 inline-flex"
          >
            <ExternalLink className="w-3 h-3" />
            {finding.source.domain}
          </a>
        </div>
      )}
    </div>
  );
};
