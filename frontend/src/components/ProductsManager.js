import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Label } from './ui/label';
import { Textarea } from './ui/textarea';
import { Badge } from './ui/badge';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from './ui/select';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from './ui/dialog';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from './ui/table';
import { 
  Plus, 
  Edit, 
  Trash2, 
  Package, 
  Search,
  Filter,
  Download,
  Upload,
  AlertCircle,
  CheckCircle,
  QrCode
} from 'lucide-react';
import axios from 'axios';

const ProductsManager = () => {
  const [products, setProducts] = useState([]);
  const [categories, setCategories] = useState([]);
  const [loading, setLoading] = useState(true);
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [isEditing, setIsEditing] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('all');
  const [formData, setFormData] = useState({
    name: '',
    product_code: '',
    squ_code: '',
    primary_category_id: '',
    description: '',
    unit: '',
    is_active: true
  });
  const [errors, setErrors] = useState({});
  const [saving, setSaving] = useState(false);

  const baseURL = process.env.REACT_APP_BACKEND_URL;

  const units = ['Project', 'License', 'Month', 'Days', 'Hours', 'Piece', 'Course', 'Package'];

  useEffect(() => {
    Promise.all([fetchProducts(), fetchCategories()]);
  }, []);

  const fetchProducts = async () => {
    try {
      setLoading(true);
      const token = localStorage.getItem('token');
      const response = await axios.get(`${baseURL}/api/mst/products`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setProducts(response.data || []);
    } catch (error) {
      console.error('Error fetching products:', error);
      alert('Error fetching products. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const fetchCategories = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(`${baseURL}/api/mst/primary-categories`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setCategories(response.data || []);
    } catch (error) {
      console.error('Error fetching categories:', error);
    }
  };

  const generateCodes = (name, categoryCode) => {
    if (!name) return { product_code: '', squ_code: '' };
    
    const nameCode = name.replace(/[^a-zA-Z0-9]/g, '').substring(0, 3).toUpperCase();
    const timestamp = Date.now().toString().slice(-3);
    
    const product_code = categoryCode ? `${categoryCode}-${nameCode}-${timestamp}` : `PRD-${nameCode}-${timestamp}`;
    const squ_code = `SQU-${categoryCode || 'PRD'}-${nameCode}-${timestamp}`;
    
    return { product_code, squ_code };
  };

  const handleInputChange = (field, value) => {
    setFormData(prev => ({
      ...prev,
      [field]: value
    }));
    
    // Auto-generate codes when name or category changes
    if ((field === 'name' || field === 'primary_category_id') && !isEditing) {
      const selectedCat = categories.find(cat => cat.id === (field === 'primary_category_id' ? value : formData.primary_category_id));
      const categoryCode = selectedCat?.category_code || '';
      const productName = field === 'name' ? value : formData.name;
      
      if (productName) {
        const codes = generateCodes(productName, categoryCode);
        setFormData(prev => ({
          ...prev,
          ...codes
        }));
      }
    }
    
    // Clear error when user starts typing
    if (errors[field]) {
      setErrors(prev => ({
        ...prev,
        [field]: ''
      }));
    }
  };

  const validateForm = () => {
    const newErrors = {};
    
    if (!formData.name.trim()) {
      newErrors.name = 'Product name is required';
    }
    
    if (!formData.product_code.trim()) {
      newErrors.product_code = 'Product code is required';
    }
    
    if (!formData.squ_code.trim()) {
      newErrors.squ_code = 'SQU code is required';
    }
    
    if (!formData.primary_category_id) {
      newErrors.primary_category_id = 'Primary category is required';
    }
    
    if (!formData.unit) {
      newErrors.unit = 'Unit is required';
    }
    
    // Check for duplicate codes
    const existingProduct = products.find(prod => 
      (prod.product_code?.toLowerCase() === formData.product_code.toLowerCase() ||
       prod.squ_code?.toLowerCase() === formData.squ_code.toLowerCase()) &&
      (!isEditing || prod.id !== formData.id)
    );
    if (existingProduct) {
      newErrors.product_code = 'Product code or SQU code already exists';
      newErrors.squ_code = 'Product code or SQU code already exists';
    }
    
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!validateForm()) {
      return;
    }
    
    setSaving(true);
    try {
      const token = localStorage.getItem('token');
      const url = isEditing 
        ? `${baseURL}/api/mst/products/${formData.id}`
        : `${baseURL}/api/mst/products`;
      
      const method = isEditing ? 'put' : 'post';
      
      await axios[method](url, formData, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      alert(`Product ${isEditing ? 'updated' : 'created'} successfully!`);
      setIsDialogOpen(false);
      resetForm();
      fetchProducts();
    } catch (error) {
      console.error('Error saving product:', error);
      const errorMessage = error.response?.data?.detail || 'Error saving product. Please try again.';
      alert(errorMessage);
    } finally {
      setSaving(false);
    }
  };

  const handleEdit = (product) => {
    setFormData({
      id: product.id,
      name: product.name || '',
      product_code: product.product_code || '',
      squ_code: product.squ_code || '',
      primary_category_id: product.primary_category_id || '',
      description: product.description || '',
      unit: product.unit || '',
      is_active: product.is_active !== false
    });
    setIsEditing(true);
    setIsDialogOpen(true);
  };

  const handleDelete = async (product) => {
    if (!window.confirm(`Are you sure you want to delete "${product.name}"?`)) {
      return;
    }
    
    try {
      const token = localStorage.getItem('token');
      await axios.delete(`${baseURL}/api/mst/products/${product.id}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      alert('Product deleted successfully!');
      fetchProducts();
    } catch (error) {
      console.error('Error deleting product:', error);
      alert('Error deleting product. Please try again.');
    }
  };

  const resetForm = () => {
    setFormData({
      name: '',
      product_code: '',
      squ_code: '',
      primary_category_id: '',
      description: '',
      unit: '',
      is_active: true
    });
    setIsEditing(false);
    setErrors({});
  };

  const openNewDialog = () => {
    resetForm();
    setIsDialogOpen(true);
  };

  const getCategoryName = (categoryId) => {
    const category = categories.find(cat => cat.id === categoryId);
    return category?.category_name || 'Unknown Category';
  };

  const filteredProducts = products.filter(product => {
    const matchesSearch = 
      product.name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      product.product_code?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      product.squ_code?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      product.description?.toLowerCase().includes(searchTerm.toLowerCase());
    
    const matchesCategory = selectedCategory === 'all' || product.primary_category_id === selectedCategory;
    
    return matchesSearch && matchesCategory;
  });

  return (
    <div className="container mx-auto p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <Package className="w-8 h-8 text-green-600" />
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Products</h1>
            <p className="text-gray-600">Manage products with SQU codes and specifications</p>
          </div>
        </div>
        <Button onClick={openNewDialog} className="flex items-center gap-2">
          <Plus className="w-4 h-4" />
          Add Product
        </Button>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-6">
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Total Products</p>
                <p className="text-2xl font-bold text-gray-900">{products.length}</p>
              </div>
              <Package className="w-8 h-8 text-green-500" />
            </div>
          </CardContent>
        </Card>
        
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">With SQU Codes</p>
                <p className="text-2xl font-bold text-blue-600">
                  {products.filter(prod => prod.squ_code).length}
                </p>
              </div>
              <QrCode className="w-8 h-8 text-blue-500" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Active</p>
                <p className="text-2xl font-bold text-green-600">
                  {products.filter(prod => prod.is_active !== false).length}
                </p>
              </div>
              <CheckCircle className="w-8 h-8 text-green-500" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Categories</p>
                <p className="text-2xl font-bold text-purple-600">{categories.length}</p>
              </div>
              <AlertCircle className="w-8 h-8 text-purple-500" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Search and Filters */}
      <Card className="mb-6">
        <CardHeader>
          <CardTitle>Search & Filters</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex flex-col md:flex-row gap-4">
            <div className="flex-1">
              <div className="relative">
                <Search className="absolute left-3 top-3 h-4 w-4 text-gray-400" />
                <Input
                  placeholder="Search products by name, code, SQU code, or description..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="pl-10"
                />
              </div>
            </div>
            <div className="flex gap-2">
              <Select value={selectedCategory} onValueChange={setSelectedCategory}>
                <SelectTrigger className="w-48">
                  <SelectValue placeholder="Filter by category" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Categories</SelectItem>
                  {categories.map((category) => (
                    <SelectItem key={category.id} value={category.id}>
                      {category.category_name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              <Button variant="outline" size="sm">
                <Filter className="w-4 h-4 mr-2" />
                Filter
              </Button>
              <Button variant="outline" size="sm">
                <Download className="w-4 h-4 mr-2" />
                Export
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Products Table */}
      <Card>
        <CardHeader>
          <CardTitle>Products List ({filteredProducts.length})</CardTitle>
          <CardDescription>
            Manage all products with SQU codes and specifications
          </CardDescription>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="flex justify-center py-8">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-green-600"></div>
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Product Name</TableHead>
                  <TableHead>Product Code</TableHead>
                  <TableHead className="hidden sm:table-cell">SQU Code</TableHead>
                  <TableHead className="hidden md:table-cell">Category</TableHead>
                  <TableHead className="hidden lg:table-cell">Unit</TableHead>
                  <TableHead className="hidden sm:table-cell">Status</TableHead>
                  <TableHead className="text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {filteredProducts.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={7} className="text-center py-8 text-gray-500">
                      {searchTerm || selectedCategory !== 'all' 
                        ? 'No products found matching your criteria.' 
                        : 'No products found. Create your first product!'}
                    </TableCell>
                  </TableRow>
                ) : (
                  filteredProducts.map((product) => (
                    <TableRow key={product.id}>
                      <TableCell className="font-medium">
                        <div>
                          <div className="font-medium">{product.name}</div>
                          {product.description && (
                            <div className="text-sm text-gray-500 truncate max-w-xs">
                              {product.description}
                            </div>
                          )}
                        </div>
                      </TableCell>
                      <TableCell>
                        <Badge variant="outline" className="font-mono text-xs">
                          {product.product_code}
                        </Badge>
                      </TableCell>
                      <TableCell className="hidden sm:table-cell">
                        <Badge variant="secondary" className="font-mono text-xs">
                          {product.squ_code || 'N/A'}
                        </Badge>
                      </TableCell>
                      <TableCell className="hidden md:table-cell">
                        <span className="text-sm">{getCategoryName(product.primary_category_id)}</span>
                      </TableCell>
                      <TableCell className="hidden lg:table-cell">
                        <Badge variant="outline">{product.unit || 'N/A'}</Badge>
                      </TableCell>
                      <TableCell className="hidden sm:table-cell">
                        <Badge variant={product.is_active !== false ? "success" : "destructive"}>
                          {product.is_active !== false ? "Active" : "Inactive"}
                        </Badge>
                      </TableCell>
                      <TableCell className="text-right">
                        <div className="flex justify-end gap-2">
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => handleEdit(product)}
                          >
                            <Edit className="w-4 h-4" />
                          </Button>
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => handleDelete(product)}
                            className="text-red-600 hover:text-red-700"
                          >
                            <Trash2 className="w-4 h-4" />
                          </Button>
                        </div>
                      </TableCell>
                    </TableRow>
                  ))
                )}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>

      {/* Add/Edit Dialog */}
      <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
        <DialogContent className="sm:max-w-[500px]">
          <DialogHeader>
            <DialogTitle>
              {isEditing ? 'Edit Product' : 'Add New Product'}
            </DialogTitle>
            <DialogDescription>
              {isEditing 
                ? 'Update the product information below.' 
                : 'Create a new product with SQU code.'
              }
            </DialogDescription>
          </DialogHeader>
          
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="grid gap-4">
              <div>
                <Label htmlFor="name">Product Name *</Label>
                <Input
                  id="name"
                  value={formData.name}
                  onChange={(e) => handleInputChange('name', e.target.value)}
                  placeholder="e.g., Custom Web Application"
                  className={errors.name ? 'border-red-500' : ''}
                />
                {errors.name && (
                  <p className="text-sm text-red-500 mt-1">{errors.name}</p>
                )}
              </div>

              <div>
                <Label htmlFor="primary_category_id">Primary Category *</Label>
                <Select
                  value={formData.primary_category_id}
                  onValueChange={(value) => handleInputChange('primary_category_id', value)}
                >
                  <SelectTrigger className={errors.primary_category_id ? 'border-red-500' : ''}>
                    <SelectValue placeholder="Select a category" />
                  </SelectTrigger>
                  <SelectContent>
                    {categories.map((category) => (
                      <SelectItem key={category.id} value={category.id}>
                        {category.category_name} ({category.category_code})
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                {errors.primary_category_id && (
                  <p className="text-sm text-red-500 mt-1">{errors.primary_category_id}</p>
                )}
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label htmlFor="product_code">Product Code *</Label>
                  <Input
                    id="product_code"
                    value={formData.product_code}
                    onChange={(e) => handleInputChange('product_code', e.target.value)}
                    placeholder="AUTO-GENERATED"
                    className={`font-mono text-sm ${errors.product_code ? 'border-red-500' : ''}`}
                  />
                  {errors.product_code && (
                    <p className="text-sm text-red-500 mt-1">{errors.product_code}</p>
                  )}
                </div>

                <div>
                  <Label htmlFor="squ_code">SQU Code *</Label>
                  <Input
                    id="squ_code"
                    value={formData.squ_code}
                    onChange={(e) => handleInputChange('squ_code', e.target.value)}
                    placeholder="AUTO-GENERATED"
                    className={`font-mono text-sm ${errors.squ_code ? 'border-red-500' : ''}`}
                  />
                  {errors.squ_code && (
                    <p className="text-sm text-red-500 mt-1">{errors.squ_code}</p>
                  )}
                </div>
              </div>

              <div>
                <Label htmlFor="unit">Unit *</Label>
                <Select
                  value={formData.unit}
                  onValueChange={(value) => handleInputChange('unit', value)}
                >
                  <SelectTrigger className={errors.unit ? 'border-red-500' : ''}>
                    <SelectValue placeholder="Select unit" />
                  </SelectTrigger>
                  <SelectContent>
                    {units.map((unit) => (
                      <SelectItem key={unit} value={unit}>
                        {unit}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                {errors.unit && (
                  <p className="text-sm text-red-500 mt-1">{errors.unit}</p>
                )}
              </div>

              <div>
                <Label htmlFor="description">Description</Label>
                <Textarea
                  id="description"
                  value={formData.description}
                  onChange={(e) => handleInputChange('description', e.target.value)}
                  placeholder="Describe this product..."
                  rows={3}
                />
              </div>

              <div className="flex items-center space-x-2">
                <input
                  type="checkbox"
                  id="is_active"
                  checked={formData.is_active}
                  onChange={(e) => handleInputChange('is_active', e.target.checked)}
                  className="w-4 h-4 text-green-600"
                />
                <Label htmlFor="is_active">Active</Label>
              </div>
            </div>

            <DialogFooter>
              <Button
                type="button"
                variant="outline"
                onClick={() => setIsDialogOpen(false)}
                disabled={saving}
              >
                Cancel
              </Button>
              <Button type="submit" disabled={saving}>
                {saving ? 'Saving...' : (isEditing ? 'Update' : 'Create')}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default ProductsManager;