import axios from 'axios';

const BASE_URL = '/api/teams';

export interface Team {
    id: string;
    name: string;
    owner_id: string;
    members: TeamMember[];
    created_at: string;
    updated_at: string;
    // add other fields as needed
}

export interface TeamMember {
    id: string;
    name: string;
    email: string;
    role_id: string;
    // add other fields as needed
}

export interface CreateTeamRequest {
  name: string;
  description?: string;
  // add other fields as needed
}

export interface Invitation {
    email: string;
    role_id: string;
    // add other fields as needed
}

export const createTeam = async (data: CreateTeamRequest): Promise<Team> => {
    const res = await axios.post<Team>(`${BASE_URL}/`, data);
    return res.data;
};

export const getMyTeams = async (): Promise<Team[]> => {
  const res = await axios.get<Team[]>(`${BASE_URL}/me`);
  return res.data;
};

export const getTeamById = async (teamId: string | number): Promise<Team> => {
  const res = await axios.get<Team>(`${BASE_URL}/${teamId}`);
  return res.data;
};

export const updateTeam = async (teamId: string | number, data: Partial<CreateTeamRequest>): Promise<Team> => {
  const res = await axios.put<Team>(`${BASE_URL}/${teamId}`, data);
  return res.data;
};

export const deleteTeam = async (teamId: string | number): Promise<void> => {
  await axios.delete(`${BASE_URL}/${teamId}`);
};

export const inviteTeamMember = async (teamId: string | number, invitation: Invitation): Promise<void> => {
  await axios.post(`${BASE_URL}/${teamId}/invitations`, invitation);
};

export const acceptInvitation = async (token: string): Promise<void> => {
  await axios.post(`${BASE_URL}/invitations/accept`, null, { params: { token } });
};

export const updateTeamMemberRole = async (
  teamId: string | number,
  userId: string | number,
  roleId: string | number
): Promise<void> => {
  await axios.put(`${BASE_URL}/${teamId}/members/${userId}/role`, { role_id: roleId });
};

export const removeTeamMember = async (teamId: string | number, userId: string | number): Promise<void> => {
  await axios.delete(`${BASE_URL}/${teamId}/members/${userId}`);
};

export const transferOwnership = async (teamId: string | number, newOwnerId: string | number): Promise<void> => {
  await axios.post(`${BASE_URL}/${teamId}/transfer-ownership`, { new_owner_id: newOwnerId });
};
