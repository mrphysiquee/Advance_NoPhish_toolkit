import React from 'react';
import { Layout, Dropdown, Avatar, Badge, Button } from 'antd';
import { UserOutlined, LogoutOutlined, BellOutlined } from '@ant-design/icons';
import { useAuth } from '../contexts/AuthContext';
import { useNavigate } from 'react-router-dom';

const { Header: AntHeader } = Layout;

const Header: React.FC = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const userMenuItems = [
    {
      key: 'profile',
      icon: <UserOutlined />,
      label: 'Profile',
    },
    {
      key: 'settings',
      icon: <UserOutlined />,
      label: 'Settings',
      onClick: () => navigate('/settings'),
    },
    {
      type: 'divider',
    },
    {
      key: 'logout',
      icon: <LogoutOutlined />,
      label: 'Logout',
      onClick: logout,
    },
  ];

  return (
    <AntHeader 
      style={{ 
        background: '#fff', 
        padding: '0 24px', 
        display: 'flex', 
        alignItems: 'center', 
        justifyContent: 'space-between',
        borderBottom: '1px solid #f0f0f0'
      }}
    >
      <div className="flex items-center space-x-4">
        <h2 className="text-lg font-semibold text-gray-800">Welcome back, {user?.username}</h2>
        {user?.role_name === 'admin' && (
          <Badge 
            count="Admin" 
            style={{ backgroundColor: '#f50' }}
            className="text-xs"
          />
        )}
      </div>
      
      <div className="flex items-center space-x-4">
        <Button 
          type="text" 
          icon={<BellOutlined />} 
          size="large"
          className="text-gray-600 hover:text-gray-800"
        />
        
        <Dropdown 
          menu={{ items: userMenuItems }} 
          placement="bottomRight"
          arrow
        >
          <div className="flex items-center space-x-2 cursor-pointer">
            <Avatar 
              icon={<UserOutlined />} 
              style={{ backgroundColor: '#1890ff' }}
            />
            <span className="text-sm font-medium text-gray-700">
              {user?.username}
            </span>
          </div>
        </Dropdown>
      </div>
    </AntHeader>
  );
};

export default Header;