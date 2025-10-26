import React, { useEffect, useState } from 'react';
import './AnalyticsPage.css';
import RevenueAttribution from '../components/RevenueAttribution';
import type { RevenueAttributionData } from '../components/RevenueAttribution';
import DescriptionPerformance from '../components/DescriptionPerformance';
import type { VariantPerformance } from '../components/DescriptionPerformance';
import SEOAnalysis from '../components/SEOAnalysis';
import type { SEOAnalysisData } from '../components/SEOAnalysis';
import ProductTimelinePerformance from '../components/ProductTimelinePerformance';
import type { TimelinePerformanceData } from '../components/ProductTimelinePerformance';
import TeamPerformance from '../components/TeamPerformance';
import type { TeamMemberPerformance } from '../components/TeamPerformance';
import CategoryPerformance from '../components/CategoryPerformance';
import type { CategoryPerformanceData } from '../components/CategoryPerformance';
import ActionableAlerts from '../components/ActionableAlerts';
import type { ActionableAlert } from '../components/ActionableAlerts';






const AnalyticsPage: React.FC = () => {
  const [revenueData, setRevenueData] = useState<RevenueAttributionData | null>(null);
  const [variantData, setVariantData] = useState<VariantPerformance[] | null>(null);
  const [seoData, setSeoData] = useState<SEOAnalysisData | null>(null);
  const [timelineData, setTimelineData] = useState<TimelinePerformanceData[] | null>(null);
  const [teamData, setTeamData] = useState<TeamMemberPerformance[] | null>(null);
  const [categoryData, setCategoryData] = useState<CategoryPerformanceData[] | null>(null);
  const [alerts, setAlerts] = useState<ActionableAlert[] | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setLoading(true);
    setError(null);
    Promise.all([
      fetch('/api/analytics/revenue').then(res => res.json()),
      fetch('/api/analytics/variants').then(res => res.json()),
      fetch('/api/analytics/seo').then(res => res.json()),
      fetch('/api/analytics/timeline').then(res => res.json()),
      fetch('/api/analytics/team').then(res => res.json()),
      fetch('/api/analytics/category').then(res => res.json()),
      fetch('/api/analytics/alerts').then(res => res.json()),
    ])
      .then(([revenue, variants, seo, timeline, team, category, alerts]) => {
        setRevenueData(revenue);
        setVariantData(variants);
        setSeoData(seo);
        setTimelineData(timeline);
        setTeamData(team);
        setCategoryData(category);
        setAlerts(alerts);
        setLoading(false);
      })
      .catch(() => {
        setError('Failed to load analytics data.');
        setLoading(false);
      });
  }, []);

  return (
    <div className="analytics-page">
      <h1>Analytics Dashboard</h1>
      <div className="analytics-dashboard-vertical">
        <RevenueAttribution data={revenueData} loading={loading} error={error} />
        <DescriptionPerformance variants={variantData || []} loading={loading} error={error} />
        <SEOAnalysis data={seoData} loading={loading} error={error} />
        <ProductTimelinePerformance timeline={timelineData || []} loading={loading} error={error} />
        <TeamPerformance members={teamData || []} loading={loading} error={error} />
        <CategoryPerformance categories={categoryData || []} loading={loading} error={error} />
        <ActionableAlerts alerts={alerts || []} loading={loading} error={error} />
      </div>
    </div>
  );
};

export default AnalyticsPage;
