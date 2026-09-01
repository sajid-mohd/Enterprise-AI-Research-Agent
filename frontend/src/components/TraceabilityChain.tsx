import React, { useState } from 'react';
import { ChevronDown, ChevronRight, Link as LinkIcon } from 'lucide-react';
import type { Conclusion, Finding } from '../types';

interface TraceabilityChainProps {
  conclusion: Conclusion;
  findings: Finding[];
}

export const TraceabilityChain: React.FC<TraceabilityChainProps> = ({ conclusion, findings }) => {
  const [expandedFindings, setExpandedFindings] = useState<Record<string, boolean>>({});

  const toggleFinding = (id: string) => {
    setExpandedFindings(prev => ({
      ...prev,
      [id]: !prev[id]
    }));
  };

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
      <h3 className="text-lg font-semibold text-gray-900 mb-6 flex items-center gap-2">
        <LinkIcon className="w-5 h-5 text-sky-500" />
        Traceability Chain
      </h3>
      
      <div className="space-y-4">
        {/* Conclusion Node */}
        <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
          <div className="text-sm font-semibold text-gray-500 uppercase mb-2">Conclusion</div>
          <p className="text-gray-800">{conclusion.text}</p>
        </div>
        
        {/* Down Arrow */}
        <div className="flex justify-center text-gray-400 py-2">
          <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 14l-7 7m0 0l-7-7m7 7V3"></path></svg>
        </div>
        
        {/* Supporting Findings */}
        <div className="space-y-3">
          <div className="text-sm font-semibold text-gray-500 uppercase">Supporting Findings & Sources</div>
          {conclusion.supporting_findings.map(finding => {
            const isExpanded = expandedFindings[finding.id];
            // Find full finding object if not fully populated in conclusion
            const fullFinding = findings.find(f => f.id === finding.id) || finding;
            
            return (
              <div key={finding.id} className="border border-gray-200 rounded-lg overflow-hidden">
                <button 
                  onClick={() => toggleFinding(finding.id)}
                  className="w-full text-left px-4 py-3 bg-white hover:bg-gray-50 flex items-start justify-between gap-4"
                >
                  <p className="text-sm text-gray-800 flex-1">{fullFinding.text}</p>
                  {isExpanded ? <ChevronDown className="w-5 h-5 text-gray-400" /> : <ChevronRight className="w-5 h-5 text-gray-400" />}
                </button>
                
                {isExpanded && fullFinding.source && (
                  <div className="px-4 py-3 bg-gray-50 border-t border-gray-200 pl-8">
                    <div className="relative">
                      {/* L-shaped connector */}
                      <div className="absolute -left-6 top-0 w-4 h-4 border-l-2 border-b-2 border-gray-300 rounded-bl"></div>
                      
                      <div className="text-xs font-semibold text-gray-500 uppercase mb-1">Source</div>
                      <a 
                        href={fullFinding.source.url} 
                        target="_blank" 
                        rel="noopener noreferrer"
                        className="text-sm text-sky-600 hover:text-sky-800 font-medium block truncate"
                      >
                        {fullFinding.source.title}
                      </a>
                      <div className="text-xs text-gray-500 mt-1 flex gap-3">
                        <span>{fullFinding.source.domain}</span>
                        <span>Reliability: {Math.round(fullFinding.source.reliability_score * 100)}%</span>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
};
