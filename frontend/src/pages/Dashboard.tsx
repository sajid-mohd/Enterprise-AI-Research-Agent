import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { Database, Search, MessageSquare, AlertTriangle, FileText, ArrowRight } from 'lucide-react';
import { getSessions, getFindings, getHealth } from '../services/api';
import { StatusBadge } from '../components/StatusBadge';
import type { SessionSummary } from '../types';

export const Dashboard: React.FC = () => {
  const [stats, setStats] = useState({ sessions: 0, findings: 0, sources: 0, contradictions: 0 });
  const [recentSessions, setRecentSessions] = useState<SessionSummary[]>([]);
  const [health, setHealth] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [sessionsData, findingsData, healthData] = await Promise.all([
          getSessions(1, 5),
          getFindings(), // Depending on implementation, you might need specific endpoints for counts
          getHealth().catch(() => null)
        ]);

        setRecentSessions(sessionsData.sessions || []);
        
        // Mocking counts from available data or you would use dedicated endpoints
        setStats({
          sessions: sessionsData.total || sessionsData.sessions?.length || 0,
          findings: findingsData.findings?.length || 0,
          sources: 124, // Mock if no endpoint
          contradictions: 12 // Mock if no endpoint
        });
        
        setHealth(healthData);
      } catch (err) {
        console.error("Failed to load dashboard data", err);
      } finally {
        setLoading(false);
      }
    };
    
    fetchData();
  }, []);

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-end">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Enterprise Research Intelligence</h1>
          <p className="text-gray-500 mt-1">AI-powered autonomous research and synthesis</p>
        </div>
        
        {health && (
          <div className="flex items-center gap-2 bg-white px-3 py-1.5 rounded-full shadow-sm border border-gray-200">
            <div className={`w-2 h-2 rounded-full ${health.status === 'ok' ? 'bg-green-500' : 'bg-red-500'}`}></div>
            <span className="text-xs font-medium text-gray-700">API Status: {health.status}</span>
          </div>
        )}
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {[
          { label: 'Total Sessions', value: stats.sessions, icon: Search, color: 'text-sky-500', bg: 'bg-sky-50' },
          { label: 'Total Findings', value: stats.findings, icon: FileText, color: 'text-green-500', bg: 'bg-green-50' },
          { label: 'Total Sources', value: stats.sources, icon: Database, color: 'text-purple-500', bg: 'bg-purple-50' },
          { label: 'Contradictions', value: stats.contradictions, icon: AlertTriangle, color: 'text-orange-500', bg: 'bg-orange-50' }
        ].map((stat, idx) => (
          <div key={idx} className="bg-white p-6 rounded-xl border border-gray-200 shadow-sm">
            <div className="flex items-center justify-between mb-4">
              <div className={`p-3 rounded-lg ${stat.bg}`}>
                <stat.icon className={`w-6 h-6 ${stat.color}`} />
              </div>
            </div>
            <div>
              <p className="text-3xl font-bold text-gray-900">{loading ? '-' : stat.value}</p>
              <p className="text-sm font-medium text-gray-500">{stat.label}</p>
            </div>
          </div>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Recent Sessions */}
        <div className="lg:col-span-2 bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
          <div className="p-6 border-b border-gray-100 flex justify-between items-center">
            <h2 className="text-lg font-semibold text-gray-900">Recent Research</h2>
            <Link to="/knowledge" className="text-sm font-medium text-sky-600 hover:text-sky-800 flex items-center gap-1">
              View all <ArrowRight className="w-4 h-4" />
            </Link>
          </div>
          <div className="divide-y divide-gray-100">
            {loading ? (
              <div className="p-8 text-center text-gray-500">Loading...</div>
            ) : recentSessions.length === 0 ? (
              <div className="p-8 text-center text-gray-500">No research sessions yet.</div>
            ) : (
              recentSessions.map(session => (
                <Link key={session.id} to={`/research/${session.id}`} className="block hover:bg-gray-50 p-6 transition-colors">
                  <div className="flex justify-between items-start mb-2">
                    <h3 className="text-base font-medium text-gray-900 line-clamp-1 flex-1 pr-4">{session.question}</h3>
                    <StatusBadge status={session.status} />
                  </div>
                  <div className="flex items-center gap-4 text-xs text-gray-500">
                    <span>{new Date(session.created_at).toLocaleString()}</span>
                    {session.finding_count !== undefined && <span>{session.finding_count} findings</span>}
                  </div>
                </Link>
              ))
            )}
          </div>
        </div>

        {/* Quick Actions */}
        <div className="space-y-4">
          <Link to="/research" className="block bg-sky-600 hover:bg-sky-700 text-white p-6 rounded-xl shadow-sm transition-colors group">
            <Search className="w-8 h-8 mb-4 opacity-80 group-hover:opacity-100 transition-opacity" />
            <h3 className="text-lg font-semibold mb-1">New Research</h3>
            <p className="text-sky-100 text-sm">Start a new deep-dive investigation.</p>
          </Link>
          
          <Link to="/query" className="block bg-white hover:bg-gray-50 border border-gray-200 p-6 rounded-xl shadow-sm transition-colors group">
            <MessageSquare className="w-8 h-8 mb-4 text-sky-600" />
            <h3 className="text-lg font-semibold text-gray-900 mb-1">Query Knowledge Base</h3>
            <p className="text-gray-500 text-sm">Ask questions across all past findings.</p>
          </Link>
        </div>
      </div>
    </div>
  );
};
