import React, { useState, useEffect } from 'react';
import { 
  Card, 
  Form, 
  Input, 
  Button, 
  Typography, 
  Space, 
  Divider,
  Alert,
  Row,
  Col,
  Switch,
  Select,
  message
} from 'antd';
import { 
  UserOutlined, 
  LockOutlined, 
  MailOutlined,
  SaveOutlined,
  ReloadOutlined,
  SettingOutlined
} from '@ant-design/icons';
import { useQuery, useMutation } from '@tanstack/react-query';
import api from '../services/api';

const { Title, Text } = Typography;
const { Option } = Select;

interface User {
  id: number;
  username: string;
  email: string;
  full_name?: string;
  role_name: string;
  is_active: boolean;
  created_at: string;
  telegram_chat_id?: string;
}

interface SettingsData {
  notifications: {
    email: boolean;
    telegram: boolean;
  };
  security: {
    two_factor: boolean;
    session_timeout: number;
  };
  appearance: {
    theme: string;
    language: string;
  };
}

const Settings: React.FC = () => {
  const [form] = Form.useForm();
  const [securityForm] = Form.useForm();
  const [notificationsForm] = Form.useForm();
  const [appearanceForm] = Form.useForm();
  
  const [user, setUser] = useState<User | null>(null);
  const [settings, setSettings] = useState<SettingsData | null>(null);
  const [loading, setLoading] = useState(false);

  const { data: userData } = useQuery({
    queryKey: ['user-profile'],
    queryFn: async () => {
      const response = await api.get('/auth/me');
      return response.data;
    },
  });

  const { data: settingsData } = useQuery({
    queryKey: ['settings'],
    queryFn: async () => {
      const response = await api.get('/settings');
      return response.data;
    },
  });

  useEffect(() => {
    if (userData) {
      setUser(userData);
      form.setFieldsValue({
        username: userData.username,
        email: userData.email,
        full_name: userData.full_name,
      });
    }
    
    if (settingsData) {
      setSettings(settingsData);
      notificationsForm.setFieldsValue(settingsData.notifications);
      securityForm.setFieldsValue(settingsData.security);
      appearanceForm.setFieldsValue(settingsData.appearance);
    }
  }, [userData, settingsData]);

  const updateProfile = useMutation({
    mutationFn: async (values: any) => {
      await api.put('/users/profile', values);
    },
    onSuccess: () => {
      message.success('Profile updated successfully');
      api.get('/auth/me').then(response => {
        setUser(response.data);
        form.setFieldsValue({
          username: response.data.username,
          email: response.data.email,
          full_name: response.data.full_name,
        });
      });
    },
    onError: (error: any) => {
      message.error(error.response?.data?.detail || 'Failed to update profile');
    },
  });

  const updatePassword = useMutation({
    mutationFn: async (values: any) => {
      await api.put('/users/password', values);
    },
    onSuccess: () => {
      message.success('Password updated successfully');
      securityForm.resetFields();
    },
    onError: (error: any) => {
      message.error(error.response?.data?.detail || 'Failed to update password');
    },
  });

  const updateSettings = useMutation({
    mutationFn: async (values: SettingsData) => {
      await api.put('/settings', values);
    },
    onSuccess: () => {
      message.success('Settings updated successfully');
      setSettings(values);
    },
    onError: (error: any) => {
      message.error(error.response?.data?.detail || 'Failed to update settings');
    },
  });

  const handleProfileUpdate = (values: any) => {
    updateProfile.mutate(values);
  };

  const handlePasswordUpdate = (values: any) => {
    updatePassword.mutate(values);
  };

  const handleSettingsUpdate = (values: SettingsData) => {
    updateSettings.mutate(values);
  };

  return (
    <div>
      <div className="mb-6">
        <Title level={2}>Settings</Title>
        <Text type="secondary">
          Manage your account and system preferences
        </Text>
      </div>

      <Row gutter={[24, 24]}>
        <Col xs={24} lg={16}>
          {/* Profile Settings */}
          <Card 
            title={
              <Space>
                <UserOutlined />
                Profile Information
              </Space>
            }
            className="mb-6"
          >
            <Form
              form={form}
              layout="vertical"
              onFinish={handleProfileUpdate}
            >
              <Row gutter={[16, 0]}>
                <Col xs={24} md={12}>
                  <Form.Item
                    name="username"
                    label="Username"
                    rules={[
                      { required: true, message: 'Please enter username!' },
                      { min: 3, message: 'Username must be at least 3 characters!' },
                    ]}
                  >
                    <Input prefix={<UserOutlined />} />
                  </Form.Item>
                </Col>
                
                <Col xs={24} md={12}>
                  <Form.Item
                    name="email"
                    label="Email"
                    rules={[
                      { required: true, message: 'Please enter email!' },
                      { type: 'email', message: 'Please enter a valid email!' },
                    ]}
                  >
                    <Input prefix={<MailOutlined />} />
                  </Form.Item>
                </Col>
              </Row>

              <Form.Item
                name="full_name"
                label="Full Name"
              >
                <Input />
              </Form.Item>

              <Form.Item>
                <Space>
                  <Button
                    type="primary"
                    htmlType="submit"
                    icon={<SaveOutlined />}
                    loading={updateProfile.isPending}
                  >
                    Save Changes
                  </Button>
                  <Button
                    icon={<ReloadOutlined />}
                    onClick={() => form.resetFields()}
                  >
                    Reset
                  </Button>
                </Space>
              </Form.Item>
            </Form>
          </Card>

          {/* Password Settings */}
          <Card 
            title={
              <Space>
                <LockOutlined />
                Change Password
              </Space>
            }
            className="mb-6"
          >
            <Form
              form={securityForm}
              layout="vertical"
              onFinish={handlePasswordUpdate}
            >
              <Form.Item
                name="current_password"
                label="Current Password"
                rules={[
                  { required: true, message: 'Please enter current password!' },
                ]}
              >
                <Input.Password prefix={<LockOutlined />} />
              </Form.Item>

              <Form.Item
                name="new_password"
                label="New Password"
                rules={[
                  { required: true, message: 'Please enter new password!' },
                  { min: 6, message: 'Password must be at least 6 characters!' },
                ]}
              >
                <Input.Password prefix={<LockOutlined />} />
              </Form.Item>

              <Form.Item
                name="confirm_password"
                label="Confirm New Password"
                dependencies={['new_password']}
                rules={[
                  { required: true, message: 'Please confirm your password!' },
                  ({ getFieldValue }) => ({
                    validator(_, value) {
                      if (!value || getFieldValue('new_password') === value) {
                        return Promise.resolve();
                      }
                      return Promise.reject(new Error('Passwords do not match!'));
                    },
                  }),
                ]}
              >
                <Input.Password prefix={<LockOutlined />} />
              </Form.Item>

              <Form.Item>
                <Button
                  type="primary"
                  htmlType="submit"
                  icon={<SaveOutlined />}
                  loading={updatePassword.isPending}
                >
                  Update Password
                </Button>
              </Form.Item>
            </Form>
          </Card>
        </Col>

        <Col xs={24} lg={8}>
          {/* Account Info */}
          <Card title="Account Information" className="mb-6">
            <Space direction="vertical" className="w-full">
              <div>
                <Text strong>Username:</Text>
                <br />
                <Text>{user?.username}</Text>
              </div>
              
              <div>
                <Text strong>Email:</Text>
                <br />
                <Text>{user?.email}</Text>
              </div>
              
              <div>
                <Text strong>Role:</Text>
                <br />
                <Tag color={user?.role_name === 'admin' ? 'red' : 'blue'}>
                  {user?.role_name}
                </Tag>
              </div>
              
              <div>
                <Text strong>Account Status:</Text>
                <br />
                <Tag color={user?.is_active ? 'green' : 'red'}>
                  {user?.is_active ? 'Active' : 'Inactive'}
                </Tag>
              </div>
              
              <div>
                <Text strong>Member Since:</Text>
                <br />
                <Text>{user?.created_at && new Date(user.created_at).toLocaleDateString()}</Text>
              </div>
              
              {user?.telegram_chat_id && (
                <div>
                  <Text strong>Telegram:</Text>
                  <br />
                  <Tag color="green">Linked</Tag>
                </div>
              )}
            </Space>
          </Card>

          {/* Quick Actions */}
          <Card title="Quick Actions">
            <Space direction="vertical" className="w-full">
              <Button
                type="primary"
                icon={<SettingOutlined />}
                block
                onClick={() => window.location.reload()}
              >
                Refresh Settings
              </Button>
              
              <Button
                icon={<ReloadOutlined />}
                block
                onClick={() => {
                  form.resetFields();
                  securityForm.resetFields();
                  notificationsForm.resetFields();
                  appearanceForm.resetFields();
                }}
              >
                Reset All Forms
              </Button>
            </Space>
          </Card>
        </Col>
      </Row>

      <Divider />

      {/* Advanced Settings */}
      <Row gutter={[24, 24]}>
        <Col xs={24} lg={12}>
          <Card title="Notification Settings">
            <Form
              form={notificationsForm}
              layout="vertical"
              onFinish={handleSettingsUpdate}
            >
              <Form.Item
                name="notifications.email"
                label="Email Notifications"
                valuePropName="checked"
              >
                <Switch />
              </Form.Item>

              <Form.Item
                name="notifications.telegram"
                label="Telegram Notifications"
                valuePropName="checked"
              >
                <Switch />
              </Form.Item>

              <Form.Item>
                <Button
                  type="primary"
                  htmlType="submit"
                  icon={<SaveOutlined />}
                  loading={updateSettings.isPending}
                >
                  Save Notifications
                </Button>
              </Form.Item>
            </Form>
          </Card>
        </Col>

        <Col xs={24} lg={12}>
          <Card title="Appearance Settings">
            <Form
              form={appearanceForm}
              layout="vertical"
              onFinish={handleSettingsUpdate}
            >
              <Form.Item
                name="appearance.theme"
                label="Theme"
                rules={[{ required: true, message: 'Please select a theme!' }]}
              >
                <Select>
                  <Option value="light">Light</Option>
                  <Option value="dark">Dark</Option>
                  <Option value="auto">Auto</Option>
                </Select>
              </Form.Item>

              <Form.Item
                name="appearance.language"
                label="Language"
                rules={[{ required: true, message: 'Please select a language!' }]}
              >
                <Select>
                  <Option value="en">English</Option>
                  <Option value="es">Spanish</Option>
                  <Option value="fr">French</Option>
                  <Option value="de">German</Option>
                </Select>
              </Form.Item>

              <Form.Item>
                <Button
                  type="primary"
                  htmlType="submit"
                  icon={<SaveOutlined />}
                  loading={updateSettings.isPending}
                >
                  Save Appearance
                </Button>
              </Form.Item>
            </Form>
          </Card>
        </Col>
      </Row>
    </div>
  );
};

export default Settings;