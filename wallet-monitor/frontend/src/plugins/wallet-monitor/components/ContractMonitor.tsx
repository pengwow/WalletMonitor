import React from 'react';
import { Card, Typography, Table, Space, Tag } from 'antd';

const { Title, Paragraph } = Typography;

const columns = [
  {
    title: '合约地址',
    dataIndex: 'address',
    key: 'address',
  },
  {
    title: '合约名称',
    dataIndex: 'name',
    key: 'name',
  },
  {
    title: '交互方法',
    dataIndex: 'method',
    key: 'method',
  },
  {
    title: '状态',
    dataIndex: 'status',
    key: 'status',
    render: (status: string) => (
      <Tag color={status === 'success' ? 'green' : 'red'}>
        {status === 'success' ? '成功' : '失败'}
      </Tag>
    ),
  },
  {
    title: '时间',
    dataIndex: 'time',
    key: 'time',
  },
];

const data = [
  {
    key: '1',
    address: '0x1234567890123456789012345678901234567890',
    name: 'Uniswap V3',
    method: 'swapExactTokensForTokens',
    status: 'success',
    time: '2024-01-31 12:00:00',
  },
  {
    key: '2',
    address: '0x0987654321098765432109876543210987654321',
    name: 'Aave',
    method: 'deposit',
    status: 'success',
    time: '2024-01-31 11:30:00',
  },
];

export const ContractMonitor: React.FC = () => {
  return (
    <div style={{ padding: '20px' }}>
      <Title level={2}>智能合约监控</Title>
      <Card>
        <Table columns={columns} dataSource={data} />
      </Card>
    </div>
  );
};

export default ContractMonitor;
