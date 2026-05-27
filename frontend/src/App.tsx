import { useState } from 'react';
import { Layout, Menu, Typography, Space, Badge } from 'antd';
import {
  DashboardOutlined,
  WalletOutlined,
  SwapOutlined,
  BellOutlined,
  LineChartOutlined,
  FileTextOutlined,
} from '@ant-design/icons';

import Dashboard from './pages/Dashboard';
import WalletManagement from './pages/WalletManagement';
import TransactionMonitor from './pages/TransactionMonitor';
import AlertManagement from './pages/AlertManagement';
import WhaleMonitor from './pages/WhaleMonitor';
import ContractMonitor from './pages/ContractMonitor';

const { Header, Content } = Layout;
const { Title } = Typography;

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

  const PageComponent = pageComponents[activePage];

  return (
    <Layout style={{ minHeight: '100vh' }}>
      {/* 顶部导航栏 */}
      <Header
        style={{
          position: 'sticky',
          top: 0,
          zIndex: 100,
          padding: 0,
          background: '#fff',
          boxShadow: '0 2px 8px rgba(0,0,0,0.06)',
          height: 'auto',
          lineHeight: 'normal',
        }}
      >
        {/* 标题区域 */}
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            padding: '12px 24px',
            borderBottom: '1px solid #f0f0f0',
          }}
        >
          <Space align="center">
            <div
              style={{
                width: 36,
                height: 36,
                borderRadius: 10,
                background: 'linear-gradient(135deg, #1677ff 0%, #0958d9 100%)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                color: '#fff',
                fontSize: 18,
                fontWeight: 'bold',
              }}
            >
              W
            </div>
            <Title level={4} style={{ margin: 0, color: '#1f1f1f' }}>
              钱包监控
            </Title>
          </Space>
          <Space>
            <span style={{ color: '#8c8c8c', fontSize: 13 }}>
              多链区块链监控系统
            </span>
          </Space>
        </div>

        {/* 导航菜单 */}
        <Menu
          mode="horizontal"
          selectedKeys={[activePage]}
          style={{
            borderBottom: 'none',
            justifyContent: 'center',
            background: '#fafafa',
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
      </Header>

      {/* 内容区域 */}
      <Content style={{ padding: 24, background: '#f5f5f5' }}>
        <PageComponent />
      </Content>
    </Layout>
  );
}
