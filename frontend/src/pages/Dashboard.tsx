import React, { useState, useEffect, useRef } from 'react';
import {
  Card,
  Row,
  Col,
  Typography,
  Spin,
  Statistic,
  Space,
  Tag,
  Button
} from 'antd';
import axios from 'axios';
import * as echarts from 'echarts';

const { Title, Text } = Typography;

const Dashboard: React.FC = () => {
  const [stats, setStats] = useState({
    total_wallets: 0,
    total_transactions: 0,
    total_alerts: 0,
    total_value: 0
  });
  const [loading, setLoading] = useState<boolean>(true);
  const [assetDistribution, setAssetDistribution] = useState<any>(null);
  const [transactionTrends, setTransactionTrends] = useState<any>(null);
  const [alertStats, setAlertStats] = useState<any>(null);

  // 图表引用
  const assetChartRef = useRef<HTMLDivElement>(null);
  const transactionChartRef = useRef<HTMLDivElement>(null);
  const alertChartRef = useRef<HTMLDivElement>(null);

  // 图表实例
  const assetChart = useRef<echarts.ECharts | null>(null);
  const transactionChart = useRef<echarts.ECharts | null>(null);
  const alertChart = useRef<echarts.ECharts | null>(null);

  const fetchStats = async () => {
    try {
      const [walletsRes, transactionsRes, alertsRes] = await Promise.all([
        axios.get('/api/wallets').catch(() => ({ data: [] })),
        axios.get('/api/transactions').catch(() => ({ data: [] })),
        axios.get('/api/alerts').catch(() => ({ data: [] }))
      ]);

      const wallets = walletsRes.data;
      const transactions = transactionsRes.data;
      const alerts = alertsRes.data;

      const totalValue = wallets.reduce((sum: number, w: any) => sum + (w.balance || 0), 0);

      setStats({
        total_wallets: wallets.length,
        total_transactions: transactions.length,
        total_alerts: alerts.length,
        total_value: totalValue
      });

      const assetByChain: Record<string, number> = {};
      wallets.forEach((w: any) => {
        const chain = w.chain || 'unknown';
        assetByChain[chain] = (assetByChain[chain] || 0) + (w.balance || 0);
      });
      setAssetDistribution(assetByChain);

      const txByDay: Record<string, number> = {};
      const now = Date.now();
      for (let i = 6; i >= 0; i--) {
        const date = new Date(now - i * 86400000);
        const key = `${date.getMonth() + 1}/${date.getDate()}`;
        txByDay[key] = 0;
      }
      transactions.forEach((tx: any) => {
        if (tx.timestamp) {
          const date = new Date(tx.timestamp * 1000);
          const key = `${date.getMonth() + 1}/${date.getDate()}`;
          if (key in txByDay) {
            txByDay[key]++;
          }
        }
      });
      setTransactionTrends({
        dates: Object.keys(txByDay),
        counts: Object.values(txByDay)
      });

      const alertCounts = { low: 0, medium: 0, high: 0 };
      alerts.forEach((a: any) => {
        if (a.risk_level in alertCounts) {
          alertCounts[a.risk_level as keyof typeof alertCounts]++;
        }
      });
      setAlertStats(alertCounts);

      setLoading(false);
    } catch (error) {
      console.error('Error fetching stats:', error);
      setLoading(false);
    }
  };

  // 初始化时获取数据
  useEffect(() => {
    fetchStats();
  }, []);

  // 初始化图表
  useEffect(() => {
    if (!loading) {
      initCharts();
    }

    // 清理函数
    return () => {
      if (assetChart.current) {
        assetChart.current.dispose();
      }
      if (transactionChart.current) {
        transactionChart.current.dispose();
      }
      if (alertChart.current) {
        alertChart.current.dispose();
      }
    };
  }, [loading, assetDistribution, transactionTrends, alertStats]);

  // 初始化所有图表
  const initCharts = () => {
    initAssetChart();
    initTransactionChart();
    initAlertChart();
  };

  // 初始化资产分布图表
  const initAssetChart = () => {
    if (assetChartRef.current && assetDistribution) {
      assetChart.current = echarts.init(assetChartRef.current);
      
      const option = {
        title: {
          text: '资产分布',
          left: 'center'
        },
        tooltip: {
          trigger: 'item',
          formatter: '{a} <br/>{b}: ${c} ({d}%)'
        },
        legend: {
          orient: 'vertical',
          left: 'left'
        },
        series: [
          {
            name: '资产',
            type: 'pie',
            radius: '50%',
            data: [
              { value: assetDistribution.ethereum, name: 'Ethereum' },
              { value: assetDistribution.bsc, name: 'BSC' },
              { value: assetDistribution.polygon, name: 'Polygon' },
              { value: assetDistribution.solana, name: 'Solana' }
            ],
            emphasis: {
              itemStyle: {
                shadowBlur: 10,
                shadowOffsetX: 0,
                shadowColor: 'rgba(0, 0, 0, 0.5)'
              }
            }
          }
        ]
      };
      
      assetChart.current.setOption(option);
    }
  };

  // 初始化交易趋势图表
  const initTransactionChart = () => {
    if (transactionChartRef.current && transactionTrends) {
      transactionChart.current = echarts.init(transactionChartRef.current);
      
      const option = {
        title: {
          text: '交易趋势',
          left: 'center'
        },
        tooltip: {
          trigger: 'axis'
        },
        xAxis: {
          type: 'category',
          data: transactionTrends.dates
        },
        yAxis: {
          type: 'value'
        },
        series: [
          {
            data: transactionTrends.counts,
            type: 'line',
            smooth: true,
            itemStyle: {
              color: '#1890ff'
            }
          }
        ]
      };
      
      transactionChart.current.setOption(option);
    }
  };

  // 初始化告警统计图表
  const initAlertChart = () => {
    if (alertChartRef.current && alertStats) {
      alertChart.current = echarts.init(alertChartRef.current);
      
      const option = {
        title: {
          text: '告警统计',
          left: 'center'
        },
        tooltip: {
          trigger: 'item'
        },
        xAxis: {
          type: 'category',
          data: ['低风险', '中风险', '高风险']
        },
        yAxis: {
          type: 'value'
        },
        series: [
          {
            data: [
              { value: alertStats.low, itemStyle: { color: '#52c41a' } },
              { value: alertStats.medium, itemStyle: { color: '#faad14' } },
              { value: alertStats.high, itemStyle: { color: '#f5222d' } }
            ],
            type: 'bar'
          }
        ]
      };
      
      alertChart.current.setOption(option);
    }
  };

  // 处理窗口大小变化
  useEffect(() => {
    const handleResize = () => {
      if (assetChart.current) {
        assetChart.current.resize();
      }
      if (transactionChart.current) {
        transactionChart.current.resize();
      }
      if (alertChart.current) {
        alertChart.current.resize();
      }
    };

    window.addEventListener('resize', handleResize);
    return () => {
      window.removeEventListener('resize', handleResize);
    };
  }, []);

  return (
    <div style={{ padding: '20px' }}>
      <Card
        title={
          <Space>
            <Title level={4}>Dashboard</Title>
            <Button type="primary" onClick={fetchStats}>
              刷新数据
            </Button>
          </Space>
        }
      >
        {loading ? (
          <Spin tip="加载中..." style={{ textAlign: 'center', padding: '40px' }} />
        ) : (
          <>
            {/* 统计卡片 */}
            <Row gutter={[16, 16]} style={{ marginBottom: '20px' }}>
              <Col span={6}>
                <Card>
                  <Statistic
                    title="总钱包数"
                    value={stats.total_wallets}
                    prefix={<Tag color="blue">钱包</Tag>}
                  />
                </Card>
              </Col>
              <Col span={6}>
                <Card>
                  <Statistic
                    title="总交易数"
                    value={stats.total_transactions}
                    prefix={<Tag color="green">交易</Tag>}
                  />
                </Card>
              </Col>
              <Col span={6}>
                <Card>
                  <Statistic
                    title="总告警数"
                    value={stats.total_alerts}
                    prefix={<Tag color="red">告警</Tag>}
                  />
                </Card>
              </Col>
              <Col span={6}>
                <Card>
                  <Statistic
                    title="总资产价值"
                    value={stats.total_value}
                    prefix={<Tag color="purple">$</Tag>}
                  />
                </Card>
              </Col>
            </Row>

            {/* 图表区域 */}
            <Row gutter={[16, 16]}>
              <Col span={8}>
                <Card>
                  <div ref={assetChartRef} style={{ height: '300px' }} />
                </Card>
              </Col>
              <Col span={8}>
                <Card>
                  <div ref={transactionChartRef} style={{ height: '300px' }} />
                </Card>
              </Col>
              <Col span={8}>
                <Card>
                  <div ref={alertChartRef} style={{ height: '300px' }} />
                </Card>
              </Col>
            </Row>

            {/* 系统状态 */}
            <Row style={{ marginTop: '20px' }}>
              <Col span={24}>
                <Card title="系统状态">
                  <Space>
                    <Tag color="green">区块链连接正常</Tag>
                    <Tag color="green">数据存储正常</Tag>
                    <Tag color="green">告警系统正常</Tag>
                    <Tag color="blue">最后更新: {new Date().toLocaleString()}</Tag>
                  </Space>
                </Card>
              </Col>
            </Row>
          </>
        )}
      </Card>
    </div>
  );
};

export default Dashboard;
