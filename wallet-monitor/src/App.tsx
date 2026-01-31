import React from 'react';
import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';
import { Layout, Menu } from 'antd';
import WalletManagement from './components/WalletManagement';
import TransactionMonitor from './components/TransactionMonitor';
import AlertManagement from './components/AlertManagement';
import Dashboard from './components/Dashboard';

const { Content } = Layout;

// 独立应用模式的App组件
function App() {
  return (
    <Router>
      <Layout style={{ minHeight: '100vh' }}>
        {/* 页面内容 */}
        <Layout style={{ padding: '24px' }}>
          <Content style={{ background: '#fff', padding: 24, margin: 0, minHeight: 280 }}>
            {/* 顶部菜单（放在main内部） */}
            <div style={{ marginBottom: '24px' }}>
              <Menu
                mode="horizontal"
                style={{ lineHeight: '48px' }}
                selectedKeys={[window.location.pathname]}
              >
                <Menu.Item key="/">
                  <Link to="/">仪表板</Link>
                </Menu.Item>
                <Menu.Item key="/wallets">
                  <Link to="/wallets">钱包管理</Link>
                </Menu.Item>
                <Menu.Item key="/transactions">
                  <Link to="/transactions">交易监控</Link>
                </Menu.Item>
                <Menu.Item key="/alerts">
                  <Link to="/alerts">告警管理</Link>
                </Menu.Item>
              </Menu>
            </div>
            
            {/* 路由内容 */}
            <Routes>
              <Route path="/" element={<Dashboard />} />
              <Route path="/wallets" element={<WalletManagement />} />
              <Route path="/transactions" element={<TransactionMonitor />} />
              <Route path="/alerts" element={<AlertManagement />} />
            </Routes>
          </Content>
        </Layout>
      </Layout>
    </Router>
  );
}

// 导出独立应用模式的App组件
export default App;

// 导出插件模式的组件，供插件系统使用
export { WalletManagement, TransactionMonitor, AlertManagement, Dashboard };

