import React, { useState, useEffect } from 'react';
import { 
  Card, 
  Row, 
  Col, 
  Statistic, 
  Typography, 
  List, 
  Tag, 
  Space, 
  Spin,
  Alert
} from 'antd';
import { 
  TrophyOutlined, 
  TeamOutlined, 
  EyeOutlined, 
  PlayCircleOutlined,
  ClockCircleOutlined,
  FolderOutlined
} from '@ant-design/icons';
import { useQuery } from '@tanstack/react-query';
import api from '../services/api';

const { Title, Text } = Typography;

interface DashboardStats {
  total_campaigns: number;
  total_users?: number;
  total_sessions: number;
  active_campaigns: number;
  active_sessions: number;
  recent_campaigns: Array<{
    id: number;
    name: string;
    status: string;
    created_at: string;
  }>;
  recent_users?: Array<{
    id: number;
    username: string;
    created_at: string;
  }>;
}

const Dashboard: React.FC = () => {
  const [stats, setStats] = useState<DashboardStats | null>(null);

  const { data: dashboardData, isLoading, error } = useQuery({
    queryKey: ['dashboard-stats'],
    queryFn: async () => {
      const response = await api.get('/dashboard/stats');
      return response.data;
    },
    staleTime: 5 * 60 * 1000, // 5 minutes
  });

  useEffect(() => {
    if (dashboardData) {
      setStats(dashboardData);
    }
  }, [dashboardData]);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Spin size="large" />
      </div>
    );
  }

  if (error) {
    return (
      <Alert
        message="Error"
        description="Failed to load dashboard data"
        type="error"
        showIcon
      />
    );
  }

  if (!stats) {
    return null;
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'running': return 'green';
      case 'created': return 'blue';
      case 'stopped': return 'red';
      case 'pending': return 'orange';
      default: return 'default';
    }
  };

  return (
    <div>
      <div className="mb-6">
        <Title level={2}>Dashboard</Title>
        <Text type="secondary">
          Overview of your NoPhish Professional platform
        </Text>
      </div>

      {/* Statistics Cards */}
      <Row gutter={[16, 16]} className="mb-6">
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="Total Campaigns"
              value={stats.total_campaigns}
              prefix={<FolderOutlined />}
              valueStyle={{ color: '#1890ff' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="Active Campaigns"
              value={stats.active_campaigns}
              prefix={<PlayCircleOutlined />}
              valueStyle={{ color: '#52c41a' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="Total Sessions"
              value={stats.total_sessions}
              prefix={<EyeOutlined />}
              valueStyle={{ color: '#722ed1' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="Active Sessions"
              value={stats.active_sessions}
              prefix={<TeamOutlined />}
              valueStyle={{ color: '#fa8c16' }}
            />
          </Card>
        </Col>
      </Row>

      {/* Recent Campaigns */}
      <Row gutter={[16, 16]}>
        <Col xs={24} lg={16}>
          <Card 
            title={
              <Space>
                <ClockCircleOutlined />
                Recent Campaigns
              </Space>
            }
            extra={
              <a href="/campaigns">View All</a>
            }
          >
            <List
              dataSource={stats.recent_campaigns}
              renderItem={(item) => (
                <List.Item>
                  <List.Item.Meta
                    title={
                      <Space>
                        {item.name}
                        <Tag color={getStatusColor(item.status)}>
                          {item.status}
                        </Tag>
                      </Space>
                    }
                    description={
                      new Date(item.created_at).toLocaleDateString() + 
                      ' ' + 
                      new Date(item.created_at).toLocaleTimeString()
                    }
                  />
                  <div>
                    <a href={`/campaigns/${item.id}`}>View Details</a>
                  </div>
                </List.Item>
              )}
            />
          </Card>
        </Col>
        
        <Col xs={24} lg={8}>
          <Card 
            title={
              <Space>
                <TrophyOutlined />
                Quick Actions
              </Space>
            }
          >
            <List
              dataSource={[
                { title: 'Create New Campaign', action: '/campaigns/create' },
                { title: 'View All Campaigns', action: '/campaigns' },
                { title: 'Monitor Sessions', action: '/monitoring' },
                { title: 'Telegram Settings', action: '/telegram' },
              ]}
              renderItem={(item) => (
                <List.Item>
                  <a href={item.action}>{item.title}</a>
                </List.Item>
              )}
            />
          </Card>
        </Col>
      </Row>
    </div>
  );
};

export default Dashboard;