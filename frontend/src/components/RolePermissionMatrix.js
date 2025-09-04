import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Button } from './ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Checkbox } from './ui/checkbox';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/tabs';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from './ui/dialog';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './ui/select';
import { Badge } from './ui/badge';
import { Alert, AlertDescription } from './ui/alert';
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from './ui/collapsible';
import { 
  Plus, 
  ChevronDown, 
  ChevronRight, 
  Save, 
  RefreshCw,
  AlertCircle,
  Info
} from 'lucide-react';
import { toast } from 'sonner';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const RolePermissionMatrix = () => {
  const [roles, setRoles] = useState([]);
  const [activeRole, setActiveRole] = useState(null);
  const [matrix, setMatrix] = useState([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [expandedModules, setExpandedModules] = useState({});
  const [pendingChanges, setPendingChanges] = useState([]);
  
  // Add Module modal state
  const [isAddModuleOpen, setIsAddModuleOpen] = useState(false);
  const [unassignedModules, setUnassignedModules] = useState([]);
  const [selectedModule, setSelectedModule] = useState(null);
  const [moduleMenus, setModuleMenus] = useState([]);

  const permissions = ['View', 'Add', 'Edit', 'Delete', 'Export'];
  
  useEffect(() => {
    fetchRoles();
  }, []);

  useEffect(() => {
    if (activeRole) {
      fetchMatrix();
    }
  }, [activeRole]);

  const fetchRoles = async () => {
    try {
      const response = await axios.get(`${API}/roles`);
      setRoles(response.data);
      if (response.data.length > 0 && !activeRole) {
        setActiveRole(response.data[0].id);
      }
    } catch (error) {
      console.error('Error fetching roles:', error);
      toast.error('Failed to fetch roles');
    }
  };

  const fetchMatrix = async () => {
    if (!activeRole) return;
    
    try {
      setLoading(true);
      const response = await axios.get(`${API}/role-permissions/matrix/${activeRole}`);
      setMatrix(response.data.matrix || []);
      
      // Auto-expand first module
      if (response.data.matrix && response.data.matrix.length > 0) {
        setExpandedModules({ [response.data.matrix[0].module.id]: true });
      }
    } catch (error) {
      console.error('Error fetching matrix:', error);
      toast.error('Failed to fetch permission matrix');
    } finally {
      setLoading(false);
    }
  };

  const handlePermissionChange = (moduleId, menuId, permissionName, permissionId, granted) => {
    // Update matrix state
    setMatrix(prev => prev.map(module => {
      if (module.module.id === moduleId) {
        return {
          ...module,
          menus: module.menus.map(menu => {
            if (menu.id === menuId) {
              return {
                ...menu,
                permissions: {
                  ...menu.permissions,
                  [permissionName]: {
                    ...menu.permissions[permissionName],
                    granted: granted
                  }
                }
              };
            }
            return menu;
          })
        };
      }
      return module;
    }));

    // Track pending changes
    const changeKey = `${moduleId}-${menuId}-${permissionId}`;
    setPendingChanges(prev => {
      const filtered = prev.filter(change => 
        !(change.module_id === moduleId && change.menu_id === menuId && change.permission_id === permissionId)
      );
      
      return [...filtered, {
        module_id: moduleId,
        menu_id: menuId,
        permission_id: permissionId,
        granted: granted
      }];
    });
  };

  const handleToggleAllColumn = (permissionName) => {
    const allChecked = matrix.every(module => 
      module.menus.every(menu => menu.permissions[permissionName]?.granted)
    );
    
    matrix.forEach(module => {
      module.menus.forEach(menu => {
        if (menu.permissions[permissionName]) {
          handlePermissionChange(
            module.module.id,
            menu.id,
            permissionName,
            menu.permissions[permissionName].permission_id,
            !allChecked
          );
        }
      });
    });
  };

  const handleToggleAllRow = (moduleId, menuId) => {
    const module = matrix.find(m => m.module.id === moduleId);
    const menu = module?.menus.find(m => m.id === menuId);
    
    if (!menu) return;
    
    const allChecked = permissions.every(perm => menu.permissions[perm]?.granted);
    
    permissions.forEach(permissionName => {
      if (menu.permissions[permissionName]) {
        handlePermissionChange(
          moduleId,
          menuId,
          permissionName,
          menu.permissions[permissionName].permission_id,
          !allChecked
        );
      }
    });
  };

  const saveChanges = async () => {
    if (pendingChanges.length === 0) {
      toast.info('No changes to save');
      return;
    }

    try {
      setSaving(true);
      await axios.post(`${API}/role-permissions/matrix/${activeRole}`, {
        updates: pendingChanges
      });
      
      setPendingChanges([]);
      toast.success('Permissions saved successfully');
    } catch (error) {
      console.error('Error saving permissions:', error);
      toast.error('Failed to save permissions');
    } finally {
      setSaving(false);
    }
  };

  const toggleModule = (moduleId) => {
    setExpandedModules(prev => ({
      ...prev,
      [moduleId]: !prev[moduleId]
    }));
  };

  const fetchUnassignedModules = async () => {
    if (!activeRole) return;
    
    try {
      const response = await axios.get(`${API}/role-permissions/unassigned-modules/${activeRole}`);
      setUnassignedModules(response.data.modules || []);
    } catch (error) {
      console.error('Error fetching unassigned modules:', error);
      toast.error('Failed to fetch unassigned modules');
    }
  };

  const handleAddModule = async () => {
    fetchUnassignedModules();
    setIsAddModuleOpen(true);
    setSelectedModule(null);
    setModuleMenus([]);
  };

  const handleModuleSelect = async (moduleId) => {
    try {
      const response = await axios.get(`${API}/menus`);
      const allMenus = response.data;
      const moduleMenus = allMenus.filter(menu => menu.module_id === moduleId);
      setModuleMenus(moduleMenus);
      setSelectedModule(moduleId);
    } catch (error) {
      console.error('Error fetching module menus:', error);
      toast.error('Failed to fetch module menus');
    }
  };

  const handleSaveAddModule = async () => {
    if (!selectedModule || !activeRole) return;

    try {
      const permissions = [];
      
      // Add all menus with no permissions by default (user will configure after)
      moduleMenus.forEach(menu => {
        permissions.push({
          menu_id: menu.id,
          permission_ids: [] // Start with no permissions
        });
      });

      await axios.post(`${API}/role-permissions/add-module`, {
        role_id: activeRole,
        module_id: selectedModule,
        permissions: permissions
      });

      toast.success('Module added successfully');
      setIsAddModuleOpen(false);
      fetchMatrix(); // Refresh matrix
    } catch (error) {
      console.error('Error adding module:', error);
      toast.error('Failed to add module');
    }
  };

  const getActiveRoleName = () => {
    const role = roles.find(r => r.id === activeRole);
    return role ? role.name : '';
  };

  if (loading) {
    return (
      <div className="p-6">
        <div className="flex items-center justify-center py-12">
          <RefreshCw className="w-6 h-6 animate-spin mr-2" />
          <span>Loading permission matrix...</span>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6">
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="text-2xl font-bold">Role Permission Matrix</CardTitle>
              <CardDescription>
                Manage permissions for each role. Configure which modules and actions each role can access.
              </CardDescription>
            </div>
            <div className="flex items-center space-x-2">
              <Button onClick={handleAddModule} variant="outline">
                <Plus className="w-4 h-4 mr-2" />
                Add Module
              </Button>
              <Button 
                onClick={saveChanges} 
                disabled={saving || pendingChanges.length === 0}
                className="bg-blue-600 hover:bg-blue-700"
              >
                {saving ? (
                  <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
                ) : (
                  <Save className="w-4 h-4 mr-2" />
                )}
                Save Changes
                {pendingChanges.length > 0 && (
                  <Badge variant="secondary" className="ml-2">
                    {pendingChanges.length}
                  </Badge>
                )}
              </Button>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          {/* Role Tabs */}
          <Tabs value={activeRole} onValueChange={setActiveRole} className="space-y-6">
            <TabsList className="grid w-full grid-cols-auto">
              {roles.map((role) => (
                <TabsTrigger 
                  key={role.id} 
                  value={role.id}
                  className="flex items-center space-x-2"
                >
                  {role.name}
                  {role.code && (
                    <Badge variant="outline" className="ml-1 text-xs">
                      {role.code}
                    </Badge>
                  )}
                </TabsTrigger>
              ))}
            </TabsList>

            <TabsContent value={activeRole} className="space-y-4">
              {pendingChanges.length > 0 && (
                <Alert className="border-yellow-200 bg-yellow-50">
                  <Info className="h-4 w-4 text-yellow-600" />
                  <AlertDescription className="text-yellow-800">
                    You have {pendingChanges.length} unsaved changes. Click "Save Changes" to apply them.
                  </AlertDescription>
                </Alert>
              )}

              {/* Permission Matrix */}
              <div className="border rounded-lg overflow-hidden">
                <div className="bg-slate-50 border-b">
                  <div className="grid grid-cols-12 gap-4 p-4 font-medium text-sm">
                    <div className="col-span-4">Module / Menu</div>
                    {permissions.map(perm => (
                      <div key={perm} className="col-span-1 text-center">
                        <div className="flex flex-col items-center space-y-1">
                          <span>{perm}</span>
                          <Checkbox 
                            checked={matrix.every(module => 
                              module.menus.every(menu => menu.permissions[perm]?.granted)
                            )}
                            onCheckedChange={() => handleToggleAllColumn(perm)}
                            className="h-3 w-3"
                          />
                        </div>
                      </div>
                    ))}
                    <div className="col-span-1 text-center">All</div>
                  </div>
                </div>

                <div className="divide-y">
                  {matrix.map((module) => (
                    <div key={module.module.id}>
                      {/* Module Header */}
                      <Collapsible
                        open={expandedModules[module.module.id]}
                        onOpenChange={() => toggleModule(module.module.id)}
                      >
                        <CollapsibleTrigger asChild>
                          <div className="grid grid-cols-12 gap-4 p-4 hover:bg-slate-50 cursor-pointer">
                            <div className="col-span-4 flex items-center space-x-2 font-medium">
                              {expandedModules[module.module.id] ? (
                                <ChevronDown className="w-4 h-4" />
                              ) : (
                                <ChevronRight className="w-4 h-4" />
                              )}
                              <span>{module.module.name}</span>
                              <Badge variant="outline" className="text-xs">
                                {module.menus.length} menus
                              </Badge>
                            </div>
                            <div className="col-span-8"></div>
                          </div>
                        </CollapsibleTrigger>
                        
                        <CollapsibleContent>
                          {/* Menu Rows */}
                          {module.menus.map((menu) => (
                            <div key={menu.id} className="grid grid-cols-12 gap-4 p-4 pl-12 bg-white border-t">
                              <div className="col-span-4">
                                <div className="flex items-center space-x-2">
                                  <span className="font-medium">{menu.name}</span>
                                  <Badge variant="secondary" className="text-xs">
                                    {menu.path}
                                  </Badge>
                                </div>
                              </div>
                              
                              {permissions.map(permissionName => (
                                <div key={permissionName} className="col-span-1 flex justify-center">
                                  {menu.permissions[permissionName] ? (
                                    <div className="group relative">
                                      <Checkbox
                                        checked={menu.permissions[permissionName].granted}
                                        onCheckedChange={(checked) => 
                                          handlePermissionChange(
                                            module.module.id,
                                            menu.id,
                                            permissionName,
                                            menu.permissions[permissionName].permission_id,
                                            checked
                                          )
                                        }
                                      />
                                      {/* Tooltip */}
                                      <div className="absolute bottom-full left-1/2 transform -translate-x-1/2 mb-2 hidden group-hover:block z-10">
                                        <div className="bg-gray-900 text-white text-xs rounded py-1 px-2 whitespace-nowrap">
                                          {menu.permissions[permissionName].description}
                                        </div>
                                      </div>
                                    </div>
                                  ) : (
                                    <span className="text-gray-300">-</span>
                                  )}
                                </div>
                              ))}
                              
                              <div className="col-span-1 flex justify-center">
                                <Button
                                  variant="ghost"
                                  size="sm"
                                  onClick={() => handleToggleAllRow(module.module.id, menu.id)}
                                  className="text-xs"
                                >
                                  Toggle All
                                </Button>
                              </div>
                            </div>
                          ))}
                        </CollapsibleContent>
                      </Collapsible>
                    </div>
                  ))}
                </div>
              </div>

              {matrix.length === 0 && (
                <div className="text-center py-12 text-gray-500">
                  <p className="text-lg font-medium">No modules assigned to this role</p>
                  <p className="text-sm">Click "Add Module" to start assigning permissions</p>
                </div>
              )}
            </TabsContent>
          </Tabs>
        </CardContent>
      </Card>

      {/* Add Module Modal */}
      <Dialog open={isAddModuleOpen} onOpenChange={setIsAddModuleOpen}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>Add Module to {getActiveRoleName()}</DialogTitle>
            <DialogDescription>
              Select a module to add to this role. You can configure specific permissions after adding.
            </DialogDescription>
          </DialogHeader>
          
          <div className="space-y-4">
            <div>
              <label className="text-sm font-medium">Select Module</label>
              <Select onValueChange={handleModuleSelect}>
                <SelectTrigger>
                  <SelectValue placeholder="Choose an unassigned module" />
                </SelectTrigger>
                <SelectContent>
                  {unassignedModules.map((module) => (
                    <SelectItem key={module.id} value={module.id}>
                      <div>
                        <div className="font-medium">{module.name}</div>
                        {module.description && (
                          <div className="text-xs text-gray-500">{module.description}</div>
                        )}
                      </div>
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            {moduleMenus.length > 0 && (
              <div>
                <label className="text-sm font-medium">Module Menus ({moduleMenus.length})</label>
                <div className="mt-2 space-y-1 max-h-32 overflow-y-auto border rounded p-2">
                  {moduleMenus.map((menu) => (
                    <div key={menu.id} className="text-sm py-1 px-2 bg-gray-50 rounded">
                      {menu.name} <span className="text-gray-500">({menu.path})</span>
                    </div>
                  ))}
                </div>
                <p className="text-xs text-gray-500 mt-1">
                  All menus will be added with no permissions. Configure permissions after adding.
                </p>
              </div>
            )}

            <div className="flex justify-end space-x-2 pt-4">
              <Button variant="outline" onClick={() => setIsAddModuleOpen(false)}>
                Cancel
              </Button>
              <Button 
                onClick={handleSaveAddModule}
                disabled={!selectedModule}
                className="bg-blue-600 hover:bg-blue-700"
              >
                Add Module
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default RolePermissionMatrix;