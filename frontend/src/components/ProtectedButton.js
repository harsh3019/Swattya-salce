import React from 'react';
import { usePermissions } from '../contexts/PermissionContext';
import { Button } from './ui/button';

const ProtectedButton = ({ 
  children, 
  path, 
  permission, 
  fallback = null,
  ...buttonProps 
}) => {
  const { hasPermission, loading } = usePermissions();

  if (loading) {
    return fallback;
  }

  if (!hasPermission(path, permission)) {
    return fallback;
  }

  return <Button {...buttonProps}>{children}</Button>;
};

export default ProtectedButton;