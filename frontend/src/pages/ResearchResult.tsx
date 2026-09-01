import React, { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import { AlertCircle, Target, BookOpen, AlertTriangle } from 'lucide-react';
import { getSession } from '../services/api';
import { StatusBadge } from '../components/StatusBadge';
import { PipelineProgress } from '../components/PipelineProgress';
import { ConfidenceBar } from '../components/ConfidenceBar';
import { FindingCard } from '../components/FindingCard';
import { ContradictionCard } from '../components/ContradictionCard';
import { SourceCard } from '../components/SourceCard';
import { TraceabilityChain } from '../components/TraceabilityChain';
import type { SessionDetail } from '../types';

export const ResearchResult: React.FC = () => {
  const { sessionId } = useParams<{sessionId: string}>();
  const [session, setSession] = useState<SessionDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState('all');

  useEffect(() => {
    if (!sessionId) return;
    
    let mounted = true;
    
    const fetchSession = async () => {
      try {
        const data = await getSession(sessionId);
        if (mounted) {
          setSession(data);
          setLoading(false);
        }
      } catch (err) {
        if (mounted) {
          setError('Failed to load session details');
          setLoading(false);
        }
      }
    };
    
    fetchSession();

    // Poll if not completed/failed
    const interval = setInterval(async () => {
      if (session && ['completed', 'failed'].includes(session.status)) {
        clearInterval(interval);
        return;
      }
      
      try {
        const data = await getSession(sessionId);
        if (mounted) setSession(data);
        if (['completed', 'failed'].includes(data.status)) clearInterval(interval);
      } catch (err) {
        // ignore polling errors
      }
    }, 2000);

    return () => {
      mounted = false;
      clearInterval(interval);
    };
  }, [sessionId, session?.status]);

  if (loading) return <div className="flex justify-center p-12"><div className="animate-spin rounded-full h-8 w-8 border-b-2 border-sky-600"></div></div>;
  if (error || !session) return <div className="bg-red-50 text-red-600 p-6 rounded-lg text-center">{error || 'Session not found'}</div>;

  const isCompleted = session.status === 'completed';
  const isFailed = session.status === 'failed';
  const isRunning = !isCompleted && !isFailed;

  const filteredFindings = session.findings?.filter(f => activeTab === 'all' || f.classification === activeTab) || [];

  return (
    <div className="space-y-8 max-w-6xl mx-auto">
      {/* Header Banner */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 md:p-8">
        <div className="flex flex-col md:flex-row md:items-start justify-between gap-4 mb-4">
          <h1 className="text-2xl font-bold text-gray-900 leading-tight flex-1">{session.question}</h1>
          <div className="flex-shrink-0">
            <StatusBadge status={session.status} />
          </div>
        </div>
        <div className="text-sm text-gray-500">Started: {new Date(session.created_at).toLocaleString()}</div>
      </div>

      {isRunning && (
        <PipelineProgress status={session.status} subquestions={session.subquestions} />
      )}

      {isFailed && (
        <div className="bg-red-50 border border-red-200 p-6 rounded-xl flex gap-4">
          <AlertCircle className="text-red-500 w-6 h-6 flex-shrink-0" />
          <div>
            <h3 className="font-semibold text-red-900 mb-1">Research Failed</h3>
            <p className="text-red-800">{session.error_message || 'An unknown error occurred during the research pipeline.'}</p>
          </div>
        </div>
      )}

      {isCompleted && session.conclusion && (
        <div className="space-y-8">
          {/* Conclusion Section */}
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-8 border-t-4 border-t-sky-500">
            <h2 className="text-xl font-bold text-gray-900 mb-6 flex items-center gap-2">
              <Target className="text-sky-500 w-6 h-6" /> Executive Synthesis
            </h2>
            
            <div className="prose max-w-none text-gray-800 mb-8">
              <p className="text-lg leading-relaxed">{session.conclusion.text}</p>
            </div>
            
            <div className="mb-8 max-w-md">
              <ConfidenceBar confidence={session.conclusion.confidence} label="Overall Confidence" />
            </div>
            
            <div className="grid md:grid-cols-2 gap-8">
              <div>
                <h3 className="font-semibold text-gray-900 mb-3 flex items-center gap-2">
                  <CheckCircle className="text-green-500 w-5 h-5" /> Key Points
                </h3>
                <ul className="space-y-2">
                  {session.conclusion.key_points.map((pt, i) => (
                    <li key={i} className="flex gap-2 text-gray-700">
                      <span className="text-green-500 mt-1">•</span>
                      <span>{pt}</span>
                    </li>
                  ))}
                </ul>
              </div>
              
              {session.conclusion.limitations.length > 0 && (
                <div>
                  <h3 className="font-semibold text-gray-900 mb-3 flex items-center gap-2">
                    <AlertTriangle className="text-orange-500 w-5 h-5" /> Limitations
                  </h3>
                  <ul className="space-y-2">
                    {session.conclusion.limitations.map((pt, i) => (
                      <li key={i} className="flex gap-2 text-gray-700">
                        <span className="text-orange-500 mt-1">•</span>
                        <span>{pt}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          </div>

          <TraceabilityChain conclusion={session.conclusion} findings={session.findings || []} />

          {/* Subquestions */}
          {session.subquestions && session.subquestions.length > 0 && (
            <div>
              <h2 className="text-xl font-bold text-gray-900 mb-4 flex items-center gap-2">
                <Target className="text-gray-400 w-6 h-6" /> Research Vectors
              </h2>
              <div className="grid gap-3">
                {session.subquestions.map(sq => (
                  <div key={sq.id} className="bg-white p-4 rounded-lg border border-gray-200 shadow-sm flex items-start gap-3">
                    <div className="mt-1 flex-shrink-0 text-sky-500"><BookOpen className="w-5 h-5" /></div>
                    <div>
                      <p className="font-medium text-gray-900">{sq.question}</p>
                      <p className="text-sm text-gray-500 mt-1">{sq.research_intent}</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Findings */}
          <div>
            <div className="flex flex-col sm:flex-row sm:items-center justify-between mb-4 gap-4">
              <h2 className="text-xl font-bold text-gray-900">Key Findings</h2>
              
              <div className="flex gap-2 overflow-x-auto pb-2 sm:pb-0">
                {['all', 'supporting', 'contradicting', 'emerging', 'uncertain'].map(tab => (
                  <button
                    key={tab}
                    onClick={() => setActiveTab(tab)}
                    className={`px-3 py-1.5 rounded-full text-sm font-medium capitalize whitespace-nowrap ${
                      activeTab === tab 
                        ? 'bg-sky-600 text-white' 
                        : 'bg-white border border-gray-200 text-gray-600 hover:bg-gray-50'
                    }`}
                  >
                    {tab}
                  </button>
                ))}
              </div>
            </div>
            
            <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
              {filteredFindings.length === 0 ? (
                <div className="col-span-full p-8 text-center bg-gray-50 rounded-lg text-gray-500 border border-gray-200">
                  No findings match this filter.
                </div>
              ) : (
                filteredFindings.map(finding => (
                  <FindingCard key={finding.id} finding={finding} />
                ))
              )}
            </div>
          </div>

          {/* Contradictions */}
          {session.contradictions && session.contradictions.length > 0 && (
            <div>
              <h2 className="text-xl font-bold text-gray-900 mb-4 flex items-center gap-2">
                <AlertTriangle className="text-red-500 w-6 h-6" /> Conflicting Information Detected
              </h2>
              <div className="grid lg:grid-cols-2 gap-6">
                {session.contradictions.map(contradiction => (
                  <ContradictionCard key={contradiction.id} contradiction={contradiction} />
                ))}
              </div>
            </div>
          )}

          {/* Sources */}
          {session.sources && session.sources.length > 0 && (
            <div>
              <h2 className="text-xl font-bold text-gray-900 mb-4">Sources Analyzed</h2>
              <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
                {session.sources.map(source => (
                  <SourceCard 
                    key={source.id} 
                    source={source} 
                    findingCount={session.findings?.filter(f => f.source?.id === source.id).length}
                  />
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

// Quick fix for missing icon
const CheckCircle: React.FC<{className?: string}> = ({className}) => (
  <svg className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7"></path></svg>
);
