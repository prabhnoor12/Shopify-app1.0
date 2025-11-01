

import React, { useState } from 'react';
import { Card, FormLayout, TextField, Button, Banner } from '@shopify/polaris';
import './TeamCreate.css';

interface TeamCreateProps {
	onTeamCreated?: (team: { name: string }) => void;
}

const TeamCreate: React.FC<TeamCreateProps> = ({ onTeamCreated }) => {
	const [teamName, setTeamName] = useState('');
	const [owner, setOwner] = useState('');
	const [tags, setTags] = useState('');
	const [roles, setRoles] = useState<{ name: string; permissions: string[] }[]>([
		{ name: '', permissions: [] }
	]);
	const [newPermissions, setNewPermissions] = useState<string[]>(['']);
	const [loading, setLoading] = useState(false);
	const [error, setError] = useState('');
	const [success, setSuccess] = useState('');

	const handleRoleNameChange = (idx: number, value: string) => {
		setRoles(prev => prev.map((r, i) => i === idx ? { ...r, name: value } : r));
	};

	const handleAddPermission = (idx: number, permission: string) => {
		if (!permission.trim()) return;
		setRoles(prev => prev.map((r, i) => i === idx ? {
			...r,
			permissions: r.permissions.includes(permission) ? r.permissions : [...r.permissions, permission]
		} : r));
		setNewPermissions(prev => prev.map((p, i) => i === idx ? '' : p));
	};

	// Removed handleRemovePermission logic

	const addRole = () => {
		setRoles(prev => [...prev, { name: '', permissions: [] }]);
		setNewPermissions(prev => [...prev, '']);
	};

	const handleNewPermissionChange = (idx: number, value: string) => {
		setNewPermissions(prev => prev.map((p, i) => i === idx ? value : p));
	};

	const handleSubmit = async () => {
		setError('');
		setSuccess('');
		if (!teamName.trim()) {
			setError('Please enter a team name');
			return;
		}
		if (!owner.trim()) {
			setError('Please enter an owner name');
			return;
		}
		if (!Array.isArray(roles) || roles.length === 0 || roles.some(r => !r.name.trim())) {
			setError('Please add at least one role and provide names for all roles.');
			return;
		}
		setLoading(true);
		try {

			// Real API call to backend
			const response = await fetch('/api/teams', {
				method: 'POST',
				headers: {
					'Content-Type': 'application/json',
				},
				body: JSON.stringify({
					name: teamName,
					owner,
					tags: tags.split(',').map(t => t.trim()).filter(Boolean),
					roles,
				}),
			});
			if (!response.ok) {
				throw new Error('API error');
			}
			const data = await response.json();
			setSuccess(`Team "${data.name || teamName}" created successfully!`);
			if (onTeamCreated) onTeamCreated({ name: data.name || teamName });
			setTeamName('');
			setOwner('');
			setTags('');
			setRoles([{ name: '', permissions: [] }]);
		} catch (e) {
			setError('Failed to create team. Please try again.');
		} finally {
			setLoading(false);
		}
	};

	const isInvalid = loading || !teamName.trim() || !owner.trim() || !roles.length || roles.some(r => !r.name.trim());

	return (
		<div className="team-create-container team-create-wide">
			<Card>
				<FormLayout>
					{error && <Banner tone="critical" aria-live="assertive">{error}</Banner>}
					{success && <Banner tone="success" aria-live="polite">{success}</Banner>}
					<TextField
						label="Team Name"
						value={teamName}
						onChange={setTeamName}
						autoComplete="off"
						placeholder="Enter team name"
						aria-label="Team Name"
					/>
					<TextField
						label="Owner"
						value={owner}
						onChange={setOwner}
						autoComplete="off"
						placeholder="Enter owner name"
						aria-label="Owner Name"
					/>
					<TextField
						label="Tags (comma separated)"
						value={tags}
						onChange={setTags}
						autoComplete="off"
						placeholder="e.g. marketing, sales, dev"
						aria-label="Team Tags"
					/>
					<div className="team-create-roles">
						<h3 className="team-create-roles-title">Roles & Permissions</h3>
									{Array.isArray(roles) && roles.map((role, idx) => (
										<div key={idx} className="team-create-role-block">
											<TextField
												label={`Role Name`}
												value={role.name}
												onChange={val => handleRoleNameChange(idx, val)}
												autoComplete="off"
												placeholder="e.g. Admin, Editor"
												aria-label={`Role Name ${idx + 1}`}
											/>
											<div className="team-create-role-perms">
												<span className="team-create-role-perms-label">Permissions:</span>
												<div className="team-create-role-perms-list">
													{Array.isArray(role.permissions) && role.permissions.map((perm) => (
														<span key={perm} className="team-create-role-perms-item">
															{perm}
														</span>
													))}
												</div>
												<div className="team-create-role-add-perm">
													<TextField
														label="Add Permission"
														value={newPermissions[idx] || ''}
														onChange={val => handleNewPermissionChange(idx, val)}
														autoComplete="off"
														placeholder="Enter permission"
														aria-label="Add Permission"
													/>
													<Button size="micro" onClick={() => handleAddPermission(idx, newPermissions[idx] || '')}>
														Add
													</Button>
												</div>
											</div>
										</div>
									))}
						<Button onClick={addRole}>
							Add Role
						</Button>
					</div>
					<Button
						variant="primary"
						onClick={handleSubmit}
						loading={loading}
						fullWidth
						disabled={isInvalid}
						aria-label="Create Team"
					>
						Create Team
					</Button>
				</FormLayout>
			</Card>
		</div>
	);
};

export default TeamCreate;

