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
import { useCRUD, DataTable, FormError } from './UserManagement';
import * as z from 'zod';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const menuSchema = z.object({
  name: z.string().min(2, 'Menu name must be at least 2 characters'),
  module_id: z.string().min(1, 'Module is required'),
  route_path: z.string().min(1, 'Route path is required'),
  icon: z.string().optional(),
  order_index: z.coerce.number().min(0, 'Order must be 0 or greater'),
  is_active: z.boolean().default(true)
});

export const Menus = () => {
  const [modules, setModules] = useState([]);
  const crud = useCRUD('menus', menuSchema);

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
    { key: 'name', label: 'Menu Name', sortable: true },
    { 
      key: 'module_id', 
      label: 'Module', 
      sortable: true,
      render: (item) => getModuleName(item.module_id)
    },
    { key: 'path', label: 'Path', sortable: true },
    { key: 'parent', label: 'Parent', sortable: true },
    { key: 'order_index', label: 'Order', sortable: true },
    { 
      key: 'is_active', 
      label: 'Active', 
      render: (item) => (
        <Badge variant={item.is_active ? 'default' : 'destructive'}>
          {item.is_active ? 'Yes' : 'No'}
        </Badge>
      )
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
        title="Menus"
      />

      {/* Create/Edit Dialog */}
      <Dialog open={crud.isDialogOpen} onOpenChange={crud.setIsDialogOpen}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>{crud.editingItem ? 'Edit Menu' : 'Create Menu'}</DialogTitle>
            <DialogDescription>
              {crud.editingItem ? 'Update menu details' : 'Add a new menu to the system'}
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
              <Label htmlFor="name">Menu Name *</Label>
              <Input
                {...crud.form.register('name')}
                id="name"
                placeholder="Enter menu name"
              />
              <FormError error={crud.form.formState.errors.name} />
            </div>

            <div>
              <Label htmlFor="module_id">Module *</Label>
              <Select onValueChange={(value) => crud.form.setValue('module_id', value)}>
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

            <div>
              <Label htmlFor="path">Path *</Label>
              <Input
                {...crud.form.register('path')}
                id="path"
                placeholder="/users, /dashboard"
              />
              <FormError error={crud.form.formState.errors.path} />
            </div>

            <div>
              <Label htmlFor="parent">Parent Menu</Label>
              <Input
                {...crud.form.register('parent')}
                id="parent"
                placeholder="Parent menu ID (leave empty for root)"
              />
              <FormError error={crud.form.formState.errors.parent} />
            </div>

            <div>
              <Label htmlFor="order_index">Order Index *</Label>
              <Input
                {...crud.form.register('order_index')}
                id="order_index"
                type="number"
                min="0"
                placeholder="0"
              />
              <FormError error={crud.form.formState.errors.order_index} />
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
            <DialogTitle>Menu Details</DialogTitle>
          </DialogHeader>
          {crud.viewingItem && (
            <div className="space-y-3">
              <div>
                <Label className="font-medium">Menu Name:</Label>
                <p className="text-sm text-gray-600">{crud.viewingItem.name}</p>
              </div>
              <div>
                <Label className="font-medium">Module:</Label>
                <p className="text-sm text-gray-600">{getModuleName(crud.viewingItem.module_id)}</p>
              </div>
              <div>
                <Label className="font-medium">Route Path:</Label>
                <p className="text-sm text-gray-600">{crud.viewingItem.route_path}</p>
              </div>
              <div>
                <Label className="font-medium">Icon:</Label>
                <p className="text-sm text-gray-600">{crud.viewingItem.icon || 'No icon'}</p>
              </div>
              <div>
                <Label className="font-medium">Order:</Label>
                <p className="text-sm text-gray-600">{crud.viewingItem.order_index}</p>
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