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
  Progress,
  Tooltip,
  Badge,
} from 'antd';
import {
  ReloadOutlined,
  SwapOutlined,
  ArrowUpOutlined,
  ArrowDownOutlined,
} from '@ant-design/icons';
import axios from 'axios';

const { Title, Text } = Typography;
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

interface BarData {
  long_count: number;
  short_count: number;
  long_pct: number;
  short_pct: number;
  long_bars: number;
  short_bars: number;
  width: number;
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
  bar: BarData;
  positions: PositionRow[];
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

const WhaleMonitor: React.FC = () => {
  const [coin, setCoin] = useState<string>('BTC');
  const [sort, setSort] = useState<string>('value');
  const [snapshot, setSnapshot] = useState<SnapshotData | null>(null);
  const [coinsData, setCoinsData] = useState<CoinsData | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [refreshing, setRefreshing] = useState<boolean>(false);
  const [autoRefresh, setAutoRefresh] = useState<boolean>(true);
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
      }, 30000);
    }
    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    };
  }, [autoRefresh, fetchSnapshot]);

  const handleRefresh = () => {
    fetchSnapshot(true);
  };

  const handleSortChange = (key: string) => {
    if (sort === key) {
      setSort(key);
    } else {
      setSort(key);
    }
  };

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
      title: 'Address',
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
      title: 'Dir',
      dataIndex: 'direction',
      key: 'direction',
      width: 70,
      align: 'center' as const,
      render: (text: string, record: PositionRow) => (
        <Tag color={record.direction_level === 'green' ? 'success' : 'error'} style={{ fontWeight: 'bold' }}>
          {text}
        </Tag>
      ),
    },
    {
      title: 'Value',
      dataIndex: 'value',
      key: 'value',
      width: 110,
      align: 'right' as const,
      sorter: true,
      render: (text: string) => <Text strong>{text}</Text>,
    },
    {
      title: 'uPnL',
      dataIndex: 'upnl',
      key: 'upnl',
      width: 110,
      align: 'right' as const,
      sorter: true,
      render: (text: string, record: PositionRow) => (
        <Text type={record.upnl_positive ? 'success' : 'danger'} style={{ fontWeight: 'bold' }}>
          {text}
        </Text>
      ),
    },
    {
      title: 'Margin',
      dataIndex: 'margin',
      key: 'margin',
      width: 100,
      align: 'right' as const,
    },
    {
      title: 'Entry',
      dataIndex: 'entry',
      key: 'entry',
      width: 100,
      align: 'right' as const,
    },
    {
      title: 'Liq Price',
      dataIndex: 'liq_price',
      key: 'liq_price',
      width: 110,
      align: 'right' as const,
      render: (text: string, record: PositionRow) => getLiqTag(record.liq_level, text),
    },
    {
      title: 'Lev',
      dataIndex: 'leverage',
      key: 'leverage',
      width: 70,
      align: 'center' as const,
      sorter: true,
      render: (text: string, record: PositionRow) => getLeverageTag(record.leverage_level, text),
    },
    {
      title: 'Mode',
      dataIndex: 'mode',
      key: 'mode',
      width: 80,
      align: 'center' as const,
      render: (text: string) => <Tag color="default">{text}</Tag>,
    },
    {
      title: 'Time',
      dataIndex: 'time',
      key: 'time',
      width: 100,
      align: 'center' as const,
      render: (text: string) => <Text type="secondary">{text}</Text>,
    },
  ];

  const renderLongShortBar = () => {
    if (!snapshot?.bar) return null;
    const { bar } = snapshot;
    if (!bar.long_count && !bar.short_count) {
      return <Text type="secondary">No data available</Text>;
    }
    return (
      <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
        <Text strong style={{ color: '#52c41a', minWidth: 80 }}>
          Long: {bar.long_count}
        </Text>
        <div style={{ flex: 1, display: 'flex', height: 24, borderRadius: 4, overflow: 'hidden' }}>
          <div
            style={{
              width: `${bar.long_pct}%`,
              background: 'linear-gradient(90deg, #52c41a, #73d13d)',
              transition: 'width 0.5s',
            }}
          />
          <div
            style={{
              width: `${bar.short_pct}%`,
              background: 'linear-gradient(90deg, #ff4d4f, #ff7875)',
              transition: 'width 0.5s',
            }}
          />
        </div>
        <Text strong style={{ color: '#ff4d4f', minWidth: 80, textAlign: 'right' }}>
          Short: {bar.short_count}
        </Text>
      </div>
    );
  };

  const renderPctLine = () => {
    if (!snapshot?.bar) return null;
    const { bar } = snapshot;
    return (
      <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: 4 }}>
        <Text style={{ color: '#52c41a' }}>Long: {bar.long_pct}%</Text>
        <Text style={{ color: '#ff4d4f' }}>Short: {bar.short_pct}%</Text>
      </div>
    );
  };

  return (
    <div style={{ padding: 20 }}>
      <style>{`
        @keyframes blink {
          0%, 100% { opacity: 1; }
          50% { opacity: 0.3; }
        }
      `}</style>

      <Card
        title={
          <Space>
            <Title level={4} style={{ margin: 0 }}>🐋 巨鲸监控</Title>
            <Select
              value={coin}
              onChange={setCoin}
              style={{ width: 120 }}
              showSearch
              placeholder="选择币种"
            >
              {coinsData?.common.map((c) => (
                <Option key={c} value={c}>{c}</Option>
              ))}
              {coinsData?.coins
                .filter((c) => !coinsData.common.includes(c))
                .map((c) => (
                  <Option key={c} value={c}>{c}</Option>
                ))}
            </Select>
          </Space>
        }
        extra={
          <Space>
            <Select
              value={sort}
              onChange={handleSortChange}
              style={{ width: 130 }}
              size="small"
            >
              <Option value="value">按价值排序</Option>
              <Option value="upnl">按 uPnL 排序</Option>
              <Option value="leverage">按杠杆排序</Option>
            </Select>
            <Button
              icon={<SwapOutlined />}
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
            >
              刷新
            </Button>
          </Space>
        }
      >
        {loading ? (
          <Spin tip="加载中..." style={{ display: 'block', textAlign: 'center', padding: 60 }} />
        ) : (
          <>
            <Card size="small" style={{ marginBottom: 16, background: '#fafafa' }}>
              <div style={{ marginBottom: 8 }}>
                {renderLongShortBar()}
                {renderPctLine()}
              </div>
              <div style={{ marginTop: 8 }}>
                <Text type="secondary">
                  24h Liquidation: <Tag>N/A</Tag> (接口暂不可用)
                </Text>
              </div>
            </Card>

            <Table
              columns={columns}
              dataSource={snapshot?.positions || []}
              rowKey="address"
              size="small"
              pagination={false}
              scroll={{ y: 'calc(100vh - 420px)' }}
              style={{ marginTop: 8 }}
              onChange={(pagination, filters, sorter: any) => {
                if (sorter.columnKey === 'value') handleSortChange('value');
                if (sorter.columnKey === 'upnl') handleSortChange('upnl');
                if (sorter.columnKey === 'leverage') handleSortChange('leverage');
              }}
            />

            <div style={{ marginTop: 12, textAlign: 'right' }}>
              <Space>
                <Badge
                  status={autoRefresh ? 'processing' : 'default'}
                  text={autoRefresh ? '自动刷新中' : '手动模式'}
                />
                <Text type="secondary">持仓数: {snapshot?.positionCount || 0}</Text>
                <Text type="secondary">更新: {snapshot?.lastUpdate}</Text>
              </Space>
            </div>
          </>
        )}
      </Card>
    </div>
  );
};

export default WhaleMonitor;
