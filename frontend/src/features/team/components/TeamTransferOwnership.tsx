import React, { useState, useEffect, useRef } from 'react';
import { transferOwnership } from '../../../api/teamApi';
import { fetchUsers } from '../../../api/userApi';
import { Card, Button,  Select } from '@shopify/polaris';
import './TeamTransferOwnership.css';

interface TransferProps {
  teamId: string | number;
}

const TeamTransferOwnership: React.FC<TransferProps> = ({ teamId }) => {
  const [newOwnerId, setNewOwnerId] = useState('');
  const [users, setUsers] = useState<any[]>([]);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [loading, setLoading] = useState(false);
  const [confirm, setConfirm] = useState(false);
  const [ownerTouched, setOwnerTouched] = useState(false);
  const successTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    fetchUsers()
      .then(setUsers)
      .catch(() => setError('Failed to load users'));
  }, []);

  const ownerError = ownerTouched && !newOwnerId ? 'Please select a new owner.' : '';

  const handleTransfer = async () => {
    setOwnerTouched(true);
    setError('');
    setSuccess('');
    if (!newOwnerId) return;
    setLoading(true);
    try {
      await transferOwnership(teamId, newOwnerId);
      setSuccess('Ownership transferred!');
      setNewOwnerId('');
      setConfirm(false);
      setOwnerTouched(false);
    } catch (e: any) {
      if (e?.response?.data?.detail) {
        setError(e.response.data.detail);
      } else if (e?.message) {
        setError(e.message);
      } else if (typeof e === 'string') {
        setError(e);
      } else {
        setError('Failed to transfer ownership');
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

  const isDisabled = !!ownerError || !newOwnerId || !users.length || loading;

  return (
    <Card>
      <div className="team-transfer-content">
        <h2 className="team-transfer-title">Transfer Team Ownership</h2>
        <div className="team-transfer-fields">
          <Select
            label="New Owner"
            options={users.length ? users.map(u => ({ label: u.email || u.name || u.id, value: String(u.id) })) : [{ label: 'No users available', value: '' }]}
            value={newOwnerId}
            onChange={v => { setNewOwnerId(v); setOwnerTouched(true); }}
            error={ownerError}
            onBlur={() => setOwnerTouched(true)}
            disabled={!users.length || loading}
            requiredIndicator
            aria-label="New Owner Selection"
            aria-invalid={!!ownerError}
          />
        </div>
        {error && <div className="team-transfer-error" aria-live="assertive">{error}</div>}
        {success && <div className="team-transfer-success" role="status" aria-live="polite">{success}</div>}
        {confirm ? (
          <div className="team-transfer-confirm">
            <p className="team-transfer-confirm-text">Are you sure you want to transfer ownership? This action cannot be undone.</p>
            <Button onClick={handleTransfer} loading={loading} tone="critical" accessibilityLabel="Confirm transfer ownership" disabled={loading}>
              Confirm Transfer
            </Button>
            <Button onClick={() => setConfirm(false)} disabled={loading}>
              Cancel
            </Button>
          </div>
        ) : (
          <Button
            onClick={() => setConfirm(true)}
            tone="critical"
            accessibilityLabel="Transfer team ownership"
            disabled={isDisabled}
          >
            Transfer Ownership
          </Button>
        )}
      </div>
    </Card>
  );
};

export default TeamTransferOwnership;
