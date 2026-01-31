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
  Form,
  Collapse,
  Modal
} from 'antd';
import axios from 'axios';

const { Title, Text } = Typography;
const { Option } = Select;
const { Panel } = Collapse;

interface Alert {
  id: number;
  wallet_address: string;
  chain: string;
  alert_type: string;
  message: string;
  risk_level: string;
  transaction_hash: string;
  status: string;
  created_at: string;
  resolved_at: string;
}

interface AlertRule {
  id: number;
  name: string;
  description: string;
  rule_type: string;
  threshold: number;
  enabled: boolean;
  created_at: string;
  updated_at: string;
}

const AlertManagement: React.FC = () => {
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [rules, setRules] = useState<AlertRule[]>([]);
  const [loading, setLoading] = useState<boolean>(false);
  const [rulesLoading, setRulesLoading] = useState<boolean>(false);
  const [filters, setFilters] = useState({
    wallet_address: '',
    chain: '',
    risk_level: ''
  });
  const [form] = Form.useForm();
  const [ruleForm] = Form.useForm();
  const [modalVisible, setModalVisible] = useState<boolean>(false);
  const [editingRule, setEditingRule] = useState<AlertRule | null>(null);

  // 支持的区块链类型
  const supportedChains = ['ethereum', 'bsc', 'polygon', 'solana'];

  // 风险等级选项
  const riskLevels = ['low', 'medium', 'high'];

  // 告警类型选项
  const alertTypes = ['transaction', 'balance', 'contract', 'anomaly'];

  // 获取告警列表
  const fetchAlerts = async () => {
    setLoading(true);
    try {
      const params = {
        wallet_address: filters.wallet_address,
        chain: filters.chain,
        limit: 100
      };
      const response = await axios.get('/api/alerts', { params });
      setAlerts(response.data);
    } catch (error) {
      message.error('获取告警列表失败');
      console.error('Error fetching alerts:', error);
    } finally {
      setLoading(false);
    }
  };

  // 获取告警规则列表
  const fetchAlertRules = async () => {
    setRulesLoading(true);
    try {
      const response = await axios.get('/api/alerts/rules');
      setRules(response.data);
    } catch (error) {
      message.error('获取告警规则列表失败');
      console.error('Error fetching alert rules:', error);
    } finally {
      setRulesLoading(false);
    }
  };

  // 初始化时获取数据
  useEffect(() => {
    fetchAlerts();
    fetchAlertRules();
  }, [filters.wallet_address, filters.chain]);

  // 解决告警
  const handleResolveAlert = async (alertId: number) => {
    try {
      await axios.post(`/api/alerts/resolve/${alertId}`);
      message.success('告警解决成功');
      fetchAlerts();
    } catch (error) {
      message.error('告警解决失败');
      console.error('Error resolving alert:', error);
    }
  };

  // 测试告警
  const handleTestAlert = async (walletAddress: string, chain: string, alertType: string) => {
    try {
      await axios.post('/api/alerts/test', {
        wallet_address: walletAddress,
        chain: chain,
        alert_type: alertType
      });
      message.success('测试告警创建成功');
      fetchAlerts();
    } catch (error) {
      message.error('测试告警创建失败');
      console.error('Error creating test alert:', error);
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
      risk_level: ''
    });
  };

  // 打开添加规则模态框
  const handleAddRule = () => {
    setEditingRule(null);
    ruleForm.resetFields();
    setModalVisible(true);
  };

  // 打开编辑规则模态框
  const handleEditRule = (rule: AlertRule) => {
    setEditingRule(rule);
    ruleForm.setFieldsValue({
      name: rule.name,
      description: rule.description,
      rule_type: rule.rule_type,
      threshold: rule.threshold,
      enabled: rule.enabled
    });
    setModalVisible(true);
  };

  // 删除规则
  const handleDeleteRule = async (ruleId: number) => {
    try {
      await axios.delete(`/api/alerts/rules/${ruleId}`);
      message.success('告警规则删除成功');
      fetchAlertRules();
    } catch (error) {
      message.error('告警规则删除失败');
      console.error('Error deleting alert rule:', error);
    }
  };

  // 提交规则表单
  const handleSubmitRule = async () => {
    try {
      const values = await ruleForm.validateFields();
      
      if (editingRule) {
        // 编辑规则
        await axios.put(`/api/alerts/rules/${editingRule.id}`, values);
        message.success('告警规则更新成功');
      } else {
        // 添加规则
        await axios.post('/api/alerts/rules', values);
        message.success('告警规则添加成功');
      }
      
      setModalVisible(false);
      fetchAlertRules();
    } catch (error) {
      message.error('操作失败');
      console.error('Error submitting rule form:', error);
    }
  };

  // 告警状态标签
  const getStatusTag = (status: string) => {
    switch (status) {
      case 'resolved':
        return <Tag color="green">已解决</Tag>;
      case 'pending':
        return <Tag color="orange">待处理</Tag>;
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

  // 告警列表列配置
  const alertColumns = [
    {
      title: '告警类型',
      dataIndex: 'alert_type',
      key: 'alert_type',
      render: (text: string) => (
        <Tag>{text.charAt(0).toUpperCase() + text.slice(1)}</Tag>
      )
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
      title: '告警信息',
      dataIndex: 'message',
      key: 'message',
      render: (text: string) => <Text ellipsis>{text}</Text>
    },
    {
      title: '风险等级',
      dataIndex: 'risk_level',
      key: 'risk_level',
      render: (text: string) => getRiskLevelTag(text)
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      render: (text: string) => getStatusTag(text)
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
      render: (_: any, record: Alert) => (
        <Space size="middle">
          {record.status === 'pending' && (
            <Button size="small" type="primary" onClick={() => handleResolveAlert(record.id)}>
              解决
            </Button>
          )}
        </Space>
      )
    }
  ];

  // 告警规则列表列配置
  const ruleColumns = [
    {
      title: '规则名称',
      dataIndex: 'name',
      key: 'name',
      render: (text: string) => <Text strong>{text}</Text>
    },
    {
      title: '规则类型',
      dataIndex: 'rule_type',
      key: 'rule_type',
      render: (text: string) => (
        <Tag>{text.charAt(0).toUpperCase() + text.slice(1)}</Tag>
      )
    },
    {
      title: '阈值',
      dataIndex: 'threshold',
      key: 'threshold',
      render: (text: number) => <Text>{text}</Text>
    },
    {
      title: '状态',
      dataIndex: 'enabled',
      key: 'enabled',
      render: (text: boolean) => (
        <Tag color={text ? 'green' : 'red'}>
          {text ? '启用' : '禁用'}
        </Tag>
      )
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
      render: (_: any, record: AlertRule) => (
        <Space size="middle">
          <Button size="small" onClick={() => handleEditRule(record)}>
            编辑
          </Button>
          <Button size="small" danger onClick={() => handleDeleteRule(record.id)}>
            删除
          </Button>
        </Space>
      )
    }
  ];

  return (
    <div style={{ padding: '20px' }}>
      {/* 告警列表 */}
      <Card
        title={
          <Space>
            <Title level={4}>告警管理</Title>
            <Button type="primary" onClick={() => fetchAlerts()}>
              刷新告警
            </Button>
          </Space>
        }
        style={{ marginBottom: '20px' }}
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

        {/* 告警列表 */}
        {loading ? (
          <Spin tip="加载中..." style={{ textAlign: 'center', padding: '40px' }} />
        ) : (
          <Table
            columns={alertColumns}
            dataSource={alerts}
            rowKey="id"
            pagination={{ pageSize: 10 }}
            emptyText="暂无告警数据"
          />
        )}

        {/* 测试告警按钮 */}
        <Space style={{ marginTop: '20px' }}>
          <Button onClick={() => handleTestAlert(filters.wallet_address, filters.chain, 'transaction')}>
            测试交易告警
          </Button>
          <Button onClick={() => handleTestAlert(filters.wallet_address, filters.chain, 'balance')}>
            测试余额告警
          </Button>
          <Button onClick={() => handleTestAlert(filters.wallet_address, filters.chain, 'anomaly')}>
            测试异常告警
          </Button>
        </Space>
      </Card>

      {/* 告警规则 */}
      <Card
        title={
          <Space>
            <Title level={4}>告警规则</Title>
            <Button type="primary" onClick={handleAddRule}>
              添加规则
            </Button>
          </Space>
        }
      >
        {rulesLoading ? (
          <Spin tip="加载中..." style={{ textAlign: 'center', padding: '40px' }} />
        ) : (
          <Table
            columns={ruleColumns}
            dataSource={rules}
            rowKey="id"
            pagination={{ pageSize: 10 }}
            emptyText="暂无告警规则"
          />
        )}
      </Card>

      {/* 添加/编辑告警规则模态框 */}
      <Modal
        title={editingRule ? '编辑告警规则' : '添加告警规则'}
        open={modalVisible}
        onOk={handleSubmitRule}
        onCancel={() => setModalVisible(false)}
        destroyOnClose
      >
        <Form form={ruleForm} layout="vertical">
          <Form.Item
            name="name"
            label="规则名称"
            rules={[{ required: true, message: '请输入规则名称' }]}
          >
            <Input placeholder="请输入规则名称" />
          </Form.Item>
          <Form.Item
            name="description"
            label="规则描述"
          >
            <Input.TextArea placeholder="请输入规则描述" />
          </Form.Item>
          <Form.Item
            name="rule_type"
            label="规则类型"
            rules={[{ required: true, message: '请选择规则类型' }]}
          >
            <Select placeholder="请选择规则类型">
              {alertTypes.map(type => (
                <Option key={type} value={type}>
                  {type.charAt(0).toUpperCase() + type.slice(1)}
                </Option>
              ))}
            </Select>
          </Form.Item>
          <Form.Item
            name="threshold"
            label="阈值"
            rules={[{ required: true, message: '请输入阈值' }]}
          >
            <Input type="number" placeholder="请输入阈值" />
          </Form.Item>
          <Form.Item
            name="enabled"
            label="状态"
            initialValue={true}
          >
            <Select>
              <Option value={true}>启用</Option>
              <Option value={false}>禁用</Option>
            </Select>
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default AlertManagement;
