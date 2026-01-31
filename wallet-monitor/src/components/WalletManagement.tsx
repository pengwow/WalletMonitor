import React, { useState, useEffect } from 'react';
import {
  Card,
  Button,
  Table,
  Modal,
  Form,
  Input,
  Select,
  message,
  Spin,
  Typography,
  Space,
  Tag
} from 'antd';
import axios from 'axios';

const { Title, Text } = Typography;
const { Option } = Select;

interface Wallet {
  id: number;
  address: string;
  chain: string;
  name: string;
  description: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
  balance: number;
}

const WalletManagement: React.FC = () => {
  const [wallets, setWallets] = useState<Wallet[]>([]);
  const [loading, setLoading] = useState<boolean>(false);
  const [modalVisible, setModalVisible] = useState<boolean>(false);
  const [editingWallet, setEditingWallet] = useState<Wallet | null>(null);
  const [form] = Form.useForm();

  // 支持的区块链类型
  const supportedChains = ['ethereum', 'bsc', 'polygon', 'solana'];

  // 获取钱包列表
  const fetchWallets = async () => {
    setLoading(true);
    try {
      const response = await axios.get('/api/wallets');
      setWallets(response.data);
    } catch (error) {
      message.error('获取钱包列表失败');
      console.error('Error fetching wallets:', error);
    } finally {
      setLoading(false);
    }
  };

  // 初始化时获取钱包列表
  useEffect(() => {
    fetchWallets();
  }, []);

  // 打开添加钱包模态框
  const handleAddWallet = () => {
    setEditingWallet(null);
    form.resetFields();
    setModalVisible(true);
  };

  // 打开编辑钱包模态框
  const handleEditWallet = (wallet: Wallet) => {
    setEditingWallet(wallet);
    form.setFieldsValue({
      address: wallet.address,
      chain: wallet.chain,
      name: wallet.name,
      description: wallet.description,
      is_active: wallet.is_active
    });
    setModalVisible(true);
  };

  // 删除钱包
  const handleDeleteWallet = async (walletId: number) => {
    try {
      await axios.delete(`/api/wallets/${walletId}`);
      message.success('钱包删除成功');
      fetchWallets();
    } catch (error) {
      message.error('钱包删除失败');
      console.error('Error deleting wallet:', error);
    }
  };

  // 提交表单
  const handleSubmit = async () => {
    try {
      const values = await form.validateFields();
      
      if (editingWallet) {
        // 编辑钱包
        await axios.put(`/api/wallets/${editingWallet.id}`, values);
        message.success('钱包更新成功');
      } else {
        // 添加钱包
        await axios.post('/api/wallets', values);
        message.success('钱包添加成功');
      }
      
      setModalVisible(false);
      fetchWallets();
    } catch (error) {
      message.error('操作失败');
      console.error('Error submitting form:', error);
    }
  };

  // 钱包状态标签
  const getStatusTag = (isActive: boolean) => {
    return isActive ? (
      <Tag color="green">活跃</Tag>
    ) : (
      <Tag color="red">禁用</Tag>
    );
  };

  // 钱包列表列配置
  const columns = [
    {
      title: '钱包名称',
      dataIndex: 'name',
      key: 'name',
      render: (text: string) => <Text strong>{text || '未命名'}</Text>
    },
    {
      title: '钱包地址',
      dataIndex: 'address',
      key: 'address',
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
      title: '余额',
      dataIndex: 'balance',
      key: 'balance',
      render: (text: number) => <Text>${text.toFixed(4)}</Text>
    },
    {
      title: '状态',
      dataIndex: 'is_active',
      key: 'is_active',
      render: (text: boolean) => getStatusTag(text)
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      key: 'created_at',
      render: (text: string) => new Date(text).toLocaleString()
    },
    {
      title: '操作',
      key: 'action',
      render: (_: any, record: Wallet) => (
        <Space size="middle">
          <Button size="small" onClick={() => handleEditWallet(record)}>
            编辑
          </Button>
          <Button size="small" danger onClick={() => handleDeleteWallet(record.id)}>
            删除
          </Button>
        </Space>
      )
    }
  ];

  return (
    <div style={{ padding: '20px' }}>
      <Card
        title={
          <Space>
            <Title level={4}>钱包管理</Title>
            <Button type="primary" onClick={handleAddWallet}>
              添加钱包
            </Button>
          </Space>
        }
      >
        {loading ? (
          <Spin tip="加载中..." style={{ textAlign: 'center', padding: '40px' }} />
        ) : (
          <Table
            columns={columns}
            dataSource={wallets}
            rowKey="id"
            pagination={{ pageSize: 10 }}
            emptyText="暂无钱包数据"
          />
        )}
      </Card>

      {/* 添加/编辑钱包模态框 */}
      <Modal
        title={editingWallet ? '编辑钱包' : '添加钱包'}
        open={modalVisible}
        onOk={handleSubmit}
        onCancel={() => setModalVisible(false)}
        destroyOnClose
      >
        <Form form={form} layout="vertical">
          <Form.Item
            name="address"
            label="钱包地址"
            rules={[{ required: true, message: '请输入钱包地址' }]}
          >
            <Input placeholder="请输入钱包地址" />
          </Form.Item>

          <Form.Item
            name="chain"
            label="区块链"
            rules={[{ required: true, message: '请选择区块链' }]}
          >
            <Select placeholder="请选择区块链">
              {supportedChains.map(chain => (
                <Option key={chain} value={chain}>
                  {chain.charAt(0).toUpperCase() + chain.slice(1)}
                </Option>
              ))}
            </Select>
          </Form.Item>

          <Form.Item
            name="name"
            label="钱包名称"
            rules={[{ required: true, message: '请输入钱包名称' }]}
          >
            <Input placeholder="请输入钱包名称" />
          </Form.Item>

          <Form.Item
            name="description"
            label="钱包描述"
          >
            <Input.TextArea placeholder="请输入钱包描述" />
          </Form.Item>

          <Form.Item
            name="is_active"
            label="状态"
            initialValue={true}
          >
            <Select>
              <Option value={true}>活跃</Option>
              <Option value={false}>禁用</Option>
            </Select>
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default WalletManagement;
