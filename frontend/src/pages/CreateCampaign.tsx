import React, { useState } from 'react';
import { 
  Form, 
  Input, 
  InputNumber, 
  Select, 
  Switch, 
  Button, 
  Card, 
  Typography,
  Space,
  Alert,
  Row,
  Col
} from 'antd';
import { useNavigate } from 'react-router-dom';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import api from '../services/api';

const { Title, Text } = Typography;
const { Option } = Select;

interface CampaignFormData {
  name: string;
  description?: string;
  domain: string;
  target_url: string;
  num_users: number;
  browser_type: string;
  ssl_enabled: boolean;
}

const CreateCampaign: React.FC = () => {
  const [form] = Form.useForm<CampaignFormData>();
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  const createCampaign = useMutation({
    mutationFn: async (campaignData: CampaignFormData) => {
      const response = await api.post('/campaigns', campaignData);
      return response.data;
    },
    onSuccess: (data) => {
      setSuccess('Campaign created successfully!');
      setError(null);
      form.resetFields();
      queryClient.invalidateQueries({ queryKey: ['campaigns'] });
      
      setTimeout(() => {
        navigate(`/campaigns/${data.id}`);
      }, 2000);
    },
    onError: (error: any) => {
      setError(error.response?.data?.detail || 'Failed to create campaign');
      setSuccess(null);
    },
  });

  const onFinish = (values: CampaignFormData) => {
    createCampaign.mutate(values);
  };

  return (
    <div>
      <div className="mb-6">
        <Title level={2}>Create New Campaign</Title>
        <Text type="secondary">Set up a new phishing campaign</Text>
      </div>

      <Row gutter={[24, 0]}>
        <Col xs={24} lg={16}>
          <Card title="Campaign Details">
            {error && (
              <Alert
                message="Error"
                description={error}
                type="error"
                showIcon
                className="mb-4"
              />
            )}
            
            {success && (
              <Alert
                message="Success"
                description={success}
                type="success"
                showIcon
                className="mb-4"
              />
            )}

            <Form
              form={form}
              layout="vertical"
              onFinish={onFinish}
              initialValues={{
                num_users: 1,
                browser_type: 'firefox',
                ssl_enabled: false,
              }}
            >
              <Row gutter={[16, 0]}>
                <Col xs={24} md={12}>
                  <Form.Item
                    name="name"
                    label="Campaign Name"
                    rules={[
                      { required: true, message: 'Please enter campaign name!' },
                      { min: 2, message: 'Campaign name must be at least 2 characters!' },
                    ]}
                  >
                    <Input placeholder="Enter campaign name" />
                  </Form.Item>
                </Col>
                
                <Col xs={24} md={12}>
                  <Form.Item
                    name="browser_type"
                    label="Browser Type"
                    rules={[{ required: true, message: 'Please select browser type!' }]}
                  >
                    <Select placeholder="Select browser type">
                      <Option value="firefox">Firefox</Option>
                      <Option value="chrome">Chrome</Option>
                    </Select>
                  </Form.Item>
                </Col>
              </Row>

              <Form.Item
                name="description"
                label="Description (Optional)"
              >
                <Input.TextArea 
                  rows={3} 
                  placeholder="Enter campaign description (optional)" 
                />
              </Form.Item>

              <Row gutter={[16, 0]}>
                <Col xs={24} md={12}>
                  <Form.Item
                    name="domain"
                    label="Phishing Domain"
                    rules={[
                      { required: true, message: 'Please enter phishing domain!' },
                    ]}
                  >
                    <Input placeholder="example.com" />
                  </Form.Item>
                </Col>
                
                <Col xs={24} md={12}>
                  <Form.Item
                    name="num_users"
                    label="Number of Users"
                    rules={[
                      { required: true, message: 'Please enter number of users!' },
                    ]}
                  >
                    <InputNumber 
                      min={1} 
                      max={100} 
                      style={{ width: '100%' }}
                      placeholder="1"
                    />
                  </Form.Item>
                </Col>
              </Row>

              <Form.Item
                name="target_url"
                label="Target URL"
                rules={[
                  { required: true, message: 'Please enter target URL!' },
                ]}
              >
                <Input placeholder="https://example.com/login" />
              </Form.Item>

              <Form.Item
                name="ssl_enabled"
                label="Enable SSL (HTTPS)"
                valuePropName="checked"
              >
                <Switch />
              </Form.Item>

              <Form.Item>
                <Space>
                  <Button
                    type="primary"
                    htmlType="submit"
                    loading={createCampaign.isPending}
                    size="large"
                  >
                    Create Campaign
                  </Button>
                  <Button
                    onClick={() => navigate('/campaigns')}
                    size="large"
                  >
                    Cancel
                  </Button>
                </Space>
              </Form.Item>
            </Form>
          </Card>
        </Col>
        
        <Col xs={24} lg={8}>
          <Card title="Campaign Tips">
            <Space direction="vertical" size="middle" className="w-full">
              <div>
                <Text strong>Domain Selection:</Text>
                <br />
                <Text type="secondary">
                  Use a domain that resembles your target but is clearly fake.
                </Text>
              </div>
              
              <div>
                <Text strong>Browser Type:</Text>
                <br />
                <Text type="secondary">
                  Choose the browser your targets primarily use.
                </Text>
              </div>
              
              <div>
                <Text strong>SSL Certificate:</Text>
                <br />
                <Text type="secondary">
                  Enable SSL for more realistic phishing pages.
                </Text>
              </div>
            </Space>
          </Card>
        </Col>
      </Row>
    </div>
  );
};

export default CreateCampaign;