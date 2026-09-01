import React from 'react';

interface ConfidenceBarProps {
  confidence: number;
  label?: string;
}

export const ConfidenceBar: React.FC<ConfidenceBarProps> = ({ confidence, label = "Confidence" }) => {
  const percentage = Math.round(confidence * 100);
  
  let color = 'bg-green-500';
  if (confidence < 0.4) color = 'bg-red-500';
  else if (confidence <= 0.65) color = 'bg-yellow-500';

  return (
    <div className="w-full">
      <div className="flex justify-between items-center mb-1">
        <span className="text-xs font-medium text-gray-700">{label}</span>
        <span className="text-xs font-medium text-gray-700">{percentage}%</span>
      </div>
      <div className="w-full bg-gray-200 rounded-full h-2">
        <div className={`h-2 rounded-full ${color}`} style={{ width: `${percentage}%` }}></div>
      </div>
    </div>
  );
};
