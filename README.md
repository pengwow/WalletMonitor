# 区块链钱包监控系统插件

## 项目概述

这是一个基于QuantCell插件系统开发的区块链钱包监控系统插件，支持多链钱包监控、实时交易跟踪、智能合约交互监控、异常行为检测与告警等核心功能。

## 核心功能

### 后端插件功能

1. **区块链交互模块**
   - 支持以太坊、BSC等多链
   - 实现了区块监听、交易跟踪
   - 提供了统一的区块链API接口

2. **数据处理模块**
   - 交易数据清洗与标准化
   - 智能合约交互解析
   - SQLite数据存储

3. **告警系统模块**
   - 规则引擎（大额转账、陌生地址、频繁交易）
   - 告警触发与存储
   - 支持多渠道告警

4. **API接口模块**
   - 钱包管理接口（添加、查询、更新）
   - 交易查询接口（按地址、链过滤）
   - 插件信息接口

### 前端插件功能

1. **仪表盘组件**
   - 钱包概览（总钱包数、总资产、今日交易）
   - 资产分布图表
   - 最近交易列表

2. **钱包管理组件**
   - 钱包列表展示
   - 钱包添加、编辑、删除
   - 多链钱包支持

3. **交易监控组件**
   - 实时交易列表
   - 交易详情查看
   - 交易类型（收入/支出）标记

4. **合约监控组件**
   - 智能合约交互记录
   - 合约方法调用追踪
   - 交易状态标记

5. **告警管理组件**
   - 告警规则配置
   - 告警历史查看
   - 风险等级标记

## 技术栈

### 后端技术栈

- Python 3.10+
- FastAPI
- SQLite
- Web3.py (以太坊交互)

### 前端技术栈

- React
- TypeScript
- Ant Design
- ECharts
- Zustand (状态管理)

## 项目结构

### 后端结构

```
wallet-monitor/backend/
├── main.py                # 后端入口
├── plugins/
│   ├── plugin_base.py     # 插件基类
│   ├── plugin_manager.py  # 插件管理器
│   └── wallet_monitor/    # 钱包监控插件
│       ├── plugin.py      # 插件入口
│       ├── blockchain/    # 区块链交互
│       ├── data/          # 数据处理
│       ├── alert/         # 告警系统
│       └── api/           # API接口
```

### 前端结构

```
wallet-monitor/frontend/src/plugins/wallet-monitor/
├── index.tsx             # 插件入口
├── manifest.json         # 插件配置
├── components/           # 组件目录
│   ├── Dashboard.tsx     # 仪表盘组件
│   ├── WalletManagement.tsx  # 钱包管理组件
│   ├── TransactionMonitor.tsx  # 交易监控组件
│   ├── ContractMonitor.tsx  # 合约监控组件
│   └── AlertManagement.tsx  # 告警管理组件
├── hooks/                # 自定义hooks
│   └── useBlockchain.ts  # 区块链交互hook
└── utils/                # 工具函数
    └── blockchain.ts     # 区块链相关工具函数
```

## 安装与使用

### 后端插件安装

1. **克隆项目**
   ```bash
   git clone https://github.com/your-repo/wallet-monitor-plugin.git
   cd wallet-monitor-plugin
   ```

2. **创建虚拟环境**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **安装依赖**
   ```bash
   uv sync
   ```

4. **启动后端服务**
   ```bash
   cd backend
   uvicorn main:app --reload
   ```

### 前端插件安装

1. **进入前端目录**
   ```bash
   cd frontend
   ```

2. **安装依赖**
   ```bash
   npm install
   ```

3. **启动前端开发服务器**
   ```bash
   npm run dev
   ```

## API接口

### 后端API接口

- **插件信息**
  - 路径: `GET /api/plugins/wallet-monitor/`
  - 返回插件基本信息

- **钱包管理**
  - 路径: `GET /api/plugins/wallet-monitor/wallets`
  - 返回钱包列表

  - 路径: `POST /api/plugins/wallet-monitor/wallets`
  - 添加新钱包

- **交易查询**
  - 路径: `GET /api/plugins/wallet-monitor/transactions`
  - 返回交易列表，支持按地址和链过滤

### 前端页面

- **仪表盘**
  - 路径: `/plugins/wallet-monitor/dashboard`
  - 展示钱包概览和资产分布

- **钱包管理**
  - 路径: `/plugins/wallet-monitor/wallets`
  - 管理钱包地址和配置

- **交易监控**
  - 路径: `/plugins/wallet-monitor/transactions`
  - 监控和查看交易记录

- **合约监控**
  - 路径: `/plugins/wallet-monitor/contracts`
  - 监控智能合约交互

- **告警管理**
  - 路径: `/plugins/wallet-monitor/alerts`
  - 管理告警规则和查看告警历史

## 配置说明

### 后端配置

- **数据库配置**
  - 默认使用SQLite数据库，存储路径为 `wallet_monitor.db`

- **区块链节点配置**
  - 以太坊节点: 默认使用Infura（需要替换为实际的API密钥）
  - BSC节点: 默认使用Binance Smart Chain官方节点

### 前端配置

- **API地址配置**
  - 默认API地址: `http://localhost:8000`
  - 可在前端代码中修改API地址

## 告警规则

### 内置告警规则

1. **大额转账**
   - 规则: 转账金额超过阈值（默认1 ETH）
   - 风险等级: 高

2. **陌生地址**
   - 规则: 与从未交互过的地址进行交易
   - 风险等级: 中

3. **频繁交易**
   - 规则: 短时间内（1小时）交易次数超过阈值（默认10笔）
   - 风险等级: 中

## 未来增强

1. **支持更多区块链**（Solana、Polygon等）
2. **实现WebSocket实时数据推送**
3. **添加机器学习异常检测**
4. **支持更多告警渠道**（Telegram、Email等）
5. **增强前端可视化效果**
6. **添加用户认证和权限管理**

## 贡献指南

1. **提交代码**
   - Fork 仓库
   - 创建分支
   - 提交代码
   - 发起 Pull Request

2. **报告问题**
   - 在 GitHub Issues 中报告问题
   - 提供详细的错误信息和复现步骤
   - 包括环境信息和插件版本

## 许可证

本项目采用 Apache License 2.0 许可证。

## 联系方式

- 项目地址: https://github.com/your-repo/wallet-monitor-plugin
- 文档地址: https://your-repo.github.io/wallet-monitor-plugin
