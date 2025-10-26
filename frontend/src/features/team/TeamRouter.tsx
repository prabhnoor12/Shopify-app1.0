import React, { useState } from 'react';
import TeamList from './components/TeamList';
import TeamCreate from './components/TeamCreate';
import TeamInvite from './components/TeamInvite';
import TeamMemberRole from './components/TeamMemberRole';
import TeamRemoveMember from './components/TeamRemoveMember';
import TeamTransferOwnership from './components/TeamTransferOwnership';
import './TeamRouter.css';

const TABS = [
	{ key: 'list', label: 'Team List' },
	{ key: 'create', label: 'Create Team' },
	{ key: 'invite', label: 'Invite Member' },
	{ key: 'role', label: 'Change Member Role' },
	{ key: 'remove', label: 'Remove Member' },
	{ key: 'transfer', label: 'Transfer Ownership' },
];

const TeamRouter: React.FC = () => {
	const [activeTab, setActiveTab] = useState('list');
	// For TeamInvite, you may want to pass a teamId. For demo, use '1'.
	const teamId = '1';

	return (
		<div>
			<div className="team-router-tabs">
				{TABS.map(tab => (
					<button
						key={tab.key}
						className={`team-router-tab-btn${activeTab === tab.key ? ' active' : ''}`}
						onClick={() => setActiveTab(tab.key)}
					>
						{tab.label}
					</button>
				))}
			</div>
			<div className="team-router-tab-content">
				{activeTab === 'list' && <TeamList />}
				{activeTab === 'create' && <TeamCreate />}
				{activeTab === 'invite' && <TeamInvite teamId={teamId} />}
				{activeTab === 'role' && <TeamMemberRole userId="1" />}
				{activeTab === 'remove' && <TeamRemoveMember />}
				{activeTab === 'transfer' && <TeamTransferOwnership teamId={teamId} />}
			</div>
		</div>
	);
};

export default TeamRouter;
