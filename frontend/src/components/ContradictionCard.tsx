import React from 'react';
import { AlertTriangle } from 'lucide-react';
import type { Contradiction } from '../types';
import { ConfidenceBar } from './ConfidenceBar';

interface ContradictionCardProps {
  contradiction: Contradiction;
}

export const ContradictionCard: React.FC<ContradictionCardProps> = ({ contradiction }) => {
  const getSeverityStyle = () => {
    switch (contradiction.severity) {
      case 'low': return 'bg-yellow-100 text-yellow-800';
      case 'medium': return 'bg-orange-100 text-orange-800';
      case 'high': return 'bg-red-100 text-red-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-5">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <AlertTriangle className={`w-5 h-5 ${contradiction.severity === 'high' ? 'text-red-500' : 'text-orange-500'}`} />
          <h3 className="font-semibold text-gray-900">Conflict Detected</h3>
        </div>
        <span className={`text-xs px-2.5 py-0.5 rounded-full font-medium ${getSeverityStyle()} uppercase tracking-wide`}>
          {contradiction.severity} Severity
        </span>
      </div>
      
      <p className="text-sm text-gray-700 mb-6 bg-gray-50 p-3 rounded">{contradiction.description}</p>
      
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
        <div className="border border-gray-200 rounded p-3">
          <div className="text-xs font-semibold text-gray-500 uppercase mb-2">Finding A</div>
          <p className="text-sm text-gray-800">{contradiction.finding_a.text}</p>
        </div>
        <div className="border border-gray-200 rounded p-3">
          <div className="text-xs font-semibold text-gray-500 uppercase mb-2">Finding B</div>
          <p className="text-sm text-gray-800">{contradiction.finding_b.text}</p>
        </div>
      </div>
      
      <div className="pt-2">
        <ConfidenceBar confidence={contradiction.confidence} label="Contradiction Confidence" />
      </div>
    </div>
  );
};
