import React, { useEffect, useState } from 'react';
import { getMyTeams } from '../../../api/teamApi';
import { Card, Spinner, InlineError } from '@shopify/polaris';
import './TeamList.css';
import type { Team } from '../../../api/teamApi';

const TeamList: React.FC = () => {
  const [teams, setTeams] = useState<Team[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    (async () => {
      setLoading(true);
      try {
        const data = await getMyTeams();
        setTeams(data);
        setError('');
      } catch (e) {
        setError('Failed to load teams');
      }
      setLoading(false);
    })();
  }, []);

  return (
    <Card>
      <h2>My Teams</h2>
      {loading ? (
        <div className="teamlist-spinner"><Spinner accessibilityLabel="Loading teams" size="large" /></div>
      ) : error ? (
        <InlineError message={error} fieldID="teamlist-error" />
      ) : teams.length === 0 ? (
        <div className="teamlist-empty" role="status">You are not a member of any teams yet.</div>
      ) : (
        <table className="teamlist-table" aria-label="Team list">
          <thead>
            <tr>
              <th scope="col">Name</th>
              <th scope="col">Owner</th>
              <th scope="col">Members</th>
              <th scope="col">Created</th>
            </tr>
          </thead>
          <tbody>
            {teams.map(team => (
              <tr key={team.id}>
                <td>{team.name}</td>
                <td>{team.owner_id}</td>
                <td>{team.members?.length ?? 0}</td>
                <td>{team.created_at ? new Date(team.created_at).toLocaleDateString() : ''}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </Card>
  );
};

export default TeamList;
