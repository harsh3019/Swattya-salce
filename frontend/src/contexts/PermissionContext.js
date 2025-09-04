import React, { createContext, useContext, useState, useEffect } from 'react';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const PermissionContext = createContext();

export const usePermissions = () => {
  const context = useContext(PermissionContext);
  if (!context) {
    throw new Error('usePermissions must be used within a PermissionProvider');
  }
  return context;
};

export const PermissionProvider = ({ children }) => {
  const [permissions, setPermissions] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchPermissions();
  }, []);

  const fetchPermissions = async () => {
    try {
      const response = await axios.get(`${API}/auth/permissions`);
      setPermissions(response.data.permissions || []);
    } catch (error) {
      console.error('Error fetching permissions:', error);
      setPermissions([]);
    } finally {
      setLoading(false);
    }
  };

  const hasPermission = (menuPath, permission) => {
    return permissions.some(p => 
      p.path === menuPath && p.permission === permission
    );
  };

  const hasModulePermission = (moduleName, permission) => {
    return permissions.some(p => 
      p.module === moduleName && p.permission === permission
    );
  };

  const canView = (path) => hasPermission(path, 'view');
  const canAdd = (path) => hasPermission(path, 'add');
  const canEdit = (path) => hasPermission(path, 'edit');
  const canDelete = (path) => hasPermission(path, 'delete');

  const value = {
    permissions,
    loading,
    hasPermission,
    hasModulePermission,
    canView,
    canAdd,
    canEdit,
    canDelete,
    refreshPermissions: fetchPermissions
  };

  return (
    <PermissionContext.Provider value={value}>
      {children}
    </PermissionContext.Provider>
  );
};