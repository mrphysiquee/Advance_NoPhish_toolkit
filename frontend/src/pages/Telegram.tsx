import React, { useState, useEffect } from 'react';
import { 
  Card, 
  Typography, 
  Alert, 
  Button, 
  Space, 
  Tag, 
  List,
  QRCode,
  Modal,
  Form,
  Input,
  message
} from 'antd';
import { 
  MessageOutlined, 
  QrcodeOutlined, 
  LinkOutlined,
  SettingOutlined,
  UserOutlined,
  MobileOutlined
} from '@ant-design/icons';
import { useQuery, useMutation } from '@tanstack/react-query';
import api from '../services/api';

const { Title, Text } = Typography;
const { Meta } = Card;

interface TelegramStatus {
  is_connected: boolean;
  chat_id?: string;
  username?: string;
  commands: string[];
}

const Telegram: React.FC = () => {
  const [status, setStatus] = useState<TelegramStatus | null>(null);
  const [qrModalVisible, setQrModalVisible] = useState(false);
  const [linkForm] = Form.useForm();

  const { data } = useQuery({
    queryKey: ['telegram-status'],
    queryFn: async () => {
      const response = await api.get('/telegram/status');
      return response.data;
    },
  });

  useEffect(() => {
    if (data) {
      setStatus(data);
    }
  }, [data]);

  const linkTelegram = useMutation({
    mutationFn: async (values: { chat_id: string }) => {
      await api.post('/telegram/link', { chat_id: values.chat_id });
    },
    onSuccess: () => {
      message.success('Telegram account linked successfully!');
      setQrModalVisible(false);
      // Refresh status
      api.get('/telegram/status').then(response => {
        setStatus(response.data);
      });
    },
    onError: (error: any) => {
      message.error(error.response?.data?.detail || 'Failed to link Telegram account');
    },
  });

  const handleLinkTelegram = (values: { chat_id: string }) => {
    linkTelegram.mutate(values);
  };

  const renderStatusCard = () => {
    if (!status) return null;

    if (status.is_connected && status.chat_id) {
      return (
        <Card>
          <Alert
            message="Telegram Connected"
            description={`Your Telegram account (${status.username}) is successfully linked to NoPhish Pro`}
            type="success"
            showIcon
            className="mb-4"
          />
          
          <Space direction="vertical" className="w-full">
            <div className="flex items-center space-x-2">
              <MobileOutlined />
              <Text strong>Chat ID:</Text>
              <Text code>{status.chat_id}</Text>
            </div>
            
            <div className="flex items-center space-x-2">
              <UserOutlined />
              <Text strong>Username:</Text>
              <Text>{status.username}</Text>
            </div>
          </Space>
        </Card>
      );
    } else {
      return (
        <Card>
          <Alert
            message="Telegram Not Connected"
            description="Link your Telegram account to receive notifications and control campaigns remotely"
            type="warning"
            showIcon
            className="mb-4"
          />
          
          <Space direction="vertical" className="w-full">
            <Button
              type="primary"
              icon={<QrcodeOutlined />}
              onClick={() => setQrModalVisible(true)}
              block
            >
              Link Telegram Account
            </Button>
            
            <Text type="secondary" className="text-sm">
              You'll need to use the Telegram bot to link your account
            </Text>
          </Space>
        </Card>
      );
    }
  };

  const renderCommandsList = () => (
    <Card title="Available Commands" className="mt-6">
      <List
        dataSource={[
          { command: '/start', description: 'Start bot and show help' },
          { command: '/help', description: 'Show available commands' },
          { command: '/campaigns', description: 'List all campaigns' },
          { command: '/monitor <id>', description: 'Monitor a campaign' },
          { command: '/sessions <id>', description: 'View sessions for campaign' },
          { command: '/keylogs <id>', description: 'View keylogs for campaign' },
          { command: '/stop <id>', description: 'Stop a campaign' },
          { command: '/status <id>', description: 'Get campaign status' },
          { command: '/settings', description: 'Bot settings' },
          { command: '/logout', description: 'Logout from bot' },
        ]}
        renderItem={(item) => (
          <List.Item>
            <Space>
              <Tag color="blue">{item.command}</Tag>
              <Text>{item.description}</Text>
            </Space>
          </List.Item>
        )}
      />
    </Card>
  );

  return (
    <div>
      <div className="mb-6">
        <Title level={2}>Telegram Integration</Title>
        <Text type="secondary">
          Connect Telegram for remote notifications and campaign management
        </Text>
      </div>

      {renderStatusCard()}

      <Card title="Quick Setup" className="mt-6">
        <Space direction="vertical" className="w-full">
          <div>
            <Text strong>1. Install Telegram:</Text>
            <br />
            <Text type="secondary">
              Make sure you have Telegram installed on your device
            </Text>
          </div>
          
          <div>
            <Text strong>2. Find the Bot:</Text>
            <br />
            <Text type="secondary">
              Search for @NoPhishProBot in Telegram or click the link below
            </Text>
          </div>
          
          <Button
            type="primary"
            icon={<MessageOutlined />}
            href="https://t.me/NoPhishProBot"
            target="_blank"
            block
          >
            Open Bot in Telegram
          </Button>
        </Space>
      </Card>

      {renderCommandsList()}

      {/* QR Code Modal */}
      <Modal
        title="Link Telegram Account"
        open={qrModalVisible}
        onCancel={() => setQrModalVisible(false)}
        footer={null}
        width={500}
      >
        <div className="text-center">
          <Alert
            message="How to Link Your Account"
            description="1. Click the button below to open Telegram in your browser<br/>2. Send /start to the bot<br/>3. Click the 'Link Account' button<br/>4. Enter your Chat ID below"
            type="info"
            showIcon
            className="mb-4"
          />
          
          <Button
            type="primary"
            icon={<MessageOutlined />}
            onClick={() => window.open('https://t.me/NoPhishProBot', '_blank')}
            block
            className="mb-4"
          >
            Open Bot in Telegram
          </Button>
          
          <Form
            form={linkForm}
            onFinish={handleLinkTelegram}
            layout="vertical"
          >
            <Form.Item
              name="chat_id"
              label="Your Chat ID"
              rules={[
                { required: true, message: 'Please enter your Chat ID!' },
                { pattern: /^\d+$/, message: 'Chat ID must be a number!' },
              ]}
            >
              <Input 
                placeholder="123456789" 
                prefix={<UserOutlined />}
              />
            </Form.Item>
            
            <Form.Item>
              <Space>
                <Button
                  type="primary"
                  htmlType="submit"
                  loading={linkTelegram.isPending}
                >
                  Link Account
                </Button>
                <Button
                  onClick={() => setQrModalVisible(false)}
                >
                  Cancel
                </Button>
              </Space>
            </Form.Item>
          </Form>
        </div>
      </Modal>
    </div>
  );
};

export default Telegram;