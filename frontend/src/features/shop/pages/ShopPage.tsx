import { Page, Layout, Tabs } from '@shopify/polaris';
import { useState, useCallback, useEffect, useRef } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../../../authContext';
import { Navigate } from 'react-router-dom';
import AIContentGeneration from '../components/AIContentGeneration';
import BrandVoiceConfiguration from '../components/BrandVoiceConfiguration';
import BulkFindReplace from '../components/BulkFindReplace';
import UserAccountStatus from '../components/UserAccountStatus';
import BulkOperations from '../components/BulkOperations';
import GenerationResult from '../components/GenerationResult';


interface ShopPageProps {
  initialTab?: number;
}

const tabRoutes = [
  'ai-content-generation',
  'brand-voice',
  'bulk-find-replace',
  'bulk-operations',
  'generation-result',
];

export const ShopPage: React.FC<ShopPageProps> = ({ initialTab = 0 }) => {

  const navigate = useNavigate();
  const location = useLocation();
  const { isAuthenticated, loading } = useAuth();
  const [selectedTab, setSelectedTab] = useState(initialTab);
  const [forceStopLoading, setForceStopLoading] = useState(false);
  const timeoutRef = useRef<number | null>(null);
  // Shared state for generation result and selected product
  const [generationResult, setGenerationResult] = useState<any>(null);
  const [selectedProduct, setSelectedProduct] = useState<string>('');

  if (!loading && !isAuthenticated) {
    return <Navigate to="/connect" replace />;
  }

  // Sync tab with URL
  useEffect(() => {
    const path = location.pathname.split('/').filter(Boolean);
    const shopIndex = path.indexOf('shop');
    let tabIdx = 0;
    if (shopIndex !== -1 && path.length > shopIndex + 1) {
      const sub = path[shopIndex + 1];
      const idx = tabRoutes.indexOf(sub);
      if (idx !== -1) tabIdx = idx;
    }
    setSelectedTab(tabIdx);
  }, [location.pathname]);

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

  const handleTabChange = useCallback(
    (selectedTabIndex: number) => {
      navigate(`/shop/${tabRoutes[selectedTabIndex]}`);
    },
    [navigate],
  );

  const tabs = [
    {
      id: 'ai-content-generation',
      content: 'AI Content Generation',
      panelID: 'ai-content-generation-panel',
    },
    {
      id: 'brand-voice',
      content: 'Brand Voice',
      panelID: 'brand-voice-panel',
    },
    {
      id: 'bulk-find-replace',
      content: 'Bulk Find & Replace',
      panelID: 'bulk-find-replace-panel',
    },
    {
      id: 'bulk-operations',
      content: 'Bulk Operations',
      panelID: 'bulk-operations-panel',
    },
    {
      id: 'generation-result',
      content: 'Generation Result',
      panelID: 'generation-result-panel',
    },
  ];

  const renderTabContent = () => {
    switch (selectedTab) {
      case 0:
        return (
          <AIContentGeneration
            forceStopLoading={forceStopLoading}
            generationResult={generationResult}
            setGenerationResult={setGenerationResult}
            selectedProduct={selectedProduct}
            setSelectedProduct={setSelectedProduct}
          />
        );
      case 1:
        return <BrandVoiceConfiguration forceStopLoading={forceStopLoading} />;
      case 2:
        return <BulkFindReplace forceStopLoading={forceStopLoading} />;
      case 3:
        return (
          <BulkOperations
            setError={() => {}}
          />
        );
      case 4:
        return (
          <GenerationResult
            result={generationResult}
            selectedProduct={selectedProduct}
            setError={() => {}}
          />
        );
      default:
        return null;
    }
  };

  return (
    <Page fullWidth title="Shop Tools">
      <Layout>
        <Layout.Section>
          <UserAccountStatus />
        </Layout.Section>
        <Layout.Section>
          <div className="shoppage-main-content">
            <Tabs tabs={tabs} selected={selectedTab} onSelect={handleTabChange} />
            <div className="shoppage-tab-content">
              {renderTabContent()}
            </div>
          </div>
        </Layout.Section>
      </Layout>
    </Page>
  );

};
export default ShopPage;
import './ShopPage.module.css';
