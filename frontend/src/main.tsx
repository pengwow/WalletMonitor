import React from 'react';
import ReactDOM from 'react-dom/client';
import { WalletOutlined } from '@ant-design/icons';
import App from './App';

const routes = [
  {
    path: '/plugins/wallet-monitor',
    element: React.createElement(App),
    pluginName: 'wallet_monitor',
  },
];

const menuItems = [
  {
    key: '/plugins/wallet-monitor',
    label: '钱包监控',
    icon: React.createElement(WalletOutlined),
    pluginName: 'wallet_monitor',
  },
];

// 插件模式导出
export function registerPlugin() {
  return {
    register(context: any) {
      for (const route of routes) {
        context.addRoute(route);
      }
      for (const menu of menuItems) {
        context.addMenu(menu);
      }
    },
    getRoutes: () => routes,
    getMenuItems: () => menuItems,
  };
}

// 独立运行模式
const rootEl = document.getElementById('root');
if (rootEl && !rootEl.getAttribute('data-plugin-mode')) {
  const root = ReactDOM.createRoot(rootEl);
  root.render(
    <React.StrictMode>
      <App />
    </React.StrictMode>
  );
}
