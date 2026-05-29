import { useState } from 'react';
import { Layout, Menu, Badge, ConfigProvider, theme as antdTheme } from 'antd';
import {
  DashboardOutlined,
  WalletOutlined,
  SwapOutlined,
  BellOutlined,
  LineChartOutlined,
  FileTextOutlined,
} from '@ant-design/icons';

import { useTheme } from './hooks/useTheme';
import Dashboard from './pages/Dashboard';
import WalletManagement from './pages/WalletManagement';
import TransactionMonitor from './pages/TransactionMonitor';
import AlertManagement from './pages/AlertManagement';
import WhaleMonitor from './pages/WhaleMonitor';
import ContractMonitor from './pages/ContractMonitor';

const { Content } = Layout;

type PageKey = 'dashboard' | 'wallets' | 'transactions' | 'alerts' | 'whales' | 'contracts';

interface MenuItemConfig {
  key: PageKey;
  icon: React.ReactNode;
  label: string;
  badge?: number;
}

const menuItems: MenuItemConfig[] = [
  { key: 'dashboard', icon: <DashboardOutlined />, label: '仪表盘' },
  { key: 'whales', icon: <LineChartOutlined />, label: '巨鲸监控' },
  { key: 'wallets', icon: <WalletOutlined />, label: '钱包管理' },
  { key: 'transactions', icon: <SwapOutlined />, label: '交易监控' },
  { key: 'alerts', icon: <BellOutlined />, label: '告警管理', badge: 3 },
  { key: 'contracts', icon: <FileTextOutlined />, label: '合约监控' },
];

const pageComponents: Record<PageKey, React.FC> = {
  dashboard: Dashboard,
  wallets: WalletManagement,
  transactions: TransactionMonitor,
  alerts: AlertManagement,
  whales: WhaleMonitor,
  contracts: ContractMonitor,
};

export default function App() {
  const [activePage, setActivePage] = useState<PageKey>('dashboard');
  const theme = useTheme();
  const isDark = theme === 'dark';

  const PageComponent = pageComponents[activePage];

  // 根据宿主主题动态调整样式
  const menuBg = isDark ? '#1f1f1f' : '#fff';
  const menuBorderColor = isDark ? '#333' : '#f0f0f0';
  const contentBg = isDark ? '#141414' : '#fff';
  const textColor = isDark ? '#fff' : 'rgba(0, 0, 0, 0.88)';
  const textColorSecondary = isDark ? 'rgba(255, 255, 255, 0.65)' : 'rgba(0, 0, 0, 0.45)';
  const shadowColor = isDark
    ? '0 1px 2px 0 rgba(0, 0, 0, 0.2), 0 1px 6px -1px rgba(0, 0, 0, 0.15), 0 2px 4px 0 rgba(0, 0, 0, 0.15)'
    : '0 1px 2px 0 rgba(0, 0, 0, 0.03), 0 1px 6px -1px rgba(0, 0, 0, 0.02), 0 2px 4px 0 rgba(0, 0, 0, 0.02)';

  return (
    <ConfigProvider
      theme={{
        algorithm: isDark ? antdTheme.darkAlgorithm : antdTheme.defaultAlgorithm,
        token: {
          colorBgBase: contentBg,
          colorTextBase: textColor,
          colorText: textColor,
          colorTextSecondary: textColorSecondary,
        },
      }}
    >
      {/* 全局样式注入 - 确保所有文字颜色跟随主题 */}
      <style>{`
        .wallet-monitor-plugin {
          color: ${textColor};
        }
        .wallet-monitor-plugin .ant-typography {
          color: ${textColor} !important;
        }
        .wallet-monitor-plugin .ant-typography-secondary {
          color: ${textColorSecondary} !important;
        }
        .wallet-monitor-plugin .ant-statistic-title {
          color: ${textColorSecondary} !important;
        }
        .wallet-monitor-plugin .ant-statistic-content {
          color: ${textColor} !important;
        }
        .wallet-monitor-plugin .ant-card-head-title {
          color: ${textColor} !important;
        }
      `}</style>
      <div className="wallet-monitor-plugin">
        <Layout style={{ minHeight: '100%', background: 'transparent' }}>
          {/* 顶部导航菜单 - 跟随宿主主题 */}
          <div
            style={{
              borderBottom: `1px solid ${menuBorderColor}`,
              background: menuBg,
              padding: '8px 16px',
            }}
          >
            <Menu
              mode="horizontal"
              selectedKeys={[activePage]}
              style={{
                borderBottom: 'none',
                justifyContent: 'flex-start',
                background: 'transparent',
                lineHeight: '40px',
              }}
              items={menuItems.map((item) => ({
                key: item.key,
                icon: item.icon,
                label: item.badge ? (
                  <Badge count={item.badge} size="small" offset={[8, -2]}>
                    <span>{item.label}</span>
                  </Badge>
                ) : (
                  item.label
                ),
              }))}
              onClick={({ key }) => setActivePage(key as PageKey)}
            />
          </div>

          {/* 内容区域 - 跟随宿主主题 */}
          <Content
            style={{
              padding: 0,
              background: contentBg,
              boxShadow: shadowColor,
            }}
          >
            <PageComponent />
          </Content>
        </Layout>
      </div>
    </ConfigProvider>
  );
}
