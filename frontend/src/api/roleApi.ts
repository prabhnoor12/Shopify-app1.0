import axios from 'axios';

const BASE_URL = '/api/teams';

export interface Role {
  id: string | number;
  name: string;
  description?: string;
}

export const getTeamRoles = async (teamId: string | number): Promise<Role[]> => {
  const res = await axios.get<Role[]>(`${BASE_URL}/${teamId}/roles`);
  return res.data;
};
