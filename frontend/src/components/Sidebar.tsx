import React from 'react';
import { Menu } from 'antd';
import { useNavigate, useLocation } from 'react-router-dom';
import {
  DashboardOutlined,
  FolderOutlined,
  PlusCircleOutlined,
  MonitorOutlined,
  MessageOutlined,
  SettingOutlined,
  UserOutlined
} from '@ant-design/icons';

const Sidebar: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();

  const menuItems = [
    {
      key: '/',
      icon: <DashboardOutlined />,
      label: 'Dashboard',
    },
    {
      key: '/campaigns',
      icon: <FolderOutlined />,
      label: 'Campaigns',
    },
    {
      key: '/campaigns/create',
      icon: <PlusCircleOutlined />,
      label: 'Create Campaign',
    },
    {
      key: '/monitoring',
      icon: <MonitorOutlined />,
      label: 'Monitoring',
    },
    {
      key: '/telegram',
      icon: <MessageOutlined />,
      label: 'Telegram',
    },
    {
      key: '/settings',
      icon: <SettingOutlined />,
      label: 'Settings',
    },
  ];

  const handleMenuClick = (e: any) => {
    navigate(e.key);
  };

  return (
    <div className="h-full">
      <div className="p-6 border-b">
        <h1 className="text-2xl font-bold text-gray-800">NoPhish Pro</h1>
        <p className="text-sm text-gray-600">Professional Phishing Platform</p>
      </div>
      <Menu
        mode="inline"
        selectedKeys={[location.pathname]}
        items={menuItems}
        onClick={handleMenuClick}
        theme="light"
        style={{ height: '100%', borderRight: 0 }}
      />
    </div>
  );
};

export default Sidebar;