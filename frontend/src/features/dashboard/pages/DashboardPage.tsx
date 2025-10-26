import React from 'react';
import UserSummaryWidget from '../components/UserSummaryWidget';
import ActivitySummaryWidget from '../components/ActivitySummaryWidget';
import RecentDescriptionsList from '../components/RecentDescriptionsList';
import TeamActivityWidget from '../components/TeamActivityWidget';
import MonthlyDescriptionChart from '../components/MonthlyDescriptionChart';
import TopProductsWidget from '../components/TopProductsWidget';
import RecentOrdersFeed from '../components/RecentOrdersFeed';
import SalesTrendChart from '../components/SalesTrendChart';
import './DashboardPage.css';

const DashboardPage: React.FC = () => {
  return (
    <main className="dashboard-page" aria-label="Merchant Dashboard">
      <header className="dashboard-header">
        <h1>Merchant Dashboard</h1>
      </header>
      <section className="dashboard-widgets" aria-label="Dashboard Widgets">
        <ActivitySummaryWidget />
        <MonthlyDescriptionChart />
        <RecentDescriptionsList />
        <RecentOrdersFeed />
        <SalesTrendChart />
        <TeamActivityWidget />
        <TopProductsWidget />
        <UserSummaryWidget />
      </section>
    </main>
  );
};

export default DashboardPage;
