import React, { useState, useEffect } from 'react';
import {
  Card,
  Button,
  Table,
  Select,
  Input,
  message,
  Spin,
  Typography,
  Space,
  Tag,
  DatePicker,
  Form,
  Collapse
} from 'antd';
import axios from 'axios';

const { Title, Text } = Typography;
const { Option } = Select;
const { RangePicker } = DatePicker;
const { Panel } = Collapse;

interface Transaction {
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
  block_hash: string;
  gas_used: number;
  gas_price: number;
  input_data: string;
  is_contract_interaction: boolean;
  contract_address: string;
  anomaly_score: number;
  risk_level: string;
  created_at: string;
}

const TransactionMonitor: React.FC = () => {
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [loading, setLoading] = useState<boolean>(false);
  const [filters, setFilters] = useState({
    wallet_address: '',
    chain: '',
    from_address: '',
    to_address: '',
    min_amount: '',
    max_amount: '',
    start_timestamp: null,
    end_timestamp: null,
    risk_level: ''
  });
  const [form] = Form.useForm();

  // 支持的区块链类型
  const supportedChains = ['ethereum', 'bsc', 'polygon', 'solana'];

  // 风险等级选项
  const riskLevels = ['low', 'medium', 'high'];

  // 获取交易列表
  const fetchTransactions = async () => {
    setLoading(true);
    try {
      const params = {
        wallet_address: filters.wallet_address,
        chain: filters.chain,
        limit: 100
      };
      const response = await axios.get('/api/plugins/wallet-monitor/transactions', { params });
      setTransactions(response.data);
    } catch (error) {
      message.error('获取交易列表失败');
      console.error('Error fetching transactions:', error);
    } finally {
      setLoading(false);
    }
  };

  // 初始化时获取交易列表
  useEffect(() => {
    fetchTransactions();
  }, [filters.wallet_address, filters.chain]);

  // 同步交易
  const handleSyncTransactions = async (walletAddress: string, chain: string) => {
    try {
      await axios.post('/api/plugins/wallet-monitor/transactions/sync', {
        wallet_address: walletAddress,
        chain: chain
      });
      message.success('交易同步成功');
      fetchTransactions();
    } catch (error) {
      message.error('交易同步失败');
      console.error('Error syncing transactions:', error);
    }
  };

  // 分析交易
  const handleAnalyzeTransactions = async (walletAddress: string, chain: string) => {
    try {
      const response = await axios.post('/api/plugins/wallet-monitor/transactions/analyze', {
        wallet_address: walletAddress,
        chain: chain
      });
      message.success('交易分析成功');
      console.log('Analysis result:', response.data);
    } catch (error) {
      message.error('交易分析失败');
      console.error('Error analyzing transactions:', error);
    }
  };

  // 处理筛选
  const handleFilter = async () => {
    try {
      const values = await form.validateFields();
      setFilters(values);
    } catch (error) {
      message.error('筛选失败');
      console.error('Error filtering:', error);
    }
  };

  // 重置筛选
  const handleReset = () => {
    form.resetFields();
    setFilters({
      wallet_address: '',
      chain: '',
      from_address: '',
      to_address: '',
      min_amount: '',
      max_amount: '',
      start_timestamp: null,
      end_timestamp: null,
      risk_level: ''
    });
  };

  // 交易状态标签
  const getStatusTag = (status: string) => {
    switch (status) {
      case 'success':
        return <Tag color="green">成功</Tag>;
      case 'failed':
        return <Tag color="red">失败</Tag>;
      case 'pending':
        return <Tag color="orange"> pending</Tag>;
      default:
        return <Tag color="blue">{status}</Tag>;
    }
  };

  // 风险等级标签
  const getRiskLevelTag = (riskLevel: string) => {
    switch (riskLevel) {
      case 'high':
        return <Tag color="red">高风险</Tag>;
      case 'medium':
        return <Tag color="orange">中风险</Tag>;
      case 'low':
        return <Tag color="green">低风险</Tag>;
      default:
        return <Tag color="blue">{riskLevel}</Tag>;
    }
  };

  // 交易列表列配置
  const columns = [
    {
      title: '交易哈希',
      dataIndex: 'hash',
      key: 'hash',
      render: (text: string) => <Text ellipsis>{text}</Text>
    },
    {
      title: '钱包地址',
      dataIndex: 'wallet_address',
      key: 'wallet_address',
      render: (text: string) => <Text ellipsis>{text}</Text>
    },
    {
      title: '区块链',
      dataIndex: 'chain',
      key: 'chain',
      render: (text: string) => (
        <Tag>{text.charAt(0).toUpperCase() + text.slice(1)}</Tag>
      )
    },
    {
      title: '发送地址',
      dataIndex: 'from_address',
      key: 'from_address',
      render: (text: string) => <Text ellipsis>{text}</Text>
    },
    {
      title: '接收地址',
      dataIndex: 'to_address',
      key: 'to_address',
      render: (text: string) => <Text ellipsis>{text}</Text>
    },
    {
      title: '金额',
      dataIndex: 'amount',
      key: 'amount',
      render: (text: number) => <Text>${text.toFixed(4)}</Text>
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      render: (text: string) => getStatusTag(text)
    },
    {
      title: '风险等级',
      dataIndex: 'risk_level',
      key: 'risk_level',
      render: (text: string) => getRiskLevelTag(text)
    },
    {
      title: '时间',
      dataIndex: 'timestamp',
      key: 'timestamp',
      render: (text: number) => new Date(text * 1000).toLocaleString()
    },
    {
      title: '合约交互',
      dataIndex: 'is_contract_interaction',
      key: 'is_contract_interaction',
      render: (text: boolean) => (
        <Tag color={text ? 'purple' : 'gray'}>
          {text ? '是' : '否'}
        </Tag>
      )
    }
  ];

  return (
    <div style={{ padding: '20px' }}>
      <Card
        title={
          <Space>
            <Title level={4}>交易监控</Title>
            <Button type="primary" onClick={() => fetchTransactions()}>
              刷新交易
            </Button>
          </Space>
        }
      >
        {/* 筛选条件 */}
        <Collapse defaultActiveKey={['1']}>
          <Panel header="筛选条件" key="1">
            <Form form={form} layout="inline" onFinish={handleFilter}>
              <Form.Item name="wallet_address" label="钱包地址">
                <Input placeholder="请输入钱包地址" />
              </Form.Item>
              <Form.Item name="chain" label="区块链">
                <Select placeholder="请选择区块链">
                  {supportedChains.map(chain => (
                    <Option key={chain} value={chain}>
                      {chain.charAt(0).toUpperCase() + chain.slice(1)}
                    </Option>
                  ))}
                </Select>
              </Form.Item>
              <Form.Item name="risk_level" label="风险等级">
                <Select placeholder="请选择风险等级">
                  {riskLevels.map(level => (
                    <Option key={level} value={level}>
                      {level.charAt(0).toUpperCase() + level.slice(1)}
                    </Option>
                  ))}
                </Select>
              </Form.Item>
              <Form.Item>
                <Space>
                  <Button type="primary" htmlType="submit">
                    筛选
                  </Button>
                  <Button onClick={handleReset}>
                    重置
                  </Button>
                </Space>
              </Form.Item>
            </Form>
          </Panel>
        </Collapse>

        {/* 交易列表 */}
        {loading ? (
          <Spin tip="加载中..." style={{ textAlign: 'center', padding: '40px' }} />
        ) : (
          <Table
            columns={columns}
            dataSource={transactions}
            rowKey="id"
            pagination={{ pageSize: 10 }}
            emptyText="暂无交易数据"
          />
        )}

        {/* 操作按钮 */}
        <Space style={{ marginTop: '20px' }}>
          <Button onClick={() => handleSyncTransactions(filters.wallet_address, filters.chain)}>
            同步交易
          </Button>
          <Button onClick={() => handleAnalyzeTransactions(filters.wallet_address, filters.chain)}>
            分析交易
          </Button>
        </Space>
      </Card>
    </div>
  );
};

export default TransactionMonitor;
