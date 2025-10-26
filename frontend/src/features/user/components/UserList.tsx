import React, { useEffect, useState } from 'react';
import {
  Page,
  Card,



  Badge,

  Text,
  Banner,
  Layout,

} from '@shopify/polaris';
import { fetchCurrentUser } from '../../../api/userApi';
import './UserList.css';

interface User {
  id: string;
  email: string;
  shop_domain: string;
  is_active: boolean;
}


const UserList: React.FC = () => {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    const loadUser = async () => {
      setLoading(true);
      try {
        const data = await fetchCurrentUser();
        setUser(data);
        setError('');
      } catch (e) {
        setError('Failed to load user details. Please try again.');
      } finally {
        setLoading(false);
      }
    };
    loadUser();
  }, []);

  return (
    <Page title="My Account">
      <Layout>
        <Layout.Section>
          {error && (
            <Banner title="Error" tone="critical" onDismiss={() => setError('')}>
              <p>{error}</p>
            </Banner>
          )}
        </Layout.Section>
        <Layout.Section>
          <Card>
            {loading ? (
              <Text as="span">Loading...</Text>
            ) : user ? (
              <div className="merchant-user-details">
                <Text variant="bodyMd" fontWeight="bold" as="h2">Merchant Details</Text>
                <div className="merchant-user-row"><strong>ID:</strong> {user.id}</div>
                <div className="merchant-user-row"><strong>Email:</strong> {user.email}</div>
                <div className="merchant-user-row"><strong>Shop Domain:</strong> {user.shop_domain}</div>
                <div className="merchant-user-row"><strong>Status:</strong> <Badge tone={user.is_active ? 'success' : 'critical'}>{user.is_active ? 'Active' : 'Inactive'}</Badge></div>
              </div>
            ) : (
              <Text as="span">No user details found.</Text>
            )}
          </Card>
        </Layout.Section>
      </Layout>
    </Page>
  );
};

export default UserList;
