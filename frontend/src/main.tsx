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
    pluginName: 'wallet_monitor',
  },
];

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
