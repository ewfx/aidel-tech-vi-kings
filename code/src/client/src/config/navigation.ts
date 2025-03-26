// config/navigation.ts
import { IconHome, IconFileUpload, IconHistory, IconChartBar } from '@tabler/icons-react';

export interface NavbarItem {
  link: string;
  label: string;
  icon: React.FC<{ size: number }>;
}

export const navbarLinks: NavbarItem[] = [
  { link: '/', label: 'Dashboard', icon: IconHome },
  { link: '/submit', label: 'Submit Transaction', icon: IconFileUpload },
  { link: '/history', label: 'Transaction History', icon: IconHistory },
];