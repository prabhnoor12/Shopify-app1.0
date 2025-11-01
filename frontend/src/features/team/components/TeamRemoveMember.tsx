import React, { useState, useRef, useEffect } from 'react';
import { removeTeamMember, getMyTeams, getTeamById } from '../../../api/teamApi';
import { Card, Button, Select } from '@shopify/polaris';
import './TeamRemoveMember.css';

interface RemoveProps {
  teamId?: string | number;
  userId?: string | number;
}

const TeamRemoveMember: React.FC<RemoveProps> = ({ teamId: propTeamId, userId: propUserId }) => {
  const [teams, setTeams] = useState<any[]>([]);
  const [selectedTeamId, setSelectedTeamId] = useState(propTeamId ? String(propTeamId) : '');
  const [members, setMembers] = useState<any[]>([]);
  const [selectedUserId, setSelectedUserId] = useState(propUserId ? String(propUserId) : '');
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [loading, setLoading] = useState(false);
  const [confirm, setConfirm] = useState(false);
  const successTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    getMyTeams()
      .then(setTeams)
      .catch(() => setError('Failed to load teams'));
    if (propTeamId) setSelectedTeamId(String(propTeamId));
    if (propUserId) setSelectedUserId(String(propUserId));
  }, [propTeamId, propUserId]);

  useEffect(() => {
    if (selectedTeamId) {
      getTeamById(selectedTeamId)
        .then(team => setMembers(team.members || []))
        .catch(() => setError('Failed to load team members'));
      setSelectedUserId('');
    } else {
      setMembers([]);
      setSelectedUserId('');
    }
  }, [selectedTeamId]);

  const handleRemove = async () => {
    setError('');
    setSuccess('');
    setLoading(true);
    try {
      await removeTeamMember(selectedTeamId, selectedUserId);
      setSuccess('Member removed!');
      setConfirm(false);
      setMembers(members.filter(m => String(m.id) !== String(selectedUserId)));
      setSelectedUserId('');
    } catch (e: any) {
      if (e?.response?.data?.detail) {
        setError(e.response.data.detail);
      } else if (e?.message) {
        setError(e.message);
      } else if (typeof e === 'string') {
        setError(e);
      } else {
        setError('Failed to remove member');
      }
    }
    setLoading(false);
  };

  React.useEffect(() => {
    if (success) {
      successTimeoutRef.current = setTimeout(() => setSuccess(''), 4000);
    }
    return () => {
      if (successTimeoutRef.current) clearTimeout(successTimeoutRef.current);
    };
  }, [success]);

  return (
    <Card>
      <div className="team-remove-content">
        <h2 className="team-remove-title">Remove Team Member</h2>
        {error && <div className="team-remove-error" aria-live="assertive">{error}</div>}
        {success && <div className="team-remove-success" role="status" aria-live="polite">{success}</div>}
        <div className="team-remove-fields">
          <Select
            label="Select Team"
            options={Array.isArray(teams) && teams.length ? teams.map(t => ({ label: t.name || t.id, value: String(t.id) })) : [{ label: 'No teams available', value: '' }]}
            value={selectedTeamId}
            onChange={v => setSelectedTeamId(v)}
            disabled={!Array.isArray(teams) || teams.length === 0 || loading}
            requiredIndicator
            // required
            aria-label="Select Team"
          />
          <Select
            label="Select Member"
            options={Array.isArray(members) && members.length ? members.map(m => ({ label: m.email || m.name || m.id, value: String(m.id) })) : [{ label: 'No members available', value: '' }]}
            value={selectedUserId}
            onChange={v => setSelectedUserId(v)}
            disabled={!Array.isArray(members) || members.length === 0 || loading || !selectedTeamId}
            requiredIndicator
            // required
            aria-label="Select Member to Remove"
          />
        </div>
        {confirm ? (
          <div className="team-remove-confirm">
            <p className="team-remove-confirm-text">Are you sure you want to remove this member? This action cannot be undone.</p>
            <Button onClick={handleRemove} loading={loading} tone="critical" accessibilityLabel="Confirm remove member" disabled={loading || !selectedTeamId || !selectedUserId}>
              Confirm Remove
            </Button>
            <Button onClick={() => setConfirm(false)} disabled={loading}>
              Cancel
            </Button>
          </div>
        ) : (
          <Button onClick={() => setConfirm(true)} tone="critical" accessibilityLabel="Remove team member" disabled={loading || !selectedTeamId || !selectedUserId}>
            Remove Member
          </Button>
        )}
      </div>
    </Card>
  );
};

export default TeamRemoveMember;
