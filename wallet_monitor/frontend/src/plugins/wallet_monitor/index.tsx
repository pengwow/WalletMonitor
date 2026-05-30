import React from 'react';
import WhaleWatcher from './components/WhaleWatcher';

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
      '1.1.0',
      '区块链钱包监控插件 + 巨鲸监控',
      'WalletMonitor Team'
    );
  }

  public register(): void {
    super.register();
    
    this.addMenu({
      group: '区块链监控',
      items: [
        {
          path: '/plugins/wallet-monitor/watcher',
          name: '🐋 HypeWatcher'
        }
      ]
    });
    
    this.addRoute({
      path: '/plugins/wallet-monitor/watcher',
      element: <WhaleWatcher />
    });
  }
}

export function registerPlugin(): WalletMonitorPlugin {
  return new WalletMonitorPlugin();
}
