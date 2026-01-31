import React from 'react';
import WalletManagement from './components/WalletManagement';
import TransactionMonitor from './components/TransactionMonitor';
import AlertManagement from './components/AlertManagement';
import Dashboard from './components/Dashboard';

// 假设的插件基类
class PluginBase {
  constructor(
    private name: string,
    private version: string,
    private description?: string,
    private author?: string
  ) {}

  public register(): void {
    console.log(`${this.name} plugin registered`);
  }

  public start(): void {
    console.log(`${this.name} plugin started`);
  }

  public stop(): void {
    console.log(`${this.name} plugin stopped`);
  }

  public addMenu(menuGroup: any): void {
    console.log('Menu added:', menuGroup);
  }

  public addRoute(route: any): void {
    console.log('Route added:', route);
  }
}

export class WalletMonitorPlugin extends PluginBase {
  constructor() {
    super(
      'wallet-monitor',
      '1.0.0',
      '区块链钱包监控插件',
      'Blockchain Monitor Team'
    );
  }

  public register(): void {
    super.register();
    
    // 添加菜单
    this.addMenu({
      group: '区块链监控',
      items: [
        {
          path: '/plugins/wallet-monitor/dashboard',
          name: 'Dashboard'
        },
        {
          path: '/plugins/wallet-monitor/wallets',
          name: '钱包管理'
        },
        {
          path: '/plugins/wallet-monitor/transactions',
          name: '交易监控'
        },
        {
          path: '/plugins/wallet-monitor/alerts',
          name: '告警管理'
        }
      ]
    });
    
    // 添加路由
    this.addRoute({
      path: '/plugins/wallet-monitor/dashboard',
      element: <Dashboard />
    });
    
    this.addRoute({
      path: '/plugins/wallet-monitor/wallets',
      element: <WalletManagement />
    });
    
    this.addRoute({
      path: '/plugins/wallet-monitor/transactions',
      element: <TransactionMonitor />
    });
    
    this.addRoute({
      path: '/plugins/wallet-monitor/alerts',
      element: <AlertManagement />
    });
  }
}

export function registerPlugin(): WalletMonitorPlugin {
  return new WalletMonitorPlugin();
}
