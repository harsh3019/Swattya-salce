import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import * as z from 'zod';

// Import Shadcn components
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Label } from './ui/label';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from './ui/dialog';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from './ui/table';
import { Badge } from './ui/badge';
import { Alert, AlertDescription } from './ui/alert';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './ui/select';
import { Textarea } from './ui/textarea';
import { Switch } from './ui/switch';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/tabs';

// Icons
import { 
  Plus, 
  Search, 
  Download, 
  Eye, 
  Edit2, 
  Trash2, 
  ChevronLeft,
  ChevronRight,
  ArrowUpDown,
  Filter,
  X,
  AlertCircle
} from 'lucide-react';

import { toast } from 'sonner';
import { usePermissions } from '../contexts/PermissionContext';
import ProtectedButton from './ProtectedButton';
import PermissionDataTable from './PermissionDataTable';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Validation Schemas
const userSchema = z.object({
  username: z.string().min(3, 'Username must be at least 3 characters'),
  email: z.string().email('Invalid email address'),
  password: z.string().min(6, 'Password must be at least 6 characters').optional(),
  role_id: z.string().optional(),
  department_id: z.string().optional(),
  designation_id: z.string().optional(),
  status: z.string().default('active'),
  is_active: z.boolean().default(true)
});

const roleSchema = z.object({
  name: z.string().min(2, 'Role name must be at least 2 characters'),
  description: z.string().optional(),
  is_active: z.boolean().default(true)
});

const departmentSchema = z.object({
  name: z.string().min(2, 'Department name must be at least 2 characters'),
  is_active: z.boolean().default(true)
});

const designationSchema = z.object({
  name: z.string().min(2, 'Designation name must be at least 2 characters'),
  is_active: z.boolean().default(true)
});

const permissionSchema = z.object({
  name: z.string().min(2, 'Permission name must be at least 2 characters'),
  description: z.string().optional(),
  status: z.string().default('active'),
  is_active: z.boolean().default(true)
});

const moduleSchema = z.object({
  name: z.string().min(2, 'Module name must be at least 2 characters'),
  description: z.string().optional(),
  status: z.string().default('active'),
  is_active: z.boolean().default(true)
});

const menuSchema = z.object({
  name: z.string().min(2, 'Menu name must be at least 2 characters'),
  path: z.string().min(1, 'Path is required'),
  parent: z.string().optional(),
  module_id: z.string().min(1, 'Module is required'),
  order_index: z.coerce.number().min(0, 'Order must be 0 or greater'),
  is_active: z.boolean().default(true)
});

// Generic CRUD Hook
const useCRUD = (endpoint, schema) => {
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [searchTerm, setSearchTerm] = useState('');
  const [sortField, setSortField] = useState('');
  const [sortDirection, setSortDirection] = useState('asc');
  const [currentPage, setCurrentPage] = useState(1);
  const [itemsPerPage] = useState(10);

  // Form states
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [editingItem, setEditingItem] = useState(null);
  const [viewingItem, setViewingItem] = useState(null);

  const form = useForm({
    resolver: zodResolver(schema),
    defaultValues: {}
  });

  const fetchData = async () => {
    try {
      setLoading(true);
      setError('');
      const response = await axios.get(`${API}/${endpoint}`);
      setData(response.data);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to fetch data');
      toast.error('Failed to fetch data');
    } finally {
      setLoading(false);
    }
  };

  const createItem = async (itemData) => {
    try {
      setError('');
      const response = await axios.post(`${API}/${endpoint}`, itemData);
      setData(prev => [...prev, response.data]);
      toast.success('Item created successfully');
      setIsDialogOpen(false);
      form.reset();
      return true;
    } catch (err) {
      const errorMsg = err.response?.data?.detail || 'Failed to create item';
      setError(errorMsg);
      toast.error(errorMsg);
      return false;
    }
  };

  const updateItem = async (id, itemData) => {
    try {
      setError('');
      const response = await axios.put(`${API}/${endpoint}/${id}`, itemData);
      setData(prev => prev.map(item => item.id === id ? response.data : item));
      toast.success('Item updated successfully');
      setIsDialogOpen(false);
      setEditingItem(null);
      form.reset();
      return true;
    } catch (err) {
      const errorMsg = err.response?.data?.detail || 'Failed to update item';
      setError(errorMsg);
      toast.error(errorMsg);
      return false;
    }
  };

  const deleteItem = async (id) => {
    try {
      setError('');
      await axios.delete(`${API}/${endpoint}/${id}`);
      setData(prev => prev.filter(item => item.id !== id));
      toast.success('Item deleted successfully');
      return true;
    } catch (err) {
      const errorMsg = err.response?.data?.detail || 'Failed to delete item';
      setError(errorMsg);
      toast.error(errorMsg);
      return false;
    }
  };

  const exportToCSV = () => {
    if (data.length === 0) {
      toast.error('No data to export');
      return;
    }

    const headers = Object.keys(data[0]).join(',');
    const csvData = data.map(row => 
      Object.values(row).map(value => 
        typeof value === 'string' ? `"${value}"` : value
      ).join(',')
    ).join('\n');

    const csv = `${headers}\n${csvData}`;
    const blob = new Blob([csv], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${endpoint}_export_${new Date().toISOString().split('T')[0]}.csv`;
    a.click();
    window.URL.revokeObjectURL(url);
    toast.success('Data exported successfully');
  };

  // Filtered and sorted data
  const filteredData = data.filter(item => {
    if (!searchTerm) return true;
    return Object.values(item).some(value => 
      value?.toString().toLowerCase().includes(searchTerm.toLowerCase())
    );
  });

  const sortedData = [...filteredData].sort((a, b) => {
    if (!sortField) return 0;
    const aVal = a[sortField] || '';
    const bVal = b[sortField] || '';
    
    if (sortDirection === 'asc') {
      return aVal.toString().localeCompare(bVal.toString());
    } else {
      return bVal.toString().localeCompare(aVal.toString());
    }
  });

  // Pagination
  const totalPages = Math.ceil(sortedData.length / itemsPerPage);
  const startIndex = (currentPage - 1) * itemsPerPage;
  const paginatedData = sortedData.slice(startIndex, startIndex + itemsPerPage);

  const handleSort = (field) => {
    if (sortField === field) {
      setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc');
    } else {
      setSortField(field);
      setSortDirection('asc');
    }
  };

  const openCreateDialog = () => {
    setEditingItem(null);
    setError('');
    form.reset();
    setIsDialogOpen(true);
  };

  const openEditDialog = (item) => {
    setEditingItem(item);
    setError('');
    form.reset(item);
    setIsDialogOpen(true);
  };

  const openViewDialog = (item) => {
    setViewingItem(item);
  };

  const handleSubmit = async (data) => {
    console.log('🔍 Form submitted with data:', data);
    console.log('🔍 Editing item:', editingItem ? 'Yes' : 'No');
    
    try {
      if (editingItem) {
        console.log('🔍 Calling updateItem...');
        return await updateItem(editingItem.id, data);
      } else {
        console.log('🔍 Calling createItem...');
        return await createItem(data);
      }
    } catch (error) {
      console.error('❌ Error in handleSubmit:', error);
      return false;
    }
  };

  const handleDelete = async (item) => {
    if (window.confirm(`Are you sure you want to delete "${item.name || item.username || item.id}"?`)) {
      await deleteItem(item.id);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  return {
    data: paginatedData,
    allData: data,
    loading,
    error,
    setError,
    searchTerm,
    setSearchTerm,
    sortField,
    sortDirection,
    currentPage,
    setCurrentPage,
    totalPages,
    itemsPerPage,
    form,
    isDialogOpen,
    setIsDialogOpen,
    editingItem,
    viewingItem,
    setViewingItem,
    fetchData,
    createItem,
    updateItem,
    deleteItem,
    exportToCSV,
    handleSort,
    openCreateDialog,
    openEditDialog,
    openViewDialog,
    handleSubmit,
    handleDelete
  };
};

// Generic Table Component
const DataTable = ({ 
  data, 
  columns, 
  loading, 
  error,
  searchTerm,
  setSearchTerm,
  sortField,
  sortDirection,
  currentPage,
  setCurrentPage,
  totalPages,
  onSort,
  onExport,
  onView,
  onEdit,
  onDelete,
  onAdd,
  title,
  modulePath = ''
}) => {
  const { canAdd, canEdit, canDelete, canView } = usePermissions();
  if (loading) {
    return (
      <div className="flex items-center justify-center p-8">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="text-2xl font-bold">{title}</CardTitle>
            <CardDescription>Manage {title.toLowerCase()}</CardDescription>
          </div>
          <div className="flex items-center space-x-2">
            {canAdd(modulePath) && (
              <Button onClick={onAdd} className="bg-blue-600 hover:bg-blue-700">
                <Plus className="w-4 h-4 mr-2" />
                Add {title.slice(0, -1)}
              </Button>
            )}
          </div>
        </div>
      </CardHeader>
      <CardContent>
        {error && (
          <Alert className="mb-4 border-red-200 bg-red-50">
            <AlertCircle className="h-4 w-4 text-red-600" />
            <AlertDescription className="text-red-800">{error}</AlertDescription>
          </Alert>
        )}

        {/* Search and Export */}
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center space-x-2">
            <div className="relative">
              <Search className="absolute left-2 top-2.5 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="Search..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pl-8 w-64"
              />
            </div>
          </div>
          <Button
            variant="outline"
            onClick={onExport}
            className="flex items-center space-x-2"
          >
            <Download className="w-4 h-4" />
            <span>Export CSV</span>
          </Button>
        </div>

        {/* Table */}
        <div className="rounded-md border">
          <Table>
            <TableHeader>
              <TableRow>
                {columns.map((column) => (
                  <TableHead
                    key={column.key}
                    className={column.sortable ? "cursor-pointer hover:bg-slate-50" : ""}
                    onClick={() => column.sortable && onSort(column.key)}
                  >
                    <div className="flex items-center space-x-1">
                      <span>{column.label}</span>
                      {column.sortable && (
                        <ArrowUpDown className="w-4 h-4" />
                      )}
                      {sortField === column.key && (
                        <span className="text-xs">
                          {sortDirection === 'asc' ? '↑' : '↓'}
                        </span>
                      )}
                    </div>
                  </TableHead>
                ))}
                <TableHead>Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {data.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={columns.length + 1} className="text-center py-8">
                    <div className="text-gray-500">
                      <p className="text-lg font-medium">No data found</p>
                      <p className="text-sm">Add new items to get started</p>
                    </div>
                  </TableCell>
                </TableRow>
              ) : (
                data.map((item) => (
                  <TableRow key={item.id}>
                    {columns.map((column) => (
                      <TableCell key={column.key}>
                        {column.render ? column.render(item) : item[column.key]}
                      </TableCell>
                    ))}
                    <TableCell>
                      <div className="flex items-center space-x-1">
                        {canView(modulePath) && (
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => onView(item)}
                            className="h-8 w-8 p-0"
                          >
                            <Eye className="w-4 h-4" />
                          </Button>
                        )}
                        {canEdit(modulePath) && (
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => onEdit(item)}
                            className="h-8 w-8 p-0"
                          >
                            <Edit2 className="w-4 h-4" />
                          </Button>
                        )}
                        {canDelete(modulePath) && (
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => onDelete(item)}
                            className="h-8 w-8 p-0 text-red-600 hover:text-red-700 hover:bg-red-50"
                          >
                            <Trash2 className="w-4 h-4" />
                          </Button>
                        )}
                      </div>
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </div>

        {/* Pagination */}
        {totalPages > 1 && (
          <div className="flex items-center justify-between mt-4">
            <div className="text-sm text-gray-500">
              Page {currentPage} of {totalPages}
            </div>
            <div className="flex items-center space-x-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => setCurrentPage(prev => Math.max(1, prev - 1))}
                disabled={currentPage === 1}
              >
                <ChevronLeft className="w-4 h-4" />
                Previous
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={() => setCurrentPage(prev => Math.min(totalPages, prev + 1))}
                disabled={currentPage === totalPages}
              >
                Next
                <ChevronRight className="w-4 h-4" />
              </Button>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
};

// Form Error Component
const FormError = ({ error }) => {
  if (!error) return null;
  
  return (
    <div className="text-red-600 text-sm mt-1 flex items-center">
      <AlertCircle className="w-4 h-4 mr-1" />
      {error.message}
    </div>
  );
};

// Users Component
// Export the shared components and hook
export { useCRUD, DataTable, FormError };

export const Users = () => {
  const [roles, setRoles] = useState([]);
  const [departments, setDepartments] = useState([]);
  const [designations, setDesignations] = useState([]);

  const crud = useCRUD('users', userSchema);

  useEffect(() => {
    const fetchRelatedData = async () => {
      try {
        const [rolesRes, deptsRes, desigsRes] = await Promise.all([
          axios.get(`${API}/roles`),
          axios.get(`${API}/departments`),
          axios.get(`${API}/designations`)
        ]);
        setRoles(rolesRes.data);
        setDepartments(deptsRes.data);
        setDesignations(desigsRes.data);
      } catch (error) {
        console.error('Failed to fetch related data:', error);
      }
    };
    
    fetchRelatedData();
  }, []);

  const getRoleName = (roleId) => {
    const role = roles.find(r => r.id === roleId);
    return role ? role.name : '-';
  };

  const getDepartmentName = (deptId) => {
    const dept = departments.find(d => d.id === deptId);
    return dept ? dept.name : '-';
  };

  const getDesignationName = (desigId) => {
    const desig = designations.find(d => d.id === desigId);
    return desig ? desig.name : '-';
  };

  const columns = [
    { key: 'username', label: 'Username', sortable: true },
    { key: 'email', label: 'Email', sortable: true },
    { 
      key: 'role_id', 
      label: 'Role', 
      sortable: true,
      render: (item) => getRoleName(item.role_id)
    },
    { 
      key: 'department_id', 
      label: 'Department', 
      sortable: true,
      render: (item) => getDepartmentName(item.department_id)
    },
    { 
      key: 'designation_id', 
      label: 'Designation', 
      sortable: true,
      render: (item) => getDesignationName(item.designation_id)
    },
    { 
      key: 'status', 
      label: 'Status', 
      sortable: true,
      render: (item) => (
        <Badge variant={item.status === 'active' ? 'default' : 'secondary'}>
          {item.status}
        </Badge>
      )
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
      key: 'last_login_at', 
      label: 'Last Login', 
      sortable: true,
      render: (item) => item.last_login_at ? new Date(item.last_login_at).toLocaleDateString() : 'Never'
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
        sortField={crud.sortField}
        sortDirection={crud.sortDirection}
        currentPage={crud.currentPage}
        setCurrentPage={crud.setCurrentPage}
        totalPages={crud.totalPages}
        onSort={crud.handleSort}
        onView={crud.openViewDialog}
        onEdit={crud.openEditDialog}
        onDelete={crud.handleDelete}
        onAdd={crud.openCreateDialog}
        title="Users"
        modulePath="/users"
        entityName="users"
      />

      {/* Create/Edit Dialog */}
      <Dialog open={crud.isDialogOpen} onOpenChange={crud.setIsDialogOpen}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>{crud.editingItem ? 'Edit User' : 'Create User'}</DialogTitle>
            <DialogDescription>
              {crud.editingItem ? 'Update user details' : 'Add a new user to the system'}
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
              <Label htmlFor="username">Username *</Label>
              <Input
                {...crud.form.register('username')}
                id="username"
                placeholder="Enter username"
              />
              <FormError error={crud.form.formState.errors.username} />
            </div>

            <div>
              <Label htmlFor="email">Email *</Label>
              <Input
                {...crud.form.register('email')}
                id="email"
                type="email"
                placeholder="Enter email"
              />
              <FormError error={crud.form.formState.errors.email} />
            </div>

            {!crud.editingItem && (
              <div>
                <Label htmlFor="password">Password *</Label>
                <Input
                  {...crud.form.register('password')}
                  id="password"
                  type="password"
                  placeholder="Enter password"
                />
                <FormError error={crud.form.formState.errors.password} />
              </div>
            )}

            <div>
              <Label htmlFor="role_id">Role</Label>
              <Select 
                onValueChange={(value) => crud.form.setValue('role_id', value)}
                defaultValue={crud.editingItem?.role_id}
              >
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
            </div>

            <div>
              <Label htmlFor="department_id">Department</Label>
              <Select 
                onValueChange={(value) => crud.form.setValue('department_id', value)}
                defaultValue={crud.editingItem?.department_id}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Select department" />
                </SelectTrigger>
                <SelectContent>
                  {departments.map((dept) => (
                    <SelectItem key={dept.id} value={dept.id}>
                      {dept.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div>
              <Label htmlFor="designation_id">Designation</Label>
              <Select 
                onValueChange={(value) => crud.form.setValue('designation_id', value)}
                defaultValue={crud.editingItem?.designation_id}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Select designation" />
                </SelectTrigger>
                <SelectContent>
                  {designations.map((desig) => (
                    <SelectItem key={desig.id} value={desig.id}>
                      {desig.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div>
              <Label htmlFor="status">Status</Label>
              <Select onValueChange={(value) => crud.form.setValue('status', value)} defaultValue="active">
                <SelectTrigger>
                  <SelectValue placeholder="Select status" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="active">Active</SelectItem>
                  <SelectItem value="inactive">Inactive</SelectItem>
                  <SelectItem value="suspended">Suspended</SelectItem>
                </SelectContent>
              </Select>
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
            <DialogTitle>User Details</DialogTitle>
          </DialogHeader>
          {crud.viewingItem && (
            <div className="space-y-3">
              <div>
                <Label className="font-medium">Username:</Label>
                <p className="text-sm text-gray-600">{crud.viewingItem.username}</p>
              </div>
              <div>
                <Label className="font-medium">Email:</Label>
                <p className="text-sm text-gray-600">{crud.viewingItem.email}</p>
              </div>
              <div>
                <Label className="font-medium">Status:</Label>
                <Badge variant={crud.viewingItem.status === 'active' ? 'default' : 'secondary'}>
                  {crud.viewingItem.status}
                </Badge>
              </div>
              <div>
                <Label className="font-medium">Active:</Label>
                <Badge variant={crud.viewingItem.is_active ? 'default' : 'destructive'}>
                  {crud.viewingItem.is_active ? 'Yes' : 'No'}
                </Badge>
              </div>
              <div>
                <Label className="font-medium">Last Login:</Label>
                <p className="text-sm text-gray-600">
                  {crud.viewingItem.last_login_at ? new Date(crud.viewingItem.last_login_at).toLocaleString() : 'Never'}
                </p>
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