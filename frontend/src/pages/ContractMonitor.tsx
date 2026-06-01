import React, { useState, useEffect } from 'react';
import { Card, Typography, Table, Space, Tag, Spin, Button, message } from 'antd';
import axios from 'axios';

const { Title } = Typography;

interface ContractTransaction {
  id: number;
  hash: string;
  wallet_address: string;
  chain: string;
  from_address: string;
  to_address: string;
  amount: number;
  status: string;
  timestamp: number;
  block_number: number;
  gas_used: number;
  is_contract_interaction: boolean;
  contract_address: string;
  risk_level: string;
  created_at: string;
}

const columns = [
  {
    title: '交易哈希',
    dataIndex: 'hash',
    key: 'hash',
    render: (text: string) => text ? `${text.slice(0, 10)}...${text.slice(-8)}` : '-',
  },
  {
    title: '合约地址',
    dataIndex: 'contract_address',
    key: 'contract_address',
    render: (text: string) => text ? `${text.slice(0, 10)}...${text.slice(-8)}` : '-',
  },
  {
    title: '钱包地址',
    dataIndex: 'wallet_address',
    key: 'wallet_address',
    render: (text: string) => text ? `${text.slice(0, 10)}...${text.slice(-8)}` : '-',
  },
  {
    title: '链',
    dataIndex: 'chain',
    key: 'chain',
    render: (text: string) => (
      <Tag color="blue">{text?.toUpperCase()}</Tag>
    ),
  },
  {
    title: '金额',
    dataIndex: 'amount',
    key: 'amount',
    render: (value: number) => value ? value.toFixed(4) : '0',
  },
  {
    title: '状态',
    dataIndex: 'status',
    key: 'status',
    render: (status: string) => (
      <Tag color={status === 'success' ? 'green' : status === 'pending' ? 'orange' : 'red'}>
        {status === 'success' ? '成功' : status === 'pending' ? '待确认' : '失败'}
      </Tag>
    ),
  },
  {
    title: '风险等级',
    dataIndex: 'risk_level',
    key: 'risk_level',
    render: (level: string) => {
      const colors: Record<string, string> = { high: 'red', medium: 'orange', low: 'green' };
      const labels: Record<string, string> = { high: '高', medium: '中', low: '低' };
      return <Tag color={colors[level] || 'blue'}>{labels[level] || level}</Tag>;
    },
  },
  {
    title: '时间',
    dataIndex: 'timestamp',
    key: 'timestamp',
    render: (ts: number) => ts ? new Date(ts * 1000).toLocaleString() : '-',
  },
];

export const ContractMonitor: React.FC = () => {
  const [transactions, setTransactions] = useState<ContractTransaction[]>([]);
  const [loading, setLoading] = useState<boolean>(false);

  const fetchContractTransactions = async () => {
    setLoading(true);
    try {
      const response = await axios.get('/api/transactions', {
        params: { limit: 100 }
      });
      const contractTxs = response.data.filter(
        (tx: ContractTransaction) => tx.is_contract_interaction
      );
      setTransactions(contractTxs);
    } catch (error) {
      message.error('获取合约交易失败');
      console.error('Error fetching contract transactions:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchContractTransactions();
  }, []);

  return (
    <div style={{ padding: '20px' }}>
      <Card
        title={
          <Space>
            <Title level={4} style={{ margin: 0 }}>智能合约监控</Title>
            <Button type="primary" onClick={fetchContractTransactions}>
              刷新数据
            </Button>
          </Space>
        }
      >
        {loading ? (
          <Spin tip="加载中..." style={{ textAlign: 'center', padding: '40px' }} />
        ) : (
          <Table
            columns={columns}
            dataSource={transactions}
            rowKey="id"
            pagination={{ pageSize: 10 }}
            emptyText="暂无合约交易数据"
          />
        )}
      </Card>
    </div>
  );
};

export default ContractMonitor;
