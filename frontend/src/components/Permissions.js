import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Badge } from './ui/badge';
import { Label } from './ui/label';
import { Input } from './ui/input';
import { Switch } from './ui/switch';
import { Button } from './ui/button';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './ui/select';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from './ui/dialog';
import { Alert, AlertDescription } from './ui/alert';
import { AlertCircle } from 'lucide-react';
import { useCRUD, FormError } from './UserManagement';
import PermissionDataTable from './PermissionDataTable';
import * as z from 'zod';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const permissionSchema = z.object({
  key: z.string().min(3, 'Permission key must be at least 3 characters'),
  label: z.string().min(2, 'Permission label must be at least 2 characters'),
  module_id: z.string().min(1, 'Module is required'),
  is_active: z.boolean().default(true)
});

export const Permissions = () => {
  const [modules, setModules] = useState([]);
  const crud = useCRUD('permissions', permissionSchema);

  useEffect(() => {
    const fetchModules = async () => {
      try {
        const response = await axios.get(`${API}/modules`);
        setModules(response.data);
      } catch (error) {
        console.error('Failed to fetch modules:', error);
      }
    };
    
    fetchModules();
  }, []);

  const getModuleName = (moduleId) => {
    const module = modules.find(m => m.id === moduleId);
    return module ? module.name : 'Unknown Module';
  };

  const columns = [
    { key: 'name', label: 'Permission Name', sortable: true },
    { key: 'description', label: 'Description', sortable: true },
    { key: 'status', label: 'Status', sortable: true },
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
      <PermissionDataTable
        data={crud.data}
        columns={columns}
        loading={crud.loading}
        error={crud.error}
        searchTerm={crud.searchTerm}
        setSearchTerm={crud.setSearchTerm}
        sortField={crud.sortDirection}
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
        title="Permissions"
        modulePath="/permissions"
        entityName="permissions"
      />

      {/* Create/Edit Dialog */}
      <Dialog open={crud.isDialogOpen} onOpenChange={crud.setIsDialogOpen}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>{crud.editingItem ? 'Edit Permission' : 'Create Permission'}</DialogTitle>
            <DialogDescription>
              {crud.editingItem ? 'Update permission details' : 'Add a new permission to the system'}
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
              <Label htmlFor="key">Permission Key *</Label>
              <Input
                {...crud.form.register('key')}
                id="key"
                placeholder="Enter permission key"
              />
              <FormError error={crud.form.formState.errors.key} />
            </div>

            <div>
              <Label htmlFor="label">Permission Label *</Label>
              <Input
                {...crud.form.register('label')}
                id="label"
                placeholder="Enter permission label"
              />
              <FormError error={crud.form.formState.errors.label} />
            </div>

            <div>
              <Label htmlFor="module_id">Module *</Label>
              <Select 
                onValueChange={(value) => crud.form.setValue('module_id', value)}
                defaultValue={crud.editingItem?.module_id}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Select module" />
                </SelectTrigger>
                <SelectContent>
                  {modules.map((module) => (
                    <SelectItem key={module.id} value={module.id}>
                      {module.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              <FormError error={crud.form.formState.errors.module_id} />
            </div>

            <div className="flex items-center space-x-2">
              <Switch
                onCheckedChange={(checked) => crud.form.setValue('is_active', checked)}
                checked={crud.form.watch('is_active')}
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
            <DialogTitle>Permission Details</DialogTitle>
          </DialogHeader>
          {crud.viewingItem && (
            <div className="space-y-3">
              <div>
                <Label className="font-medium">Key:</Label>
                <p className="text-sm text-gray-600">{crud.viewingItem.key}</p>
              </div>
              <div>
                <Label className="font-medium">Label:</Label>
                <p className="text-sm text-gray-600">{crud.viewingItem.label}</p>
              </div>
              <div>
                <Label className="font-medium">Module:</Label>
                <p className="text-sm text-gray-600">{getModuleName(crud.viewingItem.module_id)}</p>
              </div>
              <div>
                <Label className="font-medium">Status:</Label>
                <Badge variant={crud.viewingItem.is_active ? 'default' : 'destructive'}>
                  {crud.viewingItem.is_active ? 'Active' : 'Inactive'}
                </Badge>
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
};