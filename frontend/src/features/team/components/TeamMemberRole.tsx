
import React, { useState, useEffect, useRef } from 'react';
import { updateTeamMemberRole, getMyTeams } from '../../../api/teamApi';
import { getTeamRoles } from '../../../api/roleApi';
import type { Role } from '../../../api/roleApi';
import { Card, Button, Select, TextField } from '@shopify/polaris';
import './TeamMemberRole.css';


interface RoleProps {
  userId: string | number;
  teamId?: string | number;
}

const TeamMemberRole: React.FC<RoleProps> = ({ userId, teamId: propTeamId }) => {
  const [teams, setTeams] = useState<{ id: string | number; name: string }[]>([]);
  const [teamId, setTeamId] = useState(propTeamId ? String(propTeamId) : '');
  const [roles, setRoles] = useState<Role[]>([]);
  const [roleId, setRoleId] = useState('');
  const [permissions, setPermissions] = useState<string[]>([]);
  const [newPermission, setNewPermission] = useState('');
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [loading, setLoading] = useState(false);
  const [roleTouched, setRoleTouched] = useState(false);
  const successTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    getMyTeams()
      .then(teams => setTeams(teams.map(t => ({ id: t.id, name: t.name }))))
      .catch(() => setError('Failed to load teams'));
    if (propTeamId) setTeamId(String(propTeamId));
  }, [propTeamId]);

  useEffect(() => {
    if (teamId) {
      getTeamRoles(teamId)
        .then(setRoles)
        .catch(() => setError('Failed to load roles'));
      setRoleId('');
      setPermissions([]);
    }
  }, [teamId]);

  useEffect(() => {
    if (roleId) {
      const role = roles.find(r => String(r.id) === String(roleId));
      // Store permissions in description as comma-separated string
      setPermissions(role?.description ? role.description.split(',').map(p => p.trim()).filter(Boolean) : []);
    }
  }, [roleId, roles]);

  useEffect(() => {
    if (success) {
      successTimeoutRef.current = setTimeout(() => setSuccess(''), 4000);
    }
    return () => {
      if (successTimeoutRef.current) clearTimeout(successTimeoutRef.current);
    };
  }, [success]);


  const roleError = roleTouched && !roleId ? 'Please select a role.' : '';
  const teamError = !teamId ? 'Please select a team.' : '';


  const handleUpdate = async () => {
    setRoleTouched(true);
    setError('');
    setSuccess('');
    if (!teamId || !roleId) return;
    setLoading(true);
    try {
      await updateTeamMemberRole(teamId, userId, roleId);
      // Optionally, send permissions update via another API if available
      setSuccess('Role updated!');
      setRoleTouched(false);
    } catch (e: any) {
      if (e?.response?.data?.detail) {
        setError(e.response.data.detail);
      } else if (e?.message) {
        setError(e.message);
      } else if (typeof e === 'string') {
        setError(e);
      } else {
        setError('Failed to update role');
      }
    }
    setLoading(false);
  };

  const handleAddPermission = () => {
    if (!newPermission.trim()) return;
    if (permissions.includes(newPermission.trim())) return;
    setPermissions(prev => [...prev, newPermission.trim()]);
    setNewPermission('');
  };

  const handleRemovePermission = (perm: string) => {
    setPermissions(prev => prev.filter(p => p !== perm));
  };


  const isDisabled = !!roleError || !!teamError || !roleId || !roles.length || loading;

  return (
    <Card>
      <div className="team-role-content">
        <h2 className="team-role-title">Update Team Member Role & Permissions</h2>
        <div className="team-role-fields">
          <Select
            label="Team"
            options={Array.isArray(teams) && teams.length ? teams.map(t => ({ label: t.name, value: String(t.id) })) : [{ label: 'No teams available', value: '' }]}
            value={teamId}
            onChange={v => { setTeamId(v); setRoleTouched(false); setRoleId(''); setPermissions([]); }}
            error={teamError}
            disabled={!Array.isArray(teams) || teams.length === 0 || loading}
            requiredIndicator
            aria-label="Team Selection"
            aria-invalid={!!teamError}
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
          <div className="team-role-permissions">
            <label>Permissions</label>
            <div className="team-role-perms-list">
              {Array.isArray(permissions) && permissions.map(perm => (
                <span key={perm} className="team-role-perms-item">
                  {perm}
                  <Button size="micro" tone="critical" onClick={() => handleRemovePermission(perm)}>
                    Remove
                  </Button>
                </span>
              ))}
            </div>
            <div className="team-role-add-perm">
              <TextField
                label="Add Permission"
                value={newPermission}
                onChange={setNewPermission}
                autoComplete="off"
                placeholder="Enter permission"
                aria-label="Add Permission"
              />
              <Button size="micro" onClick={handleAddPermission}>
                Add
              </Button>
            </div>
          </div>
        </div>
        {error && <div className="team-role-error" aria-live="assertive">{error}</div>}
        {success && <div className="team-role-success" role="status" aria-live="polite">{success}</div>}
        <Button
          onClick={handleUpdate}
          loading={loading}
          disabled={isDisabled}
          variant="primary"
          accessibilityLabel="Update team member role and permissions"
          aria-disabled={isDisabled}
        >
          Update Role & Permissions
        </Button>
      </div>
    </Card>
  );
};

export default TeamMemberRole;
