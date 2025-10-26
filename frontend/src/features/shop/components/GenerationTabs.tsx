// src/features/shop/components/GenerationTabs.tsx
import { Tabs } from '@shopify/polaris';
import './GenerationTabs.css';

export interface GenerationTab {
  id: string;
  content: string;
  accessibilityLabel?: string;
  panelID?: string;
}

interface GenerationTabsProps {
  tabs: GenerationTab[];
  selected: number;
  onSelect: (selectedTabIndex: number) => void;
}

const GenerationTabs = ({ tabs, selected, onSelect }: GenerationTabsProps) => {
  return (
    <Tabs tabs={tabs} selected={selected} onSelect={onSelect} />
  );
};

export default GenerationTabs;
