import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Search, Loader2, ArrowRight } from 'lucide-react';
import { startResearch, getSession, getSessions } from '../services/api';
import { PipelineProgress } from '../components/PipelineProgress';
import type { SessionDetail, SessionSummary } from '../types';

export const ResearchConsole: React.FC = () => {
  const [question, setQuestion] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [currentSessionId, setCurrentSessionId] = useState<string | null>(null);
  const [currentSession, setCurrentSession] = useState<SessionDetail | null>(null);
  const [history, setHistory] = useState<SessionSummary[]>([]);
  const navigate = useNavigate();

  useEffect(() => {
    getSessions(1, 10).then(data => setHistory(data.sessions || [])).catch(console.error);
  }, []);

  useEffect(() => {
    if (!currentSessionId) return;

    // Initial fetch
    let mounted = true;
    const fetchSession = async () => {
      try {
        const data = await getSession(currentSessionId);
        if (mounted) setCurrentSession(data);
      } catch (err) {
        console.error(err);
      }
    };
    
    fetchSession();

    // Polling
    const interval = setInterval(async () => {
      if (currentSession && ['completed', 'failed'].includes(currentSession.status)) {
        clearInterval(interval);
        return;
      }
      
      try {
        const data = await getSession(currentSessionId);
        if (mounted) setCurrentSession(data);
        
        if (['completed', 'failed'].includes(data.status)) {
          clearInterval(interval);
        }
      } catch (err) {
        console.error(err);
      }
    }, 2000);

    return () => {
      mounted = false;
      clearInterval(interval);
    };
  }, [currentSessionId, currentSession?.status]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!question.trim()) return;

    setIsSubmitting(true);
    try {
      const response = await startResearch(question);
      setCurrentSessionId(response.session_id);
      setQuestion('');
    } catch (err) {
      console.error(err);
      alert('Failed to start research');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto space-y-8">
      <div>
        <h1 className="text-2xl font-bold text-gray-900 mb-2">Research Console</h1>
        <p className="text-gray-500">Initiate autonomous deep research on any topic.</p>
      </div>

      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
        <form onSubmit={handleSubmit}>
          <div className="relative">
            <Search className="absolute left-4 top-4 text-gray-400 w-6 h-6" />
            <textarea
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              placeholder="How is AI transforming healthcare logistics?"
              className="w-full pl-12 pr-4 py-4 rounded-lg border border-gray-300 focus:ring-2 focus:ring-sky-500 focus:border-sky-500 resize-none h-32 text-lg transition-shadow"
              disabled={isSubmitting || (currentSession !== null && !['completed', 'failed'].includes(currentSession.status))}
            />
          </div>
          <div className="mt-4 flex justify-end">
            <button
              type="submit"
              disabled={!question.trim() || isSubmitting || (currentSession !== null && !['completed', 'failed'].includes(currentSession.status))}
              className="bg-sky-600 hover:bg-sky-700 text-white px-6 py-2.5 rounded-md font-medium flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              {isSubmitting ? <Loader2 className="w-5 h-5 animate-spin" /> : null}
              Start Research
            </button>
          </div>
        </form>
      </div>

      {currentSession && (
        <div className="animate-fade-in-up">
          <PipelineProgress status={currentSession.status} subquestions={currentSession.subquestions} />
          
          {['completed', 'failed'].includes(currentSession.status) && (
            <div className="mt-6 flex justify-center">
              <button
                onClick={() => navigate(`/research/${currentSession.id}`)}
                className="bg-white border border-gray-300 hover:bg-gray-50 text-gray-800 px-6 py-3 rounded-lg font-medium flex items-center gap-2 shadow-sm transition-colors"
              >
                View Full Results <ArrowRight className="w-5 h-5" />
              </button>
            </div>
          )}
        </div>
      )}

      {/* History */}
      {!currentSession && history.length > 0 && (
        <div>
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Recent History</h3>
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden divide-y divide-gray-100">
            {history.map(session => (
              <button
                key={session.id}
                onClick={() => navigate(`/research/${session.id}`)}
                className="w-full text-left p-4 hover:bg-gray-50 transition-colors flex justify-between items-center"
              >
                <div className="flex-1 pr-4">
                  <p className="font-medium text-gray-900 line-clamp-1">{session.question}</p>
                  <p className="text-xs text-gray-500 mt-1">{new Date(session.created_at).toLocaleString()}</p>
                </div>
                <ArrowRight className="w-5 h-5 text-gray-400" />
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};
