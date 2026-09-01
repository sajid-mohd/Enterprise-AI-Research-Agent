import React from 'react';
import { Loader2 } from 'lucide-react';
import type { SessionStatus, Classification } from '../types';

interface StatusBadgeProps {
  status: SessionStatus | Classification | string;
}

export const StatusBadge: React.FC<StatusBadgeProps> = ({ status }) => {
  const getStyle = () => {
    switch (status) {
      case 'completed':
      case 'supporting':
        return 'bg-green-100 text-green-800 border-green-200';
      case 'failed':
      case 'contradicting':
        return 'bg-red-100 text-red-800 border-red-200';
      case 'emerging':
        return 'bg-blue-100 text-blue-800 border-blue-200';
      case 'uncertain':
      case 'pending':
        return 'bg-gray-100 text-gray-800 border-gray-200';
      default:
        // For decomposing, searching, extracting, analyzing, synthesizing
        return 'bg-sky-100 text-sky-800 border-sky-200';
    }
  };

  const isSpinning = ['decomposing', 'searching', 'extracting', 'analyzing', 'synthesizing'].includes(status);

  return (
    <span className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium border ${getStyle()} capitalize`}>
      {isSpinning && <Loader2 className="w-3 h-3 animate-spin" />}
      {status}
    </span>
  );
};
