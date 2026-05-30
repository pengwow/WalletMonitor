import React, { useState, useEffect, useRef, useCallback } from 'react';
import {
  Card,
  Table,
  Select,
  Space,
  Tag,
  Typography,
  Spin,
  Button,
  Tooltip,
  Badge,
  Row,
  Col,
  Divider,
} from 'antd';
import {
  ReloadOutlined,
  PauseCircleOutlined,
  PlayCircleOutlined,
  SwapOutlined,
  WarningOutlined,
  ThunderboltOutlined,
} from '@ant-design/icons';
import axios from 'axios';

const { Text } = Typography;
const { Option } = Select;

interface PositionRow {
  address: string;
  direction: string;
  direction_level: string;
  value: string;
  value_raw: number;
  upnl: string;
  upnl_positive: boolean;
  upnl_raw: number;
  margin: string;
  entry: string;
  liq_price: string;
  liq_level: string;
  leverage: string;
  leverage_level: string;
  leverage_raw: number;
  mode: string;
  time: string;
}

interface SnapshotData {
  coin: string;
  stats: {
    longCount: number;
    shortCount: number;
    total: number;
    longPct: number;
    shortPct: number;
  };
  bar: {
    long_count: number;
    short_count: number;
    long_pct: number;
    short_pct: number;
    long_bars: number;
    short_bars: number;
    width: number;
  };
  positions: PositionRow[];
  risk: {
    at_risk_count: number;
    at_risk_value: number;
    at_risk_value_str: string;
    high_lev_count: number;
    leverage_dist: Record<string, number>;
    total_pnl: number;
    total_pnl_str: string;
  };
  positionCount: number;
  lastUpdate: string;
  sortKey: string;
  sortReverse: boolean;
}

interface CoinsData {
  coins: string[];
  common: string[];
  total: number;
}

const API_PREFIX = '/api/plugins/wallet-monitor';

const COMMON_COINS = ['BTC', 'ETH', 'SOL', 'DOGE', 'XRP', 'SUI', 'AVAX', 'BNB', 'LINK', 'ARB', 'OP', 'kPEPE'];

const PctBar: React.FC<{ long: number; short: number }> = ({ long, short }) => {
  const total = long + short;
  if (total === 0) return <Text type="secondary">{'─'.repeat(24)}</Text>;
  const longPct = long / total;
  const longWidth = Math.round(longPct * 24);
  const shortWidth = 24 - longWidth;
  return (
    <span style={{ fontFamily: 'monospace', letterSpacing: 2 }}>
      <span style={{ color: '#52c41a', fontWeight: 'bold' }}>{'▓'.repeat(longWidth)}</span>
      <span style={{ color: '#ff4d4f', fontWeight: 'bold' }}>{'▓'.repeat(shortWidth)}</span>
    </span>
  );
};

const WhaleWatcher: React.FC = () => {
  const [coin, setCoin] = useState<string>('BTC');
  const [sort, setSort] = useState<string>('value');
  const [snapshot, setSnapshot] = useState<SnapshotData | null>(null);
  const [coinsData, setCoinsData] = useState<CoinsData | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [refreshing, setRefreshing] = useState<boolean>(false);
  const [autoRefresh, setAutoRefresh] = useState<boolean>(true);
  const [refreshInterval, setRefreshInterval] = useState<number>(30);
  const intervalRef = useRef<NodeJS.Timeout | null>(null);

  const fetchCoins = useCallback(async () => {
    try {
      const resp = await axios.get(`${API_PREFIX}/whales/coins`);
      setCoinsData(resp.data);
    } catch (err) {
      console.error('Failed to fetch coins:', err);
    }
  }, []);

  const fetchSnapshot = useCallback(async (showRefreshing = false) => {
    try {
      if (showRefreshing) setRefreshing(true);
      const resp = await axios.get(`${API_PREFIX}/whales/snapshot`, {
        params: { coin, sort },
      });
      setSnapshot(resp.data);
    } catch (err) {
      console.error('Failed to fetch snapshot:', err);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [coin, sort]);

  useEffect(() => {
    fetchCoins();
  }, [fetchCoins]);

  useEffect(() => {
    setLoading(true);
    fetchSnapshot();
  }, [fetchSnapshot]);

  useEffect(() => {
    if (autoRefresh) {
      intervalRef.current = setInterval(() => {
        fetchSnapshot();
      }, refreshInterval * 1000);
    }
    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    };
  }, [autoRefresh, refreshInterval, fetchSnapshot]);

  const handleRefresh = () => fetchSnapshot(true);

  const getLeverageTag = (level: string, text: string) => {
    if (level === 'danger') {
      return <Tag color="red" style={{ fontWeight: 'bold' }}>{text}</Tag>;
    }
    if (level === 'warn') {
      return <Tag color="orange">{text}</Tag>;
    }
    return <Tag>{text}</Tag>;
  };

  const getLiqTag = (level: string, text: string) => {
    if (level === 'danger') {
      return (
        <Tooltip title="爆仓风险！清算价距离开仓价不足5%">
          <Tag color="red" style={{ fontWeight: 'bold', animation: 'blink 1s infinite' }}>
            {text}
          </Tag>
        </Tooltip>
      );
    }
    return <Tag>{text}</Tag>;
  };

  const columns = [
    {
      title: '#',
      key: 'index',
      width: 40,
      render: (_: any, __: any, index: number) => <Text type="secondary">{index + 1}</Text>,
    },
    {
      title: '地址',
      dataIndex: 'address',
      key: 'address',
      width: 130,
      render: (text: string) => (
        <Text copyable={{ text }} style={{ fontFamily: 'monospace', fontSize: 12 }}>
          {text}
        </Text>
      ),
    },
    {
      title: '方向',
      dataIndex: 'direction',
      key: 'direction',
      width: 70,
      align: 'center' as const,
      render: (text: string, record: PositionRow) => {
        if (record.direction_level === 'green') {
          return <Tag color="success" style={{ fontWeight: 'bold' }}>多 ▲</Tag>;
        }
        if (record.direction_level === 'red') {
          return <Tag color="error" style={{ fontWeight: 'bold' }}>空 ▼</Tag>;
        }
        return <Tag>─</Tag>;
      },
    },
    {
      title: '持仓价值',
      dataIndex: 'value',
      key: 'value',
      width: 110,
      align: 'right' as const,
      sorter: true,
      render: (text: string) => <Text strong>{text}</Text>,
    },
    {
      title: '未实现盈亏',
      dataIndex: 'upnl',
      key: 'upnl',
      width: 120,
      align: 'right' as const,
      sorter: true,
      render: (text: string, record: PositionRow) => {
        if (record.upnl_raw > 0) {
          return <Text style={{ color: '#52c41a', fontWeight: 'bold' }}>+{text}</Text>;
        }
        if (record.upnl_raw < 0) {
          return <Text style={{ color: '#ff4d4f', fontWeight: 'bold' }}>{text}</Text>;
        }
        return <Text type="secondary">{text}</Text>;
      },
    },
    {
      title: '保证金',
      dataIndex: 'margin',
      key: 'margin',
      width: 100,
      align: 'right' as const,
    },
    {
      title: '开仓价',
      dataIndex: 'entry',
      key: 'entry',
      width: 100,
      align: 'right' as const,
    },
    {
      title: '清算价',
      dataIndex: 'liq_price',
      key: 'liq_price',
      width: 110,
      align: 'right' as const,
      render: (text: string, record: PositionRow) => getLiqTag(record.liq_level, text),
    },
    {
      title: '杠杆',
      dataIndex: 'leverage',
      key: 'leverage',
      width: 70,
      align: 'center' as const,
      sorter: true,
      render: (text: string, record: PositionRow) => getLeverageTag(record.leverage_level, text),
    },
    {
      title: '模式',
      dataIndex: 'mode',
      key: 'mode',
      width: 80,
      align: 'center' as const,
      render: (text: string) => <Tag color="default">{text}</Tag>,
    },
    {
      title: '时间',
      dataIndex: 'time',
      key: 'time',
      width: 100,
      align: 'center' as const,
      render: (text: string) => <Text type="secondary">{text}</Text>,
    },
  ];

  const risk = snapshot?.risk;
  const stats = snapshot?.stats;

  return (
    <div style={{ padding: 16, height: '100%', display: 'flex', flexDirection: 'column' }}>
      <style>{`
        @keyframes blink {
          0%, 100% { opacity: 1; }
          50% { opacity: 0.3; }
        }
      `}</style>

      {/* Header */}
      <Card
        size="small"
        style={{ marginBottom: 12, background: '#001529', border: 'none' }}
        bodyStyle={{ padding: '8px 16px' }}
      >
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <Space size="large">
            <Text style={{ color: '#1890ff', fontWeight: 'bold', fontSize: 16 }}>
              [HypeWatcher]
            </Text>
            <Select
              value={coin}
              onChange={setCoin}
              style={{ width: 120 }}
              showSearch
              size="small"
            >
              {coinsData?.common.map((c) => (
                <Option key={c} value={c}>{c}</Option>
              ))}
              {coinsData?.coins
                ?.filter((c) => !coinsData.common.includes(c))
                .map((c) => (
                  <Option key={c} value={c}>{c}</Option>
                ))}
            </Select>
          </Space>
          <Space>
            <Text type="secondary">刷新: {refreshInterval}s</Text>
            <Text type="secondary">更新: {snapshot?.lastUpdate || '--:--:--'}</Text>
          </Space>
        </div>
      </Card>

      {/* Stats Panel */}
      <Card
        size="small"
        style={{ marginBottom: 12 }}
        title={
          <Space>
            <SwapOutlined />
            <span>{coin} 多空比例 & 风险</span>
          </Space>
        }
        extra={
          <Space>
            <Select
              value={sort}
              onChange={setSort}
              style={{ width: 120 }}
              size="small"
            >
              <Option value="value">按价值排序</Option>
              <Option value="upnl">按 uPnL 排序</Option>
              <Option value="leverage">按杠杆排序</Option>
            </Select>
            <Select
              value={refreshInterval}
              onChange={setRefreshInterval}
              style={{ width: 90 }}
              size="small"
            >
              <Option value={10}>10s</Option>
              <Option value={30}>30s</Option>
              <Option value={60}>60s</Option>
              <Option value={120}>120s</Option>
            </Select>
            <Button
              icon={autoRefresh ? <PauseCircleOutlined /> : <PlayCircleOutlined />}
              size="small"
              type={autoRefresh ? 'primary' : 'default'}
              onClick={() => setAutoRefresh(!autoRefresh)}
            >
              {autoRefresh ? '自动' : '手动'}
            </Button>
            <Button
              icon={<ReloadOutlined spin={refreshing} />}
              onClick={handleRefresh}
              loading={refreshing}
              size="small"
            >
              刷新
            </Button>
          </Space>
        }
      >
        {loading ? (
          <Spin tip="加载中..." style={{ display: 'block', textAlign: 'center', padding: 40 }} />
        ) : (
          <>
            {/* Long/Short Bar */}
            <Row gutter={16} align="middle" style={{ marginBottom: 12 }}>
              <Col span={4} style={{ textAlign: 'right' }}>
                <Text strong style={{ color: '#52c41a', fontSize: 16 }}>
                  Long {stats?.longCount || 0}
                </Text>
              </Col>
              <Col span={16} style={{ textAlign: 'center' }}>
                <PctBar long={stats?.longCount || 0} short={stats?.shortCount || 0} />
              </Col>
              <Col span={4}>
                <Text strong style={{ color: '#ff4d4f', fontSize: 16 }}>
                  {stats?.shortCount || 0} Short
                </Text>
              </Col>
            </Row>
            <Row gutter={16} style={{ marginBottom: 12 }}>
              <Col span={4} style={{ textAlign: 'right' }}>
                <Text style={{ color: '#52c41a' }}>{stats?.longPct?.toFixed(1) || 0}%</Text>
              </Col>
              <Col span={16}>
                <div style={{ textAlign: 'center', color: '#999' }}>{'─'.repeat(32)}</div>
              </Col>
              <Col span={4}>
                <Text style={{ color: '#ff4d4f' }}>{stats?.shortPct?.toFixed(1) || 0}%</Text>
              </Col>
            </Row>

            <Divider style={{ margin: '8px 0' }} />

            {/* Risk Metrics */}
            <Row gutter={24}>
              <Col>
                <Space>
                  <WarningOutlined style={{ color: risk?.at_risk_count ? '#ff4d4f' : '#52c41a' }} />
                  <Text strong>⚠ Liq Risk: </Text>
                  {risk?.at_risk_count ? (
                    <Tag color="error">{risk.at_risk_count} pos ({risk.at_risk_value_str})</Tag>
                  ) : (
                    <Tag color="success">None</Tag>
                  )}
                </Space>
              </Col>
              <Col>
                <Space>
                  <ThunderboltOutlined style={{ color: risk?.high_lev_count ? '#ff4d4f' : '#d9d9d9' }} />
                  <Text strong>🔴 {'≥20x'}: </Text>
                  <Tag color={risk?.high_lev_count ? 'error' : 'default'}>
                    {risk?.high_lev_count || 0}
                  </Tag>
                </Space>
              </Col>
              <Col>
                <Space>
                  <Text strong>Σ PnL: </Text>
                  <Text style={{ color: (risk?.total_pnl || 0) >= 0 ? '#52c41a' : '#ff4d4f', fontWeight: 'bold' }}>
                    {risk?.total_pnl_str || '$0'}
                  </Text>
                </Space>
              </Col>
              {risk?.leverage_dist && (
                <Col>
                  <Text type="secondary">
                    {Object.entries(risk.leverage_dist).map(([k, v]) => `${k}:${v}`).join('  ')}
                  </Text>
                </Col>
              )}
            </Row>
          </>
        )}
      </Card>

      {/* Positions Table */}
      <Card
        size="small"
        style={{ flex: 1, display: 'flex', flexDirection: 'column' }}
        bodyStyle={{ flex: 1, padding: 0 }}
        title={
          <Space>
            <span>🐋 鲸鱼持仓列表</span>
            <Tag>{snapshot?.positionCount || 0} 条</Tag>
          </Space>
        }
        extra={
          snapshot?.positions && snapshot.positions.length > 0 ? (
            <Space>
              <Text type="secondary">
                多头总值:{' '}
                <Text style={{ color: '#52c41a' }}>
                  {snapshot.positions
                    .filter((r) => r.direction_level === 'green')
                    .reduce((sum, r) => sum + r.value_raw, 0)
                    .toLocaleString('en-US', { style: 'currency', currency: 'USD', notation: 'compact' })}
                </Text>
              </Text>
              <Text type="secondary">
                空头总值:{' '}
                <Text style={{ color: '#ff4d4f' }}>
                  {snapshot.positions
                    .filter((r) => r.direction_level === 'red')
                    .reduce((sum, r) => sum + r.value_raw, 0)
                    .toLocaleString('en-US', { style: 'currency', currency: 'USD', notation: 'compact' })}
                </Text>
              </Text>
            </Space>
          ) : null
        }
      >
        <Table
          columns={columns}
          dataSource={snapshot?.positions || []}
          rowKey="address"
          size="small"
          pagination={false}
          scroll={{ y: 'calc(100vh - 480px)' }}
          loading={loading}
          onChange={(_pagination, _filters, sorter: any) => {
            if (sorter.columnKey === 'value') setSort('value');
            if (sorter.columnKey === 'upnl') setSort('upnl');
            if (sorter.columnKey === 'leverage') setSort('leverage');
          }}
        />
      </Card>

      {/* Footer */}
      <Card
        size="small"
        style={{ marginTop: 12, background: '#001529', border: 'none' }}
        bodyStyle={{ padding: '6px 16px' }}
      >
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <Space size="large">
            <Badge
              status={autoRefresh ? 'processing' : 'default'}
              text={<Text style={{ color: '#fff' }}>{autoRefresh ? '自动刷新中' : '手动模式'}</Text>}
            />
            <Text type="secondary" style={{ color: '#999' }}>
              排序: {sort === 'value' ? '持仓价值' : sort === 'upnl' ? '未实现盈亏' : '杠杆'}{' '}
              {snapshot?.sortReverse ? '↓' : '↑'}
            </Text>
          </Space>
          <Space size="large">
            <Text type="secondary" style={{ color: '#999' }}>
              数据来源: hyperbot.network/whales
            </Text>
          </Space>
        </div>
      </Card>
    </div>
  );
};

export default WhaleWatcher;
