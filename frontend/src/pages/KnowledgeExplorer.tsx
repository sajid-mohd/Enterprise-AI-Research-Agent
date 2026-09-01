import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { getSessions, getFindings, getContradictions } from '../services/api';
import { StatusBadge } from '../components/StatusBadge';
import { FindingCard } from '../components/FindingCard';
import { ContradictionCard } from '../components/ContradictionCard';
import type { SessionSummary, Finding, Contradiction } from '../types';

export const KnowledgeExplorer: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'sessions' | 'findings' | 'contradictions'>('sessions');
  const [sessions, setSessions] = useState<SessionSummary[]>([]);
  const [findings, setFindings] = useState<Finding[]>([]);
  const [contradictions, setContradictions] = useState<Contradiction[]>([]);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      try {
        if (activeTab === 'sessions') {
          const res = await getSessions(1, 50);
          setSessions(res.sessions || []);
        } else if (activeTab === 'findings') {
          const res = await getFindings();
          setFindings(res.findings || []);
        } else if (activeTab === 'contradictions') {
          const res = await getContradictions();
          setContradictions(res.contradictions || []);
        }
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    };
    
    fetchData();
  }, [activeTab]);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900 mb-2">Knowledge Explorer</h1>
        <p className="text-gray-500">Browse the accumulated intelligence base.</p>
      </div>

      <div className="border-b border-gray-200">
        <nav className="-mb-px flex space-x-8">
          {[
            { id: 'sessions', label: 'Research Sessions' },
            { id: 'findings', label: 'All Findings' },
            { id: 'contradictions', label: 'Contradictions' },
          ].map(tab => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as any)}
              className={`whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm transition-colors ${
                activeTab === tab.id
                  ? 'border-sky-500 text-sky-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              {tab.label}
            </button>
          ))}
        </nav>
      </div>

      <div className="pt-4">
        {loading ? (
          <div className="flex justify-center p-12"><div className="animate-spin rounded-full h-8 w-8 border-b-2 border-sky-600"></div></div>
        ) : (
          <>
            {activeTab === 'sessions' && (
              <div className="bg-white shadow-sm border border-gray-200 rounded-lg overflow-hidden">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Question</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Date</th>
                      <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Action</th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {sessions.map(session => (
                      <tr key={session.id} className="hover:bg-gray-50">
                        <td className="px-6 py-4 whitespace-nowrap overflow-hidden text-ellipsis max-w-md">
                          <div className="text-sm font-medium text-gray-900">{session.question}</div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <StatusBadge status={session.status} />
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {new Date(session.created_at).toLocaleDateString()}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                          <button onClick={() => navigate(`/research/${session.id}`)} className="text-sky-600 hover:text-sky-900">
                            View
                          </button>
                        </td>
                      </tr>
                    ))}
                    {sessions.length === 0 && (
                      <tr><td colSpan={4} className="px-6 py-8 text-center text-gray-500">No sessions found.</td></tr>
                    )}
                  </tbody>
                </table>
              </div>
            )}

            {activeTab === 'findings' && (
              <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
                {findings.map(finding => (
                  <FindingCard key={finding.id} finding={finding} showSource={true} />
                ))}
                {findings.length === 0 && (
                  <div className="col-span-full py-12 text-center text-gray-500 bg-gray-50 rounded-lg border border-gray-200">
                    No findings accumulated yet.
                  </div>
                )}
              </div>
            )}

            {activeTab === 'contradictions' && (
              <div className="grid md:grid-cols-2 gap-6">
                {contradictions.map(contradiction => (
                  <ContradictionCard key={contradiction.id} contradiction={contradiction} />
                ))}
                {contradictions.length === 0 && (
                  <div className="col-span-full py-12 text-center text-gray-500 bg-gray-50 rounded-lg border border-gray-200">
                    No contradictions detected across research sessions.
                  </div>
                )}
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
};
