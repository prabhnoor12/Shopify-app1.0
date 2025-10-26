import {  Tabs } from '@shopify/polaris';
import { useState, useCallback, useEffect, useRef } from 'react';
import { useNavigate, useLocation, useParams, Navigate } from 'react-router-dom';
import { useAuth } from '../../../authContext';
import ABTestingDashboard from '../components/ABTestingDashboard';
import ABTestCreationWizard from '../components/ABTestCreationWizard';
import ABTestResults from '../components/ABTestResults';
import AIRecommendations from '../components/AIRecommendations';
import ExperimentManagement from '../components/ExperimentManagement';
import './ABTestingPage.css';


interface ABTestingPageProps {
  initialTab?: number;
}


const tabRoutes = [
  'dashboard',
  'create',
  'results',
  'ai-recommendations',
  'experiment-management',
];

const ABTestingPage: React.FC<ABTestingPageProps> = ({ initialTab = 0 }) => {
  const navigate = useNavigate();
  const location = useLocation();
  const params = useParams();
  const { isAuthenticated, loading } = useAuth();
  const [selectedTab, setSelectedTab] = useState(initialTab);
  const [selectedTestId, setSelectedTestId] = useState<number | null>(null);
  const [forceStopLoading, setForceStopLoading] = useState(false);
  const timeoutRef = useRef<number | null>(null);

  if (!loading && !isAuthenticated) {
    return <Navigate to="/connect" replace />;
  }
  // Force stop loading after 4 seconds
  useEffect(() => {
    setForceStopLoading(false);
    if (timeoutRef.current) clearTimeout(timeoutRef.current);
    timeoutRef.current = setTimeout(() => {
      setForceStopLoading(true);
    }, 4000);
    return () => {
      if (timeoutRef.current) clearTimeout(timeoutRef.current);
    };
  }, [selectedTab]);

  // Sync tab with URL
  useEffect(() => {
    const path = location.pathname.split('/').filter(Boolean);
    const abIndex = path.indexOf('ab-testing');
    let tabIdx = 0;
    if (abIndex !== -1 && path.length > abIndex + 1) {
      const sub = path[abIndex + 1];
      const idx = tabRoutes.indexOf(sub);
      if (idx !== -1) tabIdx = idx;
    }
    setSelectedTab(tabIdx);
    // If results tab, set testId from params
    if (tabIdx === 2 && params.testId) {
      setSelectedTestId(Number(params.testId));
    } else {
      setSelectedTestId(null);
    }
  }, [location.pathname, params.testId]);


  const handleTabChange = useCallback(
    (selectedTabIndex: number) => {
      if (selectedTabIndex === 2) {
        if (selectedTestId) {
          navigate(`/ab-testing/results/${selectedTestId}`);
        } else {
          // Show a message or prevent navigation
          alert('Select a test from the dashboard to view results.');
          return;
        }
      } else {
        navigate(`/ab-testing/${tabRoutes[selectedTabIndex]}`);
      }
    },
    [navigate, selectedTestId],
  );


  const handleTestSelect = (testId: number) => {
    setSelectedTestId(testId);
    navigate(`/ab-testing/results/${testId}`);
  };


  const handleNewTest = () => {
    navigate('/ab-testing/create');
  };


  const handleBackToDashboard = () => {
    navigate('/ab-testing');
    setSelectedTestId(null);
  };

  const tabs = [
    {
      id: 'dashboard',
      content: 'Dashboard',
      panelID: 'dashboard-panel',
    },
    {
      id: 'create-test',
      content: 'Create Test',
      panelID: 'create-test-panel',
    },
    {
      id: 'results',
      content: 'Results',
      panelID: 'results-panel',
      disabled: !selectedTestId,
    },
    {
      id: 'ai-recommendations',
      content: 'AI Recommendations',
      panelID: 'ai-recommendations-panel',
    },
    {
      id: 'experiment-management',
      content: 'Experiment Management',
      panelID: 'experiment-management-panel',
    },
  ];

  const renderTabContent = () => {
    // Pass forceStopLoading to children as prop if needed
    switch (selectedTab) {
      case 0:
        return (
          <ABTestingDashboard
            onTestSelect={handleTestSelect}
            onNewTest={handleNewTest}
            forceStopLoading={forceStopLoading}
          />
        );
      case 1:
        return <ABTestCreationWizard forceStopLoading={forceStopLoading} />;
      case 2:
        return (
          <ABTestResults
            testId={selectedTestId}
            onBack={handleBackToDashboard}
            forceStopLoading={forceStopLoading}
          />
        );
      case 3:
        return <AIRecommendations forceStopLoading={forceStopLoading} />;
      case 4:
        return <ExperimentManagement forceStopLoading={forceStopLoading} />;
      default:
        return null;
    }
  };

  return (
    <div className="abtesting-page">
      <h1>A/B Testing</h1>
      <div className="abtesting-widgets">
        <div className="abtesting-widget">
          <Tabs tabs={tabs} selected={selectedTab} onSelect={handleTabChange} />
        </div>
        <div className="abtesting-widget">
          {renderTabContent()}
        </div>
      </div>
    </div>
  );
};

export default ABTestingPage;
