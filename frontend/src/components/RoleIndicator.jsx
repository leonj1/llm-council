import { useState, useEffect } from 'react';
import { api } from '../api';
import './RoleIndicator.css';

const ROLE_CONFIG = {
  superadmin: {
    icon: '👑',
    label: 'Super Admin',
    className: 'role-superadmin',
  },
  admin: {
    icon: '🛡️',
    label: 'Admin',
    className: 'role-admin',
  },
  moderator: {
    icon: '⭐',
    label: 'Moderator',
    className: 'role-moderator',
  },
  user: {
    icon: null, // No icon for regular users (minimalist)
    label: 'User',
    className: 'role-user',
  },
};

export default function RoleIndicator() {
  const [role, setRole] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchUser = async () => {
      try {
        const user = await api.getCurrentUser();
        setRole(user.role || 'user');
      } catch (error) {
        // Not authenticated or error - don't show indicator
        setRole(null);
      } finally {
        setLoading(false);
      }
    };

    fetchUser();
  }, []);

  // Don't render anything while loading or if no role
  if (loading || !role) {
    return null;
  }

  const config = ROLE_CONFIG[role] || ROLE_CONFIG.user;

  // Don't show icon for regular users (minimalist)
  if (!config.icon) {
    return null;
  }

  return (
    <div className={`role-indicator ${config.className}`} title={config.label}>
      <span className="role-icon">{config.icon}</span>
    </div>
  );
}
