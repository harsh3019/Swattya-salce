import React, { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import axios from 'axios';
import { Button } from './ui/button';
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from './ui/collapsible';
import { 
  Building, 
  ChevronDown, 
  ChevronRight,
  Users as UsersIcon,
  Settings,
  Activity,
  Phone,
  Target,
  TrendingUp,
  Home
} from 'lucide-react';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Icon mapping for modules and menus
const iconMap = {
  'User Management': UsersIcon,
  'Sales': Building,
  'System': Settings,
  'Users': UsersIcon,
  'Companies': Building,
  'Contacts': Phone,
  'Leads': Target,
  'Opportunities': TrendingUp,
  'Activity Logs': Activity,
  'Dashboard': Home
};

const DynamicSidebar = () => {
  const [navigation, setNavigation] = useState({ modules: [] });
  const [expandedModules, setExpandedModules] = useState({});
  const [loading, setLoading] = useState(true);
  const [userPermissions, setUserPermissions] = useState([]);
  const navigate = useNavigate();
  const location = useLocation();

  useEffect(() => {
    fetchNavigationData();
    fetchUserPermissions();
  }, []);

  const fetchNavigationData = async () => {
    try {
      console.log('🔍 DynamicSidebar: Fetching navigation data...');
      console.log('🔍 API URL:', `${API}/nav/sidebar`);
      console.log('🔍 Token:', localStorage.getItem('token') ? 'Present' : 'Missing');
      
      const response = await axios.get(`${API}/nav/sidebar`);
      
      console.log('✅ DynamicSidebar: Navigation response received:', response.data);
      console.log('✅ DynamicSidebar: Number of modules:', response.data.modules?.length || 0);
      
      setNavigation(response.data);
      
      // Auto-expand modules that contain the current path
      const currentPath = location.pathname;
      const newExpanded = {};
      
      response.data.modules.forEach(module => {
        console.log('🔍 Processing module:', module.name, 'with', module.menus?.length || 0, 'menus');
        const hasActivePath = module.menus.some(menu => 
          currentPath.startsWith(menu.path) || 
          (menu.children && menu.children.some(child => currentPath.startsWith(child.path)))
        );
        if (hasActivePath) {
          newExpanded[module.id] = true;
        }
      });
      
      setExpandedModules(newExpanded);
    } catch (error) {
      console.error('❌ DynamicSidebar: Error fetching navigation:', error);
      console.error('❌ Error response:', error.response?.data);
      console.error('❌ Error status:', error.response?.status);
    } finally {
      setLoading(false);
    }
  };

  const fetchUserPermissions = async () => {
    try {
      const response = await axios.get(`${API}/auth/permissions`);
      setUserPermissions(response.data.permissions || []);
    } catch (error) {
      console.error('Error fetching permissions:', error);
    }
  };

  const hasPermission = (menuPath, permission) => {
    return userPermissions.some(p => 
      p.path === menuPath && p.permission === permission
    );
  };

  const toggleModule = (moduleId) => {
    setExpandedModules(prev => ({
      ...prev,
      [moduleId]: !prev[moduleId]
    }));
  };

  const handleNavigation = (path, menuName) => {
    // Check if user has view permission for this menu
    if (!hasPermission(path, 'view')) {
      navigate('/403');
      return;
    }
    navigate(path);
  };

  const getIcon = (name) => {
    const Icon = iconMap[name] || Home;
    return <Icon className="w-5 h-5" />;
  };

  const renderMenu = (menu, level = 0) => {
    const isActive = location.pathname === menu.path;
    const hasViewPermission = hasPermission(menu.path, 'view');
    
    if (!hasViewPermission) return null;

    return (
      <div key={menu.id}>
        <button
          onClick={() => handleNavigation(menu.path, menu.name)}
          className={`w-full flex items-center space-x-3 px-6 py-2 text-left text-sm hover:bg-slate-800 transition-colors ${
            isActive ? 'bg-slate-800 border-r-2 border-blue-500' : ''
          }`}
          style={{ paddingLeft: `${24 + (level * 16)}px` }}
        >
          {level === 0 && getIcon(menu.name)}
          <span className={level === 0 ? '' : 'ml-6'}>{menu.name}</span>
        </button>
        
        {menu.children && menu.children.length > 0 && (
          <div>
            {menu.children.map(child => renderMenu(child, level + 1))}
          </div>
        )}
      </div>
    );
  };

  const renderModule = (module) => {
    const hasAnyVisibleMenu = module.menus.some(menu => 
      hasPermission(menu.path, 'view') || 
      (menu.children && menu.children.some(child => hasPermission(child.path, 'view')))
    );

    if (!hasAnyVisibleMenu) return null;

    const isExpanded = expandedModules[module.id];
    const ModuleIcon = iconMap[module.name] || Settings;

    return (
      <Collapsible
        key={module.id}
        open={isExpanded}
        onOpenChange={() => toggleModule(module.id)}
      >
        <CollapsibleTrigger asChild>
          <button className="w-full flex items-center justify-between px-4 py-3 text-left hover:bg-slate-800 transition-colors">
            <div className="flex items-center space-x-3">
              <ModuleIcon className="w-5 h-5" />
              <span className="font-medium">{module.name}</span>
            </div>
            {isExpanded ? (
              <ChevronDown className="w-4 h-4" />
            ) : (
              <ChevronRight className="w-4 h-4" />
            )}
          </button>
        </CollapsibleTrigger>
        <CollapsibleContent>
          <div className="bg-slate-800">
            {module.menus.map(menu => renderMenu(menu))}
          </div>
        </CollapsibleContent>
      </Collapsible>
    );
  };

  if (loading) {
    return (
      <div className="bg-slate-900 text-white w-64 min-h-screen">
        <div className="p-6">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 bg-gradient-to-br from-blue-500 to-blue-700 rounded-lg flex items-center justify-center">
              <Building className="w-6 h-6 text-white" />
            </div>
            <h1 className="text-xl font-bold">Sawayatta ERP</h1>
          </div>
        </div>
        <div className="px-6 py-4">
          <div className="animate-pulse">
            <div className="h-4 bg-slate-700 rounded mb-2"></div>
            <div className="h-4 bg-slate-700 rounded mb-2"></div>
            <div className="h-4 bg-slate-700 rounded"></div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-slate-900 text-white w-64 min-h-screen">
      <div className="p-6">
        <div className="flex items-center space-x-3">
          <div className="w-10 h-10 bg-gradient-to-br from-blue-500 to-blue-700 rounded-lg flex items-center justify-center">
            <Building className="w-6 h-6 text-white" />
          </div>
          <h1 className="text-xl font-bold">Sawayatta ERP</h1>
        </div>
      </div>
      
      {/* Dashboard Link */}
      <div className="px-4 mb-4">
        <button
          onClick={() => navigate('/dashboard')}
          className={`w-full flex items-center space-x-3 px-4 py-3 text-left hover:bg-slate-800 transition-colors rounded-lg ${
            location.pathname === '/dashboard' ? 'bg-slate-800 border-r-2 border-blue-500' : ''
          }`}
        >
          <Home className="w-5 h-5" />
          <span className="font-medium">Dashboard</span>
        </button>
      </div>

      <nav className="mt-4">
        {navigation.modules.map(module => renderModule(module))}
      </nav>
    </div>
  );
};

export default DynamicSidebar;