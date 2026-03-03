import React, { useState, useEffect } from 'react';
import { 
  Card, 
  Descriptions, 
  Tag, 
  Button, 
  Typography,
  Space,
  Alert,
  Row,
  Col,
  Table,
  Spin,
  Statistic
} from 'antd';
import { 
  ArrowLeftOutlined, 
  PlayCircleOutlined, 
  StopOutlined, 
  DeleteOutlined,
  EditOutlined,
  EyeOutlined,
  TeamOutlined,
  DesktopOutlined,
  MobileOutlined
} from '@ant-design/icons';
import { useNavigate, useParams } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import api from '../services/api';

const { Title, Text } = Typography;

interface Campaign {
  id: number;
  name: string;
  description?: string;
  domain: string;
  target_url: string;
  num_users: number;
  browser_type: string;
  ssl_enabled: boolean;
  status: string;
  created_by: string;
  created_at: string;
  updated_at: string;
  sessions_count: number;
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

interface CampaignStats {
  campaign_id: number;
  campaign_name: string;
  total_sessions: number;
  active_sessions: number;
  desktop_sessions: number;
  mobile_sessions: number;
  browser_type: string;
  domain: string;
  status: string;
}

const CampaignDetail: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  const [campaign, setCampaign] = useState<Campaign | null>(null);
  const [sessions, setSessions] = useState<CampaignSession[]>([]);
  const [stats, setStats] = useState<CampaignStats | null>(null);

  const { data: campaignData, isLoading: campaignLoading } = useQuery({
    queryKey: ['campaign', id],
    queryFn: async () => {
      const response = await api.get(`/campaigns/${id}`);
      return response.data;
    },
  });

  const { data: sessionsData, isLoading: sessionsLoading } = useQuery({
    queryKey: ['campaign-sessions', id],
    queryFn: async () => {
      const response = await api.get(`/campaigns/${id}/sessions`);
      return response.data.sessions;
    },
  });

  const { data: statsData } = useQuery({
    queryKey: ['campaign-stats', id],
    queryFn: async () => {
      const response = await api.get(`/campaigns/${id}/stats`);
      return response.data;
    },
  });

  useEffect(() => {
    if (campaignData) setCampaign(campaignData);
    if (sessionsData) setSessions(sessionsData);
    if (statsData) setStats(statsData);
  }, [campaignData, sessionsData, statsData]);

  const deleteCampaign = useMutation({
    mutationFn: async () => {
      await api.delete(`/campaigns/${id}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['campaigns'] });
      navigate('/campaigns');
    },
    onError: (error: any) => {
      console.error('Failed to delete campaign:', error);
    },
  });

  const startCampaign = useMutation({
    mutationFn: async () => {
      await api.post(`/campaigns/${id}/start`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['campaign', id] });
      queryClient.invalidateQueries({ queryKey: ['campaign-stats', id] });
    },
  });

  const stopCampaign = useMutation({
    mutationFn: async () => {
      await api.post(`/campaigns/${id}/stop`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['campaign', id] });
      queryClient.invalidateQueries({ queryKey: ['campaign-stats', id] });
    },
  });

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'running': return 'green';
      case 'created': return 'blue';
      case 'stopped': return 'red';
      case 'pending': return 'orange';
      default: return 'default';
    }
  };

  const getBrowserColor = (browser: string) => {
    switch (browser) {
      case 'chrome': return 'orange';
      case 'firefox': return 'blue';
      default: return 'default';
    }
  };

  const sessionColumns = [
    {
      title: 'Session',
      dataIndex: 'user_num',
      key: 'user_num',
      render: (num: number) => `Session ${num}`,
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
      title: 'Created',
      dataIndex: 'created_at',
      key: 'created_at',
      render: (date: string) => new Date(date).toLocaleString(),
    },
  ];

  if (campaignLoading || sessionsLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Spin size="large" />
      </div>
    );
  }

  if (!campaign) {
    return (
      <Alert
        message="Campaign Not Found"
        description="The requested campaign could not be found."
        type="error"
        showIcon
      />
    );
  }

  return (
    <div>
      <div className="mb-6">
        <Space>
          <Button
            icon={<ArrowLeftOutlined />}
            onClick={() => navigate('/campaigns')}
          >
            Back to Campaigns
          </Button>
          <Title level={2}>{campaign.name}</Title>
          <Tag color={getStatusColor(campaign.status)}>
            {campaign.status.toUpperCase()}
          </Tag>
        </Space>
      </div>

      <Row gutter={[16, 16]}>
        <Col xs={24} lg={16}>
          {/* Campaign Details */}
          <Card title="Campaign Details" className="mb-6">
            <Descriptions column={2} bordered>
              <Descriptions.Item label="Name">{campaign.name}</Descriptions.Item>
              <Descriptions.Item label="Status">
                <Tag color={getStatusColor(campaign.status)}>
                  {campaign.status.toUpperCase()}
                </Tag>
              </Descriptions.Item>
              <Descriptions.Item label="Domain">{campaign.domain}</Descriptions.Item>
              <Descriptions.Item label="Browser">
                <Tag color={getBrowserColor(campaign.browser_type)}>
                  {campaign.browser_type}
                </Tag>
              </Descriptions.Item>
              <Descriptions.Item label="Target URL">{campaign.target_url}</Descriptions.Item>
              <Descriptions.Item label="SSL Enabled">
                {campaign.ssl_enabled ? 'Yes' : 'No'}
              </Descriptions.Item>
              <Descriptions.Item label="Number of Users">{campaign.num_users}</Descriptions.Item>
              <Descriptions.Item label="Sessions">{campaign.sessions_count}</Descriptions.Item>
              <Descriptions.Item label="Created">
                {new Date(campaign.created_at).toLocaleString()}
              </Descriptions.Item>
              <Descriptions.Item label="Last Updated">
                {new Date(campaign.updated_at).toLocaleString()}
              </Descriptions.Item>
            </Descriptions>
          </Card>

          {/* Statistics */}
          {stats && (
            <Card title="Campaign Statistics">
              <Row gutter={[16, 16]}>
                <Col xs={24} sm={12}>
                  <StatisticCard
                    title="Total Sessions"
                    value={stats.total_sessions}
                    icon={<TeamOutlined />}
                  />
                </Col>
                <Col xs={24} sm={12}>
                  <StatisticCard
                    title="Active Sessions"
                    value={stats.active_sessions}
                    icon={<EyeOutlined />}
                  />
                </Col>
                <Col xs={24} sm={12}>
                  <StatisticCard
                    title="Desktop Sessions"
                    value={stats.desktop_sessions}
                    icon={<DesktopOutlined />}
                  />
                </Col>
                <Col xs={24} sm={12}>
                  <StatisticCard
                    title="Mobile Sessions"
                    value={stats.mobile_sessions}
                    icon={<MobileOutlined />}
                  />
                </Col>
              </Row>
            </Card>
          )}

          {/* Sessions */}
          <Card title="Sessions">
            <Table
              columns={sessionColumns}
              dataSource={sessions}
              rowKey="id"
              pagination={{
                pageSize: 10,
                showSizeChanger: true,
                showQuickJumper: true,
              }}
            />
          </Card>
        </Col>

        <Col xs={24} lg={8}>
          {/* Actions */}
          <Card title="Actions">
            <Space direction="vertical" className="w-full">
              <Button
                type="primary"
                icon={<EditOutlined />}
                onClick={() => navigate(`/campaigns/${id}/edit`)}
                block
              >
                Edit Campaign
              </Button>
              
              {campaign.status === 'created' && (
                <Button
                  type="primary"
                  icon={<PlayCircleOutlined />}
                  onClick={() => startCampaign.mutate()}
                  loading={startCampaign.isPending}
                  block
                >
                  Start Campaign
                </Button>
              )}
              
              {campaign.status === 'running' && (
                <Button
                  danger
                  icon={<StopOutlined />}
                  onClick={() => stopCampaign.mutate()}
                  loading={stopCampaign.isPending}
                  block
                >
                  Stop Campaign
                </Button>
              )}
              
              <Button
                danger
                icon={<DeleteOutlined />}
                onClick={() => deleteCampaign.mutate()}
                loading={deleteCampaign.isPending}
                block
              >
                Delete Campaign
              </Button>
            </Space>
          </Card>

          {/* Campaign Info */}
          <Card title="Campaign Information" className="mt-6">
            <Space direction="vertical" className="w-full">
              <div>
                <Text strong>Description:</Text>
                <br />
                <Text type="secondary">
                  {campaign.description || 'No description provided'}
                </Text>
              </div>
              
              <div>
                <Text strong>Target URL:</Text>
                <br />
                <Text type="secondary" code>
                  {campaign.target_url}
                </Text>
              </div>
              
              <div>
                <Text strong>SSL Enabled:</Text>
                <br />
                <Text type="secondary">
                  {campaign.ssl_enabled ? 'Yes' : 'No'}
                </Text>
              </div>
            </Space>
          </Card>
        </Col>
      </Row>
    </div>
  );
};

// Helper component for statistics cards
const StatisticCard: React.FC<{
  title: string;
  value: number;
  icon: React.ReactNode;
}> = ({ title, value, icon }) => (
  <Card>
    <div className="flex items-center space-x-3">
      <div className="text-blue-600">
        {icon}
      </div>
      <div>
        <div className="text-2xl font-bold">{value}</div>
        <div className="text-sm text-gray-600">{title}</div>
      </div>
    </div>
  </Card>
);

export default CampaignDetail;