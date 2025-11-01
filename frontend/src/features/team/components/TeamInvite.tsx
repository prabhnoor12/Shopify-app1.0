import React, { useState, useEffect, useRef } from 'react';
import { inviteTeamMember } from '../../../api/teamApi';
import { getTeamRoles } from '../../../api/roleApi';
import type { Role } from '../../../api/roleApi';
import { Card, TextField, Button,  Select } from '@shopify/polaris';
import './TeamInvite.css';

interface InviteProps {
  teamId: string | number;
}

const validateEmail = (email: string) => {
  // RFC 5322 Official Standard regex (simplified)
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
};

const TeamInvite: React.FC<InviteProps> = ({ teamId }) => {
  const [email, setEmail] = useState('');
  const [roleId, setRoleId] = useState('');
  const [roles, setRoles] = useState<Role[]>([]);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [loading, setLoading] = useState(false);
  const [emailTouched, setEmailTouched] = useState(false);
  const [roleTouched, setRoleTouched] = useState(false);
  const [showDisabledTooltip, setShowDisabledTooltip] = useState(false);
  const successTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    getTeamRoles(teamId)
      .then(setRoles)
      .catch(() => setError('Failed to load roles'));
  }, [teamId]);

  useEffect(() => {
    if (success) {
      successTimeoutRef.current = setTimeout(() => setSuccess(''), 4000);
    }
    return () => {
      if (successTimeoutRef.current) clearTimeout(successTimeoutRef.current);
    };
  }, [success]);

  const emailError = emailTouched && !validateEmail(email) ? 'Please enter a valid email address.' : '';
  const roleError = roleTouched && !roleId ? 'Please select a role.' : '';

  const handleInvite = async () => {
    setEmailTouched(true);
    setRoleTouched(true);
    setError('');
    setSuccess('');
    if (!validateEmail(email) || !roleId) return;
    setLoading(true);
    try {
      await inviteTeamMember(teamId, { email, role_id: roleId });
      setSuccess('Invitation sent!');
      setEmail('');
      setRoleId('');
      setEmailTouched(false);
      setRoleTouched(false);
    } catch (e: any) {
      if (e?.response?.data?.detail) {
        setError(e.response.data.detail);
      } else if (e?.message) {
        setError(e.message);
      } else if (typeof e === 'string') {
        setError(e);
      } else {
        setError('Failed to send invitation');
      }
    }
    setLoading(false);
  };

  const isDisabled = !!emailError || !!roleError || !email.trim() || !roleId || !Array.isArray(roles) || roles.length === 0 || loading;

  return (
    <Card>
      <div className="team-invite-content">
        <h2 className="team-invite-title">Invite Team Member</h2>
        <div className="team-invite-fields">
          <TextField
            label="Email"
            value={email}
            onChange={v => { setEmail(v); setEmailTouched(true); }}
            autoComplete="off"
            error={emailError}
            onBlur={() => setEmailTouched(true)}
            type="email"
            requiredIndicator
            aria-label="Invitee Email"
            aria-invalid={!!emailError}
            disabled={loading}
          />
          <Select
            label="Role"
            options={Array.isArray(roles) && roles.length ? roles.map(r => ({ label: r.name, value: String(r.id) })) : [{ label: 'No roles available', value: '' }]}
            value={roleId}
            onChange={v => { setRoleId(v); setRoleTouched(true); }}
            error={roleError}
            onBlur={() => setRoleTouched(true)}
            disabled={!Array.isArray(roles) || roles.length === 0 || loading}
            requiredIndicator
            aria-label="Role Selection"
            aria-invalid={!!roleError}
          />
        </div>
        {error && <div className="team-invite-error" aria-live="assertive">{error}</div>}
        {success && <div className="team-invite-success" role="status" aria-live="polite">{success}</div>}
        <div
          className="team-invite-btn-wrapper"
          onMouseEnter={() => isDisabled && setShowDisabledTooltip(true)}
          onMouseLeave={() => setShowDisabledTooltip(false)}
        >
          <Button
            onClick={handleInvite}
            loading={loading}
            disabled={isDisabled}
            variant="primary"
            accessibilityLabel="Send team invitation"
            aria-disabled={isDisabled}
          >
            Send Invitation
          </Button>
          {isDisabled && showDisabledTooltip && (
            <div className="team-invite-tooltip" role="tooltip">
              {loading ? 'Sending invitation...' :
                !roles.length ? 'No roles available. Please add roles first.' :
                !!emailError ? emailError :
                !!roleError ? roleError :
                !email.trim() ? 'Email is required.' :
                !roleId ? 'Role is required.' :
                'Cannot send invitation.'}
            </div>
          )}
        </div>
      </div>
    </Card>
  );
};

export default TeamInvite;
