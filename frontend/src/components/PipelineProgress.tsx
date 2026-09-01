import React from 'react';
import { CheckCircle2, Circle, Loader2, XCircle } from 'lucide-react';
import type { SessionStatus, SubQuestion } from '../types';

interface PipelineProgressProps {
  status: SessionStatus;
  subquestions?: SubQuestion[];
}

export const PipelineProgress: React.FC<PipelineProgressProps> = ({ status, subquestions }) => {
  const steps: { key: SessionStatus | 'received'; label: string; activeAt: SessionStatus[] }[] = [
    { key: 'received', label: 'Question Received', activeAt: ['pending'] },
    { key: 'decomposing', label: 'Decomposing question', activeAt: ['decomposing'] },
    { key: 'searching', label: 'Searching sources', activeAt: ['searching'] },
    { key: 'extracting', label: 'Extracting findings', activeAt: ['extracting'] },
    { key: 'analyzing', label: 'Analyzing contradictions', activeAt: ['analyzing'] },
    { key: 'synthesizing', label: 'Synthesizing conclusion', activeAt: ['synthesizing'] },
    { key: 'completed', label: 'Research complete', activeAt: ['completed'] }
  ];

  const orderedStatuses: (SessionStatus | 'received')[] = ['received', 'pending', 'decomposing', 'searching', 'extracting', 'analyzing', 'synthesizing', 'completed'];
  
  const currentStepIndex = orderedStatuses.indexOf(status === 'pending' ? 'received' : status);

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
      <h3 className="text-lg font-semibold text-gray-900 mb-6">Research Pipeline</h3>
      <div className="relative">
        {/* Vertical line connecting steps */}
        <div className="absolute left-[15px] top-4 bottom-4 w-0.5 bg-gray-200"></div>
        
        <div className="space-y-6 relative">
          {steps.map((step) => {
            const stepIndex = orderedStatuses.indexOf(step.key);
            let state: 'done' | 'active' | 'pending' | 'failed' = 'pending';
            
            if (status === 'failed' && currentStepIndex === -1) {
              // If failed but we don't know where, just mark current as failed
              state = 'failed';
            } else if (status === 'failed') {
              if (stepIndex < orderedStatuses.indexOf('completed')) state = 'done'; // Simplification: actual failure step needs tracking, assuming it fails AT the current state
              // Let's assume if status is failed, we mark the one before as done, current as failed
            }
            
            if (status !== 'failed') {
              if (step.key === 'completed' && status === 'completed') state = 'done';
              else if (step.key === 'received' && status !== 'pending') state = 'done';
              else if (step.activeAt.includes(status)) state = 'active';
              else if (orderedStatuses.indexOf(step.key) < currentStepIndex && step.key !== 'completed') state = 'done';
            }

            // Fix for failed state logic
            if (status === 'failed' && step.activeAt.includes('synthesizing')) {
               // Placeholder logic for failure display
               state = 'failed';
            }

            return (
              <div key={step.key} className="flex gap-4 items-start">
                <div className="relative z-10 flex-shrink-0 bg-white">
                  {state === 'done' && <CheckCircle2 className="w-8 h-8 text-green-500" />}
                  {state === 'active' && <Loader2 className="w-8 h-8 text-sky-500 animate-spin" />}
                  {state === 'pending' && <Circle className="w-8 h-8 text-gray-300" />}
                  {status === 'failed' && step.key === status && <XCircle className="w-8 h-8 text-red-500" />}
                  {status === 'failed' && state === 'failed' && <XCircle className="w-8 h-8 text-red-500" />}
                </div>
                <div className="pt-1">
                  <p className={`font-medium ${state === 'active' ? 'text-sky-700' : state === 'done' ? 'text-gray-900' : 'text-gray-500'}`}>
                    {step.label}
                  </p>
                  {step.key === 'decomposing' && subquestions && subquestions.length > 0 && (
                    <div className="mt-2 text-sm text-gray-600">
                      <ul className="list-disc pl-4 space-y-1">
                        {subquestions.map(sq => (
                          <li key={sq.id}>{sq.question}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
};
