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
  const [loading, setLoading] = useState(true); // Changed back to true to properly handle initial loading state

  // Listen for authentication state changes via storage events
  useEffect(() => {
    const handleStorageChange = (e) => {
      if (e.key === 'token') {
        if (e.newValue) {
          // Token was added, fetch permissions
          fetchPermissions();
        } else {
          // Token was removed, clear permissions
          setPermissions([]);
        }
      }
    };

    // Listen for storage changes (for token updates)
    window.addEventListener('storage', handleStorageChange);

    // Check if token exists on mount and fetch permissions if it does
    const token = localStorage.getItem('token');
    if (token) {
      fetchPermissions();
    }

    return () => {
      window.removeEventListener('storage', handleStorageChange);
    };
  }, []);

  const fetchPermissions = async () => {
    setLoading(true);
    try {
      // Check if user is authenticated by checking for token
      const token = localStorage.getItem('token');
      if (!token) {
        console.log('🔍 PermissionContext: No token found, clearing permissions');
        setPermissions([]);
        setLoading(false);
        return;
      }

      console.log('🔍 PermissionContext: Fetching permissions with token');
      const response = await axios.get(`${API}/auth/permissions`);
      console.log('✅ PermissionContext: Permissions fetched:', response.data.permissions?.length || 0);
      setPermissions(response.data.permissions || []);
    } catch (error) {
      console.error('❌ PermissionContext: Error fetching permissions:', error);
      // If 401/403, clear permissions but don't set error
      if (error.response?.status === 401 || error.response?.status === 403) {
        console.log('🔍 PermissionContext: Auth error, clearing permissions');
        setPermissions([]);
      }
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

  const canView = (path) => hasPermission(path, 'View');
  const canAdd = (path) => hasPermission(path, 'Add');
  const canEdit = (path) => hasPermission(path, 'Edit');
  const canDelete = (path) => hasPermission(path, 'Delete');
  const canExport = (path) => hasPermission(path, 'Export');

  const value = {
    permissions,
    loading,
    hasPermission,
    hasModulePermission,
    canView,
    canAdd,
    canEdit,
    canDelete,
    canExport,
    refreshPermissions: fetchPermissions // Export this function so components can trigger refresh
  };

  return (
    <PermissionContext.Provider value={value}>
      {children}
    </PermissionContext.Provider>
  );
};