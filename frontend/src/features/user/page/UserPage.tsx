import React from 'react';
import { Page, Layout } from '@shopify/polaris';
import UserList from '../components/UserList';

const UserPage: React.FC = () => (
  <Page title="Shopify Merchants">
    <Layout>
      <Layout.Section>
        <UserList />
      </Layout.Section>
    </Layout>
  </Page>
);

export default UserPage;