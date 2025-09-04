import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Badge } from './ui/badge';
import { Label } from './ui/label';
import { Switch } from './ui/switch';
import { Button } from './ui/button';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './ui/select';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from './ui/dialog';
import { Alert, AlertDescription } from './ui/alert';
import { AlertCircle } from 'lucide-react';
import { useCRUD, DataTable, FormError } from './UserManagement';
import * as z from 'zod';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const rolePermissionSchema = z.object({
  role_id: z.string().min(1, 'Role is required'),
  permission_id: z.string().min(1, 'Permission is required'),
  is_active: z.boolean().default(true)
});

export const RolePermissions = () => {
  const [roles, setRoles] = useState([]);
  const [permissions, setPermissions] = useState([]);
  const crud = useCRUD('role-permissions', rolePermissionSchema);

  useEffect(() => {
    const fetchRelatedData = async () => {
      try {
        const [rolesRes, permsRes] = await Promise.all([
          axios.get(`${API}/roles`),
          axios.get(`${API}/permissions`)
        ]);
        setRoles(rolesRes.data);
        setPermissions(permsRes.data);
      } catch (error) {
        console.error('Failed to fetch related data:', error);
      }
    };
    
    fetchRelatedData();
  }, []);

  const getRoleName = (roleId) => {
    const role = roles.find(r => r.id === roleId);
    return role ? role.name : 'Unknown Role';
  };

  const getPermissionLabel = (permissionId) => {
    const permission = permissions.find(p => p.id === permissionId);
    return permission ? permission.label : 'Unknown Permission';
  };

  const columns = [
    { 
      key: 'role_id', 
      label: 'Role', 
      sortable: true,
      render: (item) => getRoleName(item.role_id)
    },
    { 
      key: 'permission_id', 
      label: 'Permission', 
      sortable: true,
      render: (item) => getPermissionLabel(item.permission_id)
    },
    { 
      key: 'is_active', 
      label: 'Active', 
      render: (item) => (
        <Badge variant={item.is_active ? 'default' : 'destructive'}>
          {item.is_active ? 'Yes' : 'No'}
        </Badge>
      )
    },
    { 
      key: 'created_at', 
      label: 'Created', 
      sortable: true,
      render: (item) => new Date(item.created_at).toLocaleDateString()
    }
  ];

  return (
    <div className="space-y-6">
      <DataTable
        data={crud.data}
        columns={columns}
        loading={crud.loading}
        error={crud.error}
        searchTerm={crud.searchTerm}
        setSearchTerm={crud.setSearchTerm}
        sortField={crud.sortField}
        sortDirection={crud.sortDirection}
        currentPage={crud.currentPage}
        setCurrentPage={crud.setCurrentPage}
        totalPages={crud.totalPages}
        onSort={crud.handleSort}
        onExport={crud.exportToCSV}
        onView={crud.openViewDialog}
        onEdit={crud.openEditDialog}
        onDelete={crud.handleDelete}
        onAdd={crud.openCreateDialog}
        title="Role Permissions"
      />

      {/* Create/Edit Dialog */}
      <Dialog open={crud.isDialogOpen} onOpenChange={crud.setIsDialogOpen}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>{crud.editingItem ? 'Edit Role Permission' : 'Create Role Permission'}</DialogTitle>
            <DialogDescription>
              {crud.editingItem ? 'Update role permission mapping' : 'Assign permissions to roles'}
            </DialogDescription>
          </DialogHeader>
          
          {crud.error && (
            <Alert className="border-red-200 bg-red-50">
              <AlertCircle className="h-4 w-4 text-red-600" />
              <AlertDescription className="text-red-800">{crud.error}</AlertDescription>
            </Alert>
          )}

          <form onSubmit={crud.form.handleSubmit(crud.handleSubmit)} className="space-y-4">
            <div>
              <Label htmlFor="role_id">Role *</Label>
              <Select onValueChange={(value) => crud.form.setValue('role_id', value)}>
                <SelectTrigger>
                  <SelectValue placeholder="Select role" />
                </SelectTrigger>
                <SelectContent>
                  {roles.map((role) => (
                    <SelectItem key={role.id} value={role.id}>
                      {role.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              <FormError error={crud.form.formState.errors.role_id} />
            </div>

            <div>
              <Label htmlFor="permission_id">Permission *</Label>
              <Select onValueChange={(value) => crud.form.setValue('permission_id', value)}>
                <SelectTrigger>
                  <SelectValue placeholder="Select permission" />
                </SelectTrigger>
                <SelectContent>
                  {permissions.map((permission) => (
                    <SelectItem key={permission.id} value={permission.id}>
                      {permission.label} ({permission.key})
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              <FormError error={crud.form.formState.errors.permission_id} />
            </div>

            <div className="flex items-center space-x-2">
              <Switch
                {...crud.form.register('is_active')}
                id="is_active"
                defaultChecked={true}
              />
              <Label htmlFor="is_active">Is Active</Label>
            </div>

            <div className="flex justify-end space-x-2 pt-4">
              <Button
                type="button"
                variant="outline"
                onClick={() => crud.setIsDialogOpen(false)}
              >
                Cancel
              </Button>
              <Button type="submit" className="bg-blue-600 hover:bg-blue-700">
                {crud.editingItem ? 'Update' : 'Create'}
              </Button>
            </div>
          </form>
        </DialogContent>
      </Dialog>

      {/* View Dialog */}
      <Dialog open={!!crud.viewingItem} onOpenChange={() => crud.setViewingItem(null)}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>Role Permission Details</DialogTitle>
          </DialogHeader>
          {crud.viewingItem && (
            <div className="space-y-3">
              <div>
                <Label className="font-medium">Role:</Label>
                <p className="text-sm text-gray-600">{getRoleName(crud.viewingItem.role_id)}</p>
              </div>
              <div>
                <Label className="font-medium">Permission:</Label>
                <p className="text-sm text-gray-600">{getPermissionLabel(crud.viewingItem.permission_id)}</p>
              </div>
              <div>
                <Label className="font-medium">Active:</Label>
                <Badge variant={crud.viewingItem.is_active ? 'default' : 'destructive'}>
                  {crud.viewingItem.is_active ? 'Yes' : 'No'}
                </Badge>
              </div>
              <div>
                <Label className="font-medium">Created:</Label>
                <p className="text-sm text-gray-600">
                  {new Date(crud.viewingItem.created_at).toLocaleString()}
                </p>
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
};