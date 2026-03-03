import React, { useState, useEffect } from 'react';
import { 
  Card, 
  Button, 
  Table, 
  Tag, 
  Space, 
  Typography, 
  Modal,
  message,
  Popconfirm
} from 'antd';
import { 
  PlusOutlined, 
  EyeOutlined, 
  EditOutlined, 
  DeleteOutlined,
  PlayCircleOutlined,
  StopOutlined
} from '@ant-design/icons';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
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

const Campaigns: React.FC = () => {
  const [campaigns, setCampaigns] = useState<Campaign[]>([]);
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  const { data, isLoading, error } = useQuery({
    queryKey: ['campaigns'],
    queryFn: async () => {
      const response = await api.get('/campaigns');
      return response.data.campaigns;
    },
  });

  useEffect(() => {
    if (data) {
      setCampaigns(data);
    }
  }, [data]);

  const deleteCampaign = useMutation({
    mutationFn: async (campaignId: number) => {
      await api.delete(`/campaigns/${campaignId}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['campaigns'] });
      message.success('Campaign deleted successfully');
    },
    onError: (error: any) => {
      message.error(error.response?.data?.detail || 'Failed to delete campaign');
    },
  });

  const startCampaign = useMutation({
    mutationFn: async (campaignId: number) => {
      await api.post(`/campaigns/${campaignId}/start`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['campaigns'] });
      message.success('Campaign started successfully');
    },
    onError: (error: any) => {
      message.error(error.response?.data?.detail || 'Failed to start campaign');
    },
  });

  const stopCampaign = useMutation({
    mutationFn: async (campaignId: number) => {
      await api.post(`/campaigns/${campaignId}/stop`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['campaigns'] });
      message.success('Campaign stopped successfully');
    },
    onError: (error: any) => {
      message.error(error.response?.data?.detail || 'Failed to stop campaign');
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

  const columns = [
    {
      title: 'Name',
      dataIndex: 'name',
      key: 'name',
      render: (text: string, record: Campaign) => (
        <Space>
          <Text strong>{text}</Text>
          <Tag color={getBrowserColor(record.browser_type)}>
            {record.browser_type}
          </Tag>
        </Space>
      ),
    },
    {
      title: 'Domain',
      dataIndex: 'domain',
      key: 'domain',
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
      title: 'Sessions',
      dataIndex: 'sessions_count',
      key: 'sessions_count',
      render: (count: number) => <Text>{count}</Text>,
    },
    {
      title: 'Created',
      dataIndex: 'created_at',
      key: 'created_at',
      render: (date: string) => (
        <Text>
          {new Date(date).toLocaleDateString()}
        </Text>
      ),
    },
    {
      title: 'Actions',
      key: 'actions',
      render: (text: any, record: Campaign) => (
        <Space>
          <Button
            type="text"
            icon={<EyeOutlined />}
            onClick={() => navigate(`/campaigns/${record.id}`)}
          />
          <Button
            type="text"
            icon={<EditOutlined />}
            onClick={() => navigate(`/campaigns/${record.id}/edit`)}
          />
          {record.status === 'created' && (
            <Button
              type="text"
              icon={<PlayCircleOutlined />}
              onClick={() => startCampaign.mutate(record.id)}
              loading={startCampaign.isPending}
            />
          )}
          {record.status === 'running' && (
            <Button
              type="text"
              icon={<StopOutlined />}
              onClick={() => stopCampaign.mutate(record.id)}
              loading={stopCampaign.isPending}
            />
          )}
          <Popconfirm
            title="Are you sure you want to delete this campaign?"
            onConfirm={() => deleteCampaign.mutate(record.id)}
            okText="Yes"
            cancelText="No"
          >
            <Button
              type="text"
              danger
              icon={<DeleteOutlined />}
              loading={deleteCampaign.isPending}
            />
          </Popconfirm>
        </Space>
      ),
    },
  ];

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading campaigns...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <Card>
        <Alert
          message="Error"
          description="Failed to load campaigns"
          type="error"
          showIcon
        />
      </Card>
    );
  }

  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <div>
          <Title level={2}>Campaigns</Title>
          <Text type="secondary">Manage your phishing campaigns</Text>
        </div>
        <Button
          type="primary"
          icon={<PlusOutlined />}
          onClick={() => navigate('/campaigns/create')}
        >
          Create Campaign
        </Button>
      </div>

      <Card>
        <Table
          columns={columns}
          dataSource={campaigns}
          rowKey="id"
          pagination={{
            pageSize: 10,
            showSizeChanger: true,
            showQuickJumper: true,
            showTotal: (total, range) => 
              `${range[0]}-${range[1]} of ${total} campaigns`,
          }}
        />
      </Card>
    </div>
  );
};

export default Campaigns;