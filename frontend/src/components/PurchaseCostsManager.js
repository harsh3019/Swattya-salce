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
  Calculator, 
  Search,
  Filter,
  Download,
  Upload,
  AlertCircle,
  CheckCircle,
  TrendingUp,
  DollarSign
} from 'lucide-react';
import axios from 'axios';

const PurchaseCostsManager = () => {
  const [purchaseCosts, setPurchaseCosts] = useState([]);
  const [products, setProducts] = useState([]);
  const [rateCards, setRateCards] = useState([]);
  const [salesPrices, setSalesPrices] = useState([]);
  const [loading, setLoading] = useState(true);
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [isEditing, setIsEditing] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedProduct, setSelectedProduct] = useState('all');
  const [formData, setFormData] = useState({
    product_id: '',
    purchase_cost: '',
    cost_type: 'standard',
    vendor: '',
    effective_date: '',
    notes: '',
    is_active: true
  });
  const [errors, setErrors] = useState({});
  const [saving, setSaving] = useState(false);
  const [marginInfo, setMarginInfo] = useState(null);

  const baseURL = process.env.REACT_APP_BACKEND_URL;

  const costTypes = ['standard', 'bulk', 'special', 'seasonal'];

  useEffect(() => {
    Promise.all([
      fetchPurchaseCosts(),
      fetchProducts(),
      fetchRateCards(),
      fetchSalesPrices()
    ]);
  }, []);

  const fetchPurchaseCosts = async () => {
    try {
      setLoading(true);
      const token = localStorage.getItem('token');
      const response = await axios.get(`${baseURL}/api/mst/purchase-costs`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setPurchaseCosts(response.data || []);
    } catch (error) {
      console.error('Error fetching purchase costs:', error);
      alert('Error fetching purchase costs. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const fetchProducts = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(`${baseURL}/api/mst/products`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setProducts(response.data || []);
    } catch (error) {
      console.error('Error fetching products:', error);
    }
  };

  const fetchRateCards = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(`${baseURL}/api/mst/rate-cards`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setRateCards(response.data || []);
    } catch (error) {
      console.error('Error fetching rate cards:', error);
    }
  };

  const fetchSalesPrices = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(`${baseURL}/api/mst/sales-prices`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setSalesPrices(response.data || []);
    } catch (error) {
      console.error('Error fetching sales prices:', error);
    }
  };

  const calculateMarginInfo = (productId, purchaseCost) => {
    if (!productId || !purchaseCost) return null;
    
    // Get standard rate card (first one or find by name)
    const standardRateCard = rateCards.find(card => 
      card.rate_card_name?.toLowerCase().includes('standard')
    ) || rateCards[0];
    
    if (!standardRateCard) return null;
    
    // Find sales price for this product in standard rate card
    const salesPrice = salesPrices.find(price => 
      price.product_id === productId && price.rate_card_id === standardRateCard.id
    );
    
    if (!salesPrice) return null;
    
    const margin = salesPrice.sales_price - purchaseCost;
    const marginPercent = (margin / salesPrice.sales_price) * 100;
    
    return {
      salesPrice: salesPrice.sales_price,
      purchaseCost: purchaseCost,
      margin: margin,
      marginPercent: marginPercent
    };
  };

  const handleInputChange = (field, value) => {
    setFormData(prev => ({
      ...prev,
      [field]: value
    }));
    
    // Calculate margin info when product or cost changes
    if (field === 'product_id' || field === 'purchase_cost') {
      const productId = field === 'product_id' ? value : formData.product_id;
      const cost = field === 'purchase_cost' ? parseFloat(value) : parseFloat(formData.purchase_cost);
      
      if (productId && cost) {
        setMarginInfo(calculateMarginInfo(productId, cost));
      } else {
        setMarginInfo(null);
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
    
    if (!formData.product_id) {
      newErrors.product_id = 'Product is required';
    }
    
    if (!formData.purchase_cost || formData.purchase_cost <= 0) {
      newErrors.purchase_cost = 'Valid purchase cost is required';
    }
    
    if (!formData.cost_type) {
      newErrors.cost_type = 'Cost type is required';
    }
    
    if (!formData.effective_date) {
      newErrors.effective_date = 'Effective date is required';
    }
    
    // Check for duplicate (same product + cost type)
    const existingCost = purchaseCosts.find(cost => 
      cost.product_id === formData.product_id &&
      cost.cost_type === formData.cost_type &&
      (!isEditing || cost.id !== formData.id)
    );
    if (existingCost) {
      newErrors.product_id = `${formData.cost_type} cost already exists for this product`;
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
        ? `${baseURL}/api/mst/purchase-costs/${formData.id}`
        : `${baseURL}/api/mst/purchase-costs`;
      
      const method = isEditing ? 'put' : 'post';
      
      const submitData = {
        ...formData,
        purchase_cost: parseFloat(formData.purchase_cost)
      };
      
      await axios[method](url, submitData, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      alert(`Purchase cost ${isEditing ? 'updated' : 'created'} successfully!`);
      setIsDialogOpen(false);
      resetForm();
      fetchPurchaseCosts();
    } catch (error) {
      console.error('Error saving purchase cost:', error);
      const errorMessage = error.response?.data?.detail || 'Error saving purchase cost. Please try again.';
      alert(errorMessage);
    } finally {
      setSaving(false);
    }
  };

  const handleEdit = (cost) => {
    const formatDate = (dateStr) => {
      if (!dateStr) return new Date().toISOString().split('T')[0];
      const date = new Date(dateStr);
      return date.toISOString().split('T')[0];
    };

    setFormData({
      id: cost.id,
      product_id: cost.product_id || '',
      purchase_cost: cost.purchase_cost?.toString() || '',
      cost_type: cost.cost_type || 'standard',
      vendor: cost.vendor || '',
      effective_date: formatDate(cost.effective_date),
      notes: cost.notes || '',
      is_active: cost.is_active !== false
    });
    setIsEditing(true);
    setIsDialogOpen(true);
    
    // Calculate margin info for editing
    if (cost.product_id && cost.purchase_cost) {
      setMarginInfo(calculateMarginInfo(cost.product_id, cost.purchase_cost));
    }
  };

  const handleDelete = async (cost) => {
    const productName = getProductName(cost.product_id);
    if (!window.confirm(`Are you sure you want to delete purchase cost for "${productName}"?`)) {
      return;
    }
    
    try {
      const token = localStorage.getItem('token');
      await axios.delete(`${baseURL}/api/mst/purchase-costs/${cost.id}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      alert('Purchase cost deleted successfully!');
      fetchPurchaseCosts();
    } catch (error) {
      console.error('Error deleting purchase cost:', error);
      alert('Error deleting purchase cost. Please try again.');
    }
  };

  const resetForm = () => {
    setFormData({
      product_id: '',
      purchase_cost: '',
      cost_type: 'standard',
      vendor: '',
      effective_date: new Date().toISOString().split('T')[0],
      notes: '',
      is_active: true
    });
    setIsEditing(false);
    setErrors({});
    setMarginInfo(null);
  };

  const openNewDialog = () => {
    resetForm();
    setIsDialogOpen(true);
  };

  const getProductName = (productId) => {
    const product = products.find(prod => prod.id === productId);
    return product?.name || 'Unknown Product';
  };

  const getProductSQU = (productId) => {
    const product = products.find(prod => prod.id === productId);
    return product?.squ_code || 'N/A';
  };

  const getMarginForCost = (cost) => {
    const marginInfo = calculateMarginInfo(cost.product_id, cost.purchase_cost);
    return marginInfo;
  };

  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0
    }).format(amount);
  };

  const filteredCosts = purchaseCosts.filter(cost => {
    const productName = getProductName(cost.product_id);
    const productSQU = getProductSQU(cost.product_id);
    
    const matchesSearch = 
      productName.toLowerCase().includes(searchTerm.toLowerCase()) ||
      productSQU.toLowerCase().includes(searchTerm.toLowerCase()) ||
      cost.vendor?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      cost.cost_type?.toLowerCase().includes(searchTerm.toLowerCase());
    
    const matchesProduct = selectedProduct === 'all' || cost.product_id === selectedProduct;
    
    return matchesSearch && matchesProduct;
  });

  return (
    <div className="container mx-auto p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <Calculator className="w-8 h-8 text-orange-600" />
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Purchase Costs</h1>
            <p className="text-gray-600">Manage product purchase costs and margins</p>
          </div>
        </div>
        <Button onClick={openNewDialog} className="flex items-center gap-2">
          <Plus className="w-4 h-4" />
          Add Purchase Cost
        </Button>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-6">
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Total Cost Records</p>
                <p className="text-2xl font-bold text-gray-900">{purchaseCosts.length}</p>
              </div>
              <Calculator className="w-8 h-8 text-orange-500" />
            </div>
          </CardContent>
        </Card>
        
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Products Covered</p>
                <p className="text-2xl font-bold text-blue-600">
                  {new Set(purchaseCosts.map(cost => cost.product_id)).size}
                </p>
              </div>
              <CheckCircle className="w-8 h-8 text-blue-500" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Avg Margin</p>
                <p className="text-2xl font-bold text-green-600">
                  {purchaseCosts.length > 0 ? (
                    (() => {
                      const validMargins = purchaseCosts
                        .map(cost => getMarginForCost(cost))
                        .filter(margin => margin)
                        .map(margin => margin.marginPercent);
                      const avgMargin = validMargins.length > 0 
                        ? validMargins.reduce((a, b) => a + b, 0) / validMargins.length 
                        : 0;
                      return `${avgMargin.toFixed(1)}%`;
                    })()
                  ) : '0%'}
                </p>
              </div>
              <TrendingUp className="w-8 h-8 text-green-500" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Total Value</p>
                <p className="text-2xl font-bold text-purple-600">
                  {formatCurrency(purchaseCosts.reduce((sum, cost) => sum + (cost.purchase_cost || 0), 0))}
                </p>
              </div>
              <DollarSign className="w-8 h-8 text-purple-500" />
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
                  placeholder="Search by product name, SQU code, vendor, or cost type..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="pl-10"
                />
              </div>
            </div>
            <div className="flex gap-2">
              <Select value={selectedProduct} onValueChange={setSelectedProduct}>
                <SelectTrigger className="w-48">
                  <SelectValue placeholder="Filter by product" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Products</SelectItem>
                  {products.map((product) => (
                    <SelectItem key={product.id} value={product.id}>
                      {product.name}
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

      {/* Purchase Costs Table */}
      <Card>
        <CardHeader>
          <CardTitle>Purchase Costs List ({filteredCosts.length})</CardTitle>
          <CardDescription>
            Manage purchase costs and monitor profit margins
          </CardDescription>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="flex justify-center py-8">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-orange-600"></div>
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Product</TableHead>
                  <TableHead>Cost Type</TableHead>
                  <TableHead className="text-right">Purchase Cost</TableHead>
                  <TableHead className="text-right hidden md:table-cell">Sales Price</TableHead>
                  <TableHead className="text-right hidden lg:table-cell">Margin</TableHead>
                  <TableHead className="hidden sm:table-cell">Vendor</TableHead>
                  <TableHead className="hidden sm:table-cell">Status</TableHead>
                  <TableHead className="text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {filteredCosts.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={8} className="text-center py-8 text-gray-500">
                      {searchTerm || selectedProduct !== 'all' 
                        ? 'No purchase costs found matching your criteria.' 
                        : 'No purchase costs found. Create your first purchase cost record!'}
                    </TableCell>
                  </TableRow>
                ) : (
                  filteredCosts.map((cost) => {
                    const marginInfo = getMarginForCost(cost);
                    return (
                      <TableRow key={cost.id}>
                        <TableCell className="font-medium">
                          <div>
                            <div className="font-medium">{getProductName(cost.product_id)}</div>
                            <div className="text-sm text-gray-500">
                              SQU: {getProductSQU(cost.product_id)}
                            </div>
                          </div>
                        </TableCell>
                        <TableCell>
                          <Badge variant="outline" className="capitalize">
                            {cost.cost_type}
                          </Badge>
                        </TableCell>
                        <TableCell className="text-right font-mono">
                          {formatCurrency(cost.purchase_cost)}
                        </TableCell>
                        <TableCell className="text-right font-mono hidden md:table-cell">
                          {marginInfo ? formatCurrency(marginInfo.salesPrice) : 'N/A'}
                        </TableCell>
                        <TableCell className="text-right hidden lg:table-cell">
                          {marginInfo ? (
                            <div>
                              <div className="font-medium">{marginInfo.marginPercent.toFixed(1)}%</div>
                              <div className="text-sm text-gray-500 font-mono">
                                {formatCurrency(marginInfo.margin)}
                              </div>
                            </div>
                          ) : (
                            'N/A'
                          )}
                        </TableCell>
                        <TableCell className="hidden sm:table-cell">
                          <span className="text-sm">{cost.vendor || 'N/A'}</span>
                        </TableCell>
                        <TableCell className="hidden sm:table-cell">
                          <Badge variant={cost.is_active !== false ? "success" : "destructive"}>
                            {cost.is_active !== false ? "Active" : "Inactive"}
                          </Badge>
                        </TableCell>
                        <TableCell className="text-right">
                          <div className="flex justify-end gap-2">
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => handleEdit(cost)}
                            >
                              <Edit className="w-4 h-4" />
                            </Button>
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => handleDelete(cost)}
                              className="text-red-600 hover:text-red-700"
                            >
                              <Trash2 className="w-4 h-4" />
                            </Button>
                          </div>
                        </TableCell>
                      </TableRow>
                    );
                  })
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
              {isEditing ? 'Edit Purchase Cost' : 'Add New Purchase Cost'}
            </DialogTitle>
            <DialogDescription>
              {isEditing 
                ? 'Update the purchase cost information below.' 
                : 'Create a new purchase cost record with margin calculation.'
              }
            </DialogDescription>
          </DialogHeader>
          
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="grid gap-4">
              <div>
                <Label htmlFor="product_id">Product *</Label>
                <Select
                  value={formData.product_id}
                  onValueChange={(value) => handleInputChange('product_id', value)}
                >
                  <SelectTrigger className={errors.product_id ? 'border-red-500' : ''}>
                    <SelectValue placeholder="Select a product" />
                  </SelectTrigger>
                  <SelectContent>
                    {products.map((product) => (
                      <SelectItem key={product.id} value={product.id}>
                        <div>
                          <div className="font-medium">{product.name}</div>
                          <div className="text-sm text-gray-500">SQU: {product.squ_code}</div>
                        </div>
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                {errors.product_id && (
                  <p className="text-sm text-red-500 mt-1">{errors.product_id}</p>
                )}
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label htmlFor="purchase_cost">Purchase Cost (₹) *</Label>
                  <Input
                    id="purchase_cost"
                    type="number"
                    min="0"
                    step="0.01"
                    value={formData.purchase_cost}
                    onChange={(e) => handleInputChange('purchase_cost', e.target.value)}
                    placeholder="0.00"
                    className={`font-mono ${errors.purchase_cost ? 'border-red-500' : ''}`}
                  />
                  {errors.purchase_cost && (
                    <p className="text-sm text-red-500 mt-1">{errors.purchase_cost}</p>
                  )}
                </div>

                <div>
                  <Label htmlFor="cost_type">Cost Type *</Label>
                  <Select
                    value={formData.cost_type}
                    onValueChange={(value) => handleInputChange('cost_type', value)}
                  >
                    <SelectTrigger className={errors.cost_type ? 'border-red-500' : ''}>
                      <SelectValue placeholder="Select cost type" />
                    </SelectTrigger>
                    <SelectContent>
                      {costTypes.map((type) => (
                        <SelectItem key={type} value={type}>
                          <span className="capitalize">{type}</span>
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                  {errors.cost_type && (
                    <p className="text-sm text-red-500 mt-1">{errors.cost_type}</p>
                  )}
                </div>
              </div>

              {/* Margin Information */}
              {marginInfo && (
                <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                  <h4 className="font-medium text-blue-900 mb-2">Margin Analysis</h4>
                  <div className="grid grid-cols-2 gap-4 text-sm">
                    <div>
                      <span className="text-gray-600">Sales Price:</span>
                      <span className="font-mono font-medium ml-2">
                        {formatCurrency(marginInfo.salesPrice)}
                      </span>
                    </div>
                    <div>
                      <span className="text-gray-600">Margin:</span>
                      <span className="font-mono font-medium ml-2">
                        {marginInfo.marginPercent.toFixed(1)}%
                      </span>
                    </div>
                    <div className="col-span-2">
                      <span className="text-gray-600">Profit:</span>
                      <span className="font-mono font-medium ml-2">
                        {formatCurrency(marginInfo.margin)}
                      </span>
                    </div>
                  </div>
                </div>
              )}

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label htmlFor="vendor">Vendor</Label>
                  <Input
                    id="vendor"
                    value={formData.vendor}
                    onChange={(e) => handleInputChange('vendor', e.target.value)}
                    placeholder="Vendor name"
                  />
                </div>

                <div>
                  <Label htmlFor="effective_date">Effective Date *</Label>
                  <Input
                    id="effective_date"
                    type="date"
                    value={formData.effective_date}
                    onChange={(e) => handleInputChange('effective_date', e.target.value)}
                    className={errors.effective_date ? 'border-red-500' : ''}
                  />
                  {errors.effective_date && (
                    <p className="text-sm text-red-500 mt-1">{errors.effective_date}</p>
                  )}
                </div>
              </div>

              <div>
                <Label htmlFor="notes">Notes</Label>
                <Textarea
                  id="notes"
                  value={formData.notes}
                  onChange={(e) => handleInputChange('notes', e.target.value)}
                  placeholder="Additional notes..."
                  rows={2}
                />
              </div>

              <div className="flex items-center space-x-2">
                <input
                  type="checkbox"
                  id="is_active"
                  checked={formData.is_active}
                  onChange={(e) => handleInputChange('is_active', e.target.checked)}
                  className="w-4 h-4 text-orange-600"
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

export default PurchaseCostsManager;