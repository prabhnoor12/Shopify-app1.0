import TeamCreate from '../components/TeamCreate';
import TeamInvite from '../components/TeamInvite';
import TeamMemberRole from '../components/TeamMemberRole';
import TeamRemoveMember from '../components/TeamRemoveMember';
import TeamTransferOwnership from '../components/TeamTransferOwnership';
import TeamList from '../components/TeamList';
import { Page } from '@shopify/polaris';
import './TeamListPage.css';

import React, { useEffect, useState } from 'react';

import type { Team } from '../../../api/teamApi';

const TeamListPage: React.FC = () => {
  const [_, setTeams] = useState<Team[]>([]); // teams state is only used for side effects
  const [selectedTeamId, setSelectedTeamId] = useState<string | number | undefined>(undefined);
  const [selectedUserId, setSelectedUserId] = useState<string | number | undefined>(undefined);

  // Fetch teams for context (could be improved with context/provider in a real app)
  useEffect(() => {
    import('../../../api/teamApi').then(api => {
      api.getMyTeams().then(data => {
        setTeams(data);
        if (data.length > 0) {
          setSelectedTeamId(data[0].id);
          if (data[0].members && data[0].members.length > 0) {
            setSelectedUserId(data[0].members[0].id);
          }
        }
      });
    });
  }, []);

  return (
    <Page title="Teams">
      <div className="teamlistpage-flex">
        <div className="teamlistpage-col">
          <TeamCreate />
        </div>
        <div className="teamlistpage-col">
          {selectedTeamId && <TeamInvite teamId={selectedTeamId} />}
        </div>
        <div className="teamlistpage-col">
          {selectedTeamId && selectedUserId && (
            <TeamMemberRole teamId={selectedTeamId} userId={selectedUserId} />
          )}
        </div>
        <div className="teamlistpage-col">
          {selectedTeamId && selectedUserId && (
            <TeamRemoveMember teamId={selectedTeamId} userId={selectedUserId} />
          )}
        </div>
        <div className="teamlistpage-col">
          {selectedTeamId && <TeamTransferOwnership teamId={selectedTeamId} />}
        </div>
      </div>
      <div className="teamlistpage-list">
        <TeamList />
      </div>
    </Page>
  );
};

export default TeamListPage;
