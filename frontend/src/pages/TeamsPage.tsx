import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Sidebar } from '../components/Sidebar';
import { MobileTabBar } from '../components/MobileTabBar';
import { graphApi } from '../api';
import { Users } from 'lucide-react';

// Placeholder Teams page — shows all teams from Neo4j
export const TeamsPage: React.FC = () => {
  const navigate = useNavigate();
  const [teams, setTeams] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);

  // Fetch teams via graph nodes
  useEffect(() => {
    graphApi.nodes('Team', 50).then((data: any) => {
      setTeams(data.nodes || []);
    }).catch(() => {
      setError(true);
    }).finally(() => setLoading(false));
  }, []);

  return (
    <div className="flex min-h-screen">
      <Sidebar />
      <main className="page-with-sidebar flex-1">
        <div className="page-content p-6">
          <h1 className="text-2xl font-bold text-gray-900 mb-6">Teams</h1>
          {loading ? (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {[...Array(4)].map((_, i) => <div key={i} className="card h-32 animate-pulse bg-gray-100" />)}
            </div>
          ) : error ? (
            <div className="card text-center py-12">
              <p className="font-semibold text-gray-700">Teams could not be loaded.</p>
              <p className="text-sm text-gray-500 mt-1">Start Neo4j on localhost:7687 and try again.</p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {teams.map((team) => (
                <button
                  key={team.id}
                  id={`team-card-${team.label}`}
                  onClick={() => navigate(`/entities/team/${encodeURIComponent(team.label)}`)}
                  className="card card-hover text-left group"
                >
                  <div className="flex items-center gap-3 mb-3">
                    <div className="w-10 h-10 rounded-xl bg-teal-100 flex items-center justify-center">
                      <Users size={18} className="text-teal-600" />
                    </div>
                    <div>
                      <h3 className="font-semibold text-gray-900">{team.label}</h3>
                      <p className="text-xs text-gray-400">Team</p>
                    </div>
                  </div>
                  {team.properties?.description && (
                    <p className="text-sm text-gray-500 line-clamp-2">{team.properties.description}</p>
                  )}
                </button>
              ))}
            </div>
          )}
        </div>
      </main>
      <MobileTabBar />
    </div>
  );
};
