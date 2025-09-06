import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Badge } from './ui/badge';
import { Label } from './ui/label';
import { Input } from './ui/input';
import { Button } from './ui/button';
import { Textarea } from './ui/textarea';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogFooter } from './ui/dialog';
import { Alert, AlertDescription } from './ui/alert';
import { AlertCircle, Package, Eye, Edit, Trash2, FileDown, Plus } from 'lucide-react';
import { toast } from 'sonner';
import PermissionDataTable from './PermissionDataTable';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export const ProductServicesList = () => {
  const [productServices, setProductServices] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [searchTerm, setSearchTerm] = useState('');
  const [sortField, setSortField] = useState('');
  const [sortDirection, setSortDirection] = useState('asc');
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  
  // Dialog states
  const [viewingItem, setViewingItem] = useState(null);
  const [editingItem, setEditingItem] = useState(null);
  const [isAddDialogOpen, setIsAddDialogOpen] = useState(false);
  const [isEditDialogOpen, setIsEditDialogOpen] = useState(false);
  
  // Form data
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    is_active: true
  });
  const [formErrors, setFormErrors] = useState({});
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    fetchProductServices();
  }, []);

  const fetchProductServices = async () => {
    try {
      setLoading(true);
      setError('');
      const response = await axios.get(`${API}/product-services`);
      setProductServices(response.data || []);
    } catch (err) {
      const errorMsg = err.response?.data?.detail || 'Failed to fetch product services';
      setError(errorMsg);
      toast.error(errorMsg);
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (item) => {
    if (window.confirm(`Are you sure you want to delete "${item.name}"?`)) {
      try {
        await axios.delete(`${API}/product-services/${item.id}`);
        toast.success('Product/Service deleted successfully');
        fetchProductServices();
      } catch (err) {
        const errorMsg = err.response?.data?.detail || 'Failed to delete product/service';
        toast.error(errorMsg);
      }
    }
  };

  const handleSort = (field) => {
    const newDirection = sortField === field && sortDirection === 'asc' ? 'desc' : 'asc';
    setSortField(field);
    setSortDirection(newDirection);
  };

  const exportToCSV = async () => {
    try {
      const csvContent = convertToCSV(productServices);
      downloadCSV(csvContent, 'product_services_export.csv');
      toast.success('Product Services exported successfully');
    } catch (err) {
      toast.error('Failed to export product services');
    }
  };

  const convertToCSV = (data) => {
    if (!data.length) return '';
    
    const headers = ['Name', 'Description', 'Status', 'Created Date', 'Updated Date'];
    const rows = data.map(item => [
      item.name || '',
      item.description || '',
      item.is_active ? 'Active' : 'Inactive',
      new Date(item.created_at).toLocaleDateString(),
      new Date(item.updated_at).toLocaleDateString()
    ]);
    
    return [headers, ...rows].map(row => row.join(',')).join('\n');
  };

  const downloadCSV = (content, filename) => {
    const blob = new Blob([content], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    const url = URL.createObjectURL(blob);
    link.setAttribute('href', url);
    link.setAttribute('download', filename);
    link.style.visibility = 'hidden';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  // Form handlers
  const resetForm = () => {
    setFormData({
      name: '',
      description: '',
      is_active: true
    });
    setFormErrors({});
  };

  const handleAddClick = () => {
    resetForm();
    setIsAddDialogOpen(true);
  };

  const handleEditClick = (item) => {
    setFormData({
      name: item.name,
      description: item.description || '',
      is_active: item.is_active
    });
    setEditingItem(item);
    setFormErrors({});
    setIsEditDialogOpen(true);
  };

  const validateForm = () => {
    const errors = {};
    
    if (!formData.name.trim()) {
      errors.name = 'Name is required';
    } else if (formData.name.trim().length < 2) {
      errors.name = 'Name must be at least 2 characters';
    } else if (formData.name.trim().length > 100) {
      errors.name = 'Name must be less than 100 characters';
    }
    
    if (formData.description && formData.description.length > 500) {
      errors.description = 'Description must be less than 500 characters';
    }
    
    setFormErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!validateForm()) {
      return;
    }
    
    setSubmitting(true);
    
    try {
      const submitData = {
        name: formData.name.trim(),
        description: formData.description.trim(),
        is_active: formData.is_active
      };
      
      if (editingItem) {
        // Update existing
        await axios.put(`${API}/product-services/${editingItem.id}`, submitData);
        toast.success('Product/Service updated successfully');
        setIsEditDialogOpen(false);
        setEditingItem(null);
      } else {
        // Create new
        await axios.post(`${API}/product-services`, submitData);
        toast.success('Product/Service created successfully');
        setIsAddDialogOpen(false);
      }
      
      resetForm();
      fetchProductServices();
    } catch (err) {
      const errorMsg = err.response?.data?.detail || 'Failed to save product/service';
      toast.error(errorMsg);
    } finally {
      setSubmitting(false);
    }
  };

  // Filter and sort data
  const filteredData = productServices.filter(item =>
    item.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    (item.description && item.description.toLowerCase().includes(searchTerm.toLowerCase()))
  );

  const sortedData = [...filteredData].sort((a, b) => {
    if (!sortField) return 0;
    
    let aValue = a[sortField];
    let bValue = b[sortField];
    
    if (typeof aValue === 'string') {
      aValue = aValue.toLowerCase();
      bValue = bValue.toLowerCase();
    }
    
    if (aValue < bValue) return sortDirection === 'asc' ? -1 : 1;
    if (aValue > bValue) return sortDirection === 'asc' ? 1 : -1;
    return 0;
  });

  const columns = [
    { 
      key: 'name', 
      label: 'Product/Service Name', 
      sortable: true,
      render: (item) => (
        <div className="flex items-center space-x-2">
          <Package className="h-4 w-4 text-blue-600" />
          <div>
            <p className="font-medium">{item.name}</p>
            <p className="text-sm text-gray-500 truncate max-w-xs">
              {item.description || 'No description'}
            </p>
          </div>
        </div>
      )
    },
    { 
      key: 'description', 
      label: 'Description', 
      render: (item) => (
        <div className="max-w-md">
          <p className="text-sm text-gray-600 truncate">
            {item.description || 'No description provided'}
          </p>
        </div>
      )
    },
    { 
      key: 'is_active', 
      label: 'Status', 
      sortable: true,
      render: (item) => (
        <Badge variant={item.is_active ? 'default' : 'destructive'}>
          {item.is_active ? 'Active' : 'Inactive'}
        </Badge>
      )
    },
    { 
      key: 'created_at', 
      label: 'Created', 
      sortable: true,
      render: (item) => (
        <div className="text-sm text-gray-600">
          {new Date(item.created_at).toLocaleDateString()}
        </div>
      )
    },
    { 
      key: 'updated_at', 
      label: 'Updated', 
      sortable: true,
      render: (item) => (
        <div className="text-sm text-gray-600">
          {new Date(item.updated_at).toLocaleDateString()}
        </div>
      )
    }
  ];

  return (
    <div className="space-y-6">
      {error && (
        <Alert className="border-red-200 bg-red-50">
          <AlertCircle className="h-4 w-4 text-red-600" />
          <AlertDescription className="text-red-800">{error}</AlertDescription>
        </Alert>
      )}

      <PermissionDataTable
        data={sortedData}
        columns={columns}
        loading={loading}
        error={error}
        searchTerm={searchTerm}
        setSearchTerm={setSearchTerm}
        sortField={sortField}
        sortDirection={sortDirection}
        currentPage={currentPage}
        setCurrentPage={setCurrentPage}
        totalPages={totalPages}
        onSort={handleSort}
        onExport={exportToCSV}
        onView={(item) => setViewingItem(item)}
        onEdit={handleEditClick}
        onDelete={handleDelete}
        onAdd={handleAddClick}
        title="Product & Services"
        description="Manage product and service offerings"
        modulePath="/product-services"
        entityName="product-services"
      />

      {/* View Dialog */}
      <Dialog open={!!viewingItem} onOpenChange={() => setViewingItem(null)}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle className="flex items-center space-x-2">
              <Package className="h-5 w-5" />
              <span>Product/Service Details</span>
            </DialogTitle>
          </DialogHeader>
          
          {viewingItem && (
            <div className="space-y-4">
              <div className="grid grid-cols-1 gap-4">
                <div>
                  <Label className="font-medium">Name:</Label>
                  <p className="text-gray-700 text-lg">{viewingItem.name}</p>
                </div>
                
                <div>
                  <Label className="font-medium">Description:</Label>
                  <p className="text-gray-600">
                    {viewingItem.description || 'No description provided'}
                  </p>
                </div>
                
                <div>
                  <Label className="font-medium">Status:</Label>
                  <Badge variant={viewingItem.is_active ? 'default' : 'destructive'}>
                    {viewingItem.is_active ? 'Active' : 'Inactive'}
                  </Badge>
                </div>
                
                <div className="border-t pt-4 grid grid-cols-2 gap-4">
                  <div>
                    <Label className="font-medium">Created:</Label>
                    <p className="text-gray-600">
                      {new Date(viewingItem.created_at).toLocaleString()}
                    </p>
                  </div>
                  <div>
                    <Label className="font-medium">Last Updated:</Label>
                    <p className="text-gray-600">
                      {new Date(viewingItem.updated_at).toLocaleString()}
                    </p>
                  </div>
                </div>
                
                <div>
                  <Label className="font-medium">ID:</Label>
                  <p className="text-xs text-gray-500 font-mono">{viewingItem.id}</p>
                </div>
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>

      {/* Add Dialog */}
      <Dialog open={isAddDialogOpen} onOpenChange={setIsAddDialogOpen}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle className="flex items-center space-x-2">
              <Plus className="h-5 w-5" />
              <span>Add Product/Service</span>
            </DialogTitle>
            <DialogDescription>
              Create a new product or service offering
            </DialogDescription>
          </DialogHeader>
          
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <Label htmlFor="name">Name *</Label>
              <Input
                id="name"
                value={formData.name}
                onChange={(e) => setFormData({...formData, name: e.target.value})}
                placeholder="Enter product/service name"
                className={formErrors.name ? 'border-red-500' : ''}
              />
              {formErrors.name && (
                <p className="text-sm text-red-600 mt-1">{formErrors.name}</p>
              )}
            </div>
            
            <div>
              <Label htmlFor="description">Description</Label>
              <Textarea
                id="description"
                value={formData.description}
                onChange={(e) => setFormData({...formData, description: e.target.value})}
                placeholder="Enter description (optional)"
                rows={3}
                className={formErrors.description ? 'border-red-500' : ''}
              />
              {formErrors.description && (
                <p className="text-sm text-red-600 mt-1">{formErrors.description}</p>
              )}
            </div>
            
            <DialogFooter>
              <Button 
                type="button" 
                variant="outline" 
                onClick={() => setIsAddDialogOpen(false)}
                disabled={submitting}
              >
                Cancel
              </Button>
              <Button type="submit" disabled={submitting}>
                {submitting ? 'Creating...' : 'Create'}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      {/* Edit Dialog */}
      <Dialog open={isEditDialogOpen} onOpenChange={setIsEditDialogOpen}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle className="flex items-center space-x-2">
              <Edit className="h-5 w-5" />
              <span>Edit Product/Service</span>
            </DialogTitle>
            <DialogDescription>
              Update product or service information
            </DialogDescription>
          </DialogHeader>
          
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <Label htmlFor="edit-name">Name *</Label>
              <Input
                id="edit-name"
                value={formData.name}
                onChange={(e) => setFormData({...formData, name: e.target.value})}
                placeholder="Enter product/service name"
                className={formErrors.name ? 'border-red-500' : ''}
              />
              {formErrors.name && (
                <p className="text-sm text-red-600 mt-1">{formErrors.name}</p>
              )}
            </div>
            
            <div>
              <Label htmlFor="edit-description">Description</Label>
              <Textarea
                id="edit-description"
                value={formData.description}
                onChange={(e) => setFormData({...formData, description: e.target.value})}
                placeholder="Enter description (optional)"
                rows={3}
                className={formErrors.description ? 'border-red-500' : ''}
              />
              {formErrors.description && (
                <p className="text-sm text-red-600 mt-1">{formErrors.description}</p>
              )}
            </div>
            
            <DialogFooter>
              <Button 
                type="button" 
                variant="outline" 
                onClick={() => {
                  setIsEditDialogOpen(false);
                  setEditingItem(null);
                }}
                disabled={submitting}
              >
                Cancel
              </Button>
              <Button type="submit" disabled={submitting}>
                {submitting ? 'Updating...' : 'Update'}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default ProductServicesList;