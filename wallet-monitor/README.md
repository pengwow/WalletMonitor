# 区块链钱包监控系统

## 项目概述

这是一个区块链钱包监控系统，既可以作为独立服务运行，也可以作为quantcell的插件运行。

## 功能特性

- 多链钱包监控（以太坊、Solana等）
- 实时交易跟踪
- 智能合约交互监控
- 异常行为检测与告警
- 可视化Dashboard

## 运行模式

### 1. 独立服务模式

#### 启动后端服务
```bash
./run_backend.sh
```

#### 启动前端服务
```bash
./run_frontend.sh
```

### 2. 插件模式

#### 运行插件脚本
```bash
./run_as_plugin.sh
```

#### 然后将插件目录复制到quantcell中
```bash
# 后端插件
cp -r backend/plugins/wallet-monitor quantcell/backend/plugins/

# 前端插件
cp -r frontend/src/plugins/wallet-monitor quantcell/frontend/src/plugins/
```

#### 启动quantcell服务
```bash
# 启动后端
cd quantcell/backend && uvicorn main:app --reload

# 启动前端
cd quantcell/frontend && npm run dev
```

## 项目结构

```
wallet-monitor/
├── backend/           # 后端代码
│   ├── blockchain/    # 区块链交互模块
│   ├── data/          # 数据处理模块
│   ├── alert/         # 告警系统模块
│   ├── api/           # API接口模块
│   ├── plugins/       # 插件结构
│   └── main.py        # 后端入口
├── frontend/          # 前端代码
│   ├── src/           # 源代码
│   │   ├── components/ # 组件
│   │   ├── plugins/    # 插件结构
│   │   └── main.tsx    # 前端入口
│   └── package.json    # 前端依赖
├── run_backend.sh      # 启动后端服务脚本
├── run_frontend.sh     # 启动前端服务脚本
└── run_as_plugin.sh    # 以插件模式运行脚本
```

## 配置说明

### 后端配置

- 数据库：默认使用SQLite，存储路径为`wallet_monitor.db`
- 区块链节点：可在`blockchain`目录中配置

### 前端配置

- API地址：默认指向`http://localhost:8000`
- 主题：默认使用Ant Design主题

## 告警规则

- 大额转账：超过阈值的转账
- 陌生地址：与从未交互过的地址交易
- 频繁交易：短时间内交易次数过多

## 未来计划

- 支持更多区块链
- 实现WebSocket实时数据推送
- 添加机器学习异常检测
- 支持更多告警渠道
- 增强前端可视化效果
