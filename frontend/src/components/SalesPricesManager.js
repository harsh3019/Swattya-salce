import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Label } from './ui/label';
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
  DollarSign, 
  Search,
  Filter,
  Download,
  Upload,
  AlertCircle,
  CheckCircle,
  Calculator,
  Package
} from 'lucide-react';
import axios from 'axios';

const SalesPricesManager = () => {
  const [salesPrices, setSalesPrices] = useState([]);
  const [rateCards, setRateCards] = useState([]);
  const [products, setProducts] = useState([]);
  const [purchaseCosts, setPurchaseCosts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [isEditing, setIsEditing] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedRateCard, setSelectedRateCard] = useState('all');
  const [selectedProduct, setSelectedProduct] = useState('all');
  const [formData, setFormData] = useState({
    rate_card_id: '',
    product_id: '',
    sales_price: '',
    pricing_type: 'one_time',
    effective_date: '',
    is_active: true
  });
  const [errors, setErrors] = useState({});
  const [saving, setSaving] = useState(false);
  const [marginInfo, setMarginInfo] = useState(null);

  const baseURL = process.env.REACT_APP_BACKEND_URL;

  const pricingTypes = ['one_time', 'recurring', 'subscription', 'usage_based'];

  useEffect(() => {
    Promise.all([
      fetchSalesPrices(),
      fetchRateCards(),
      fetchProducts(),
      fetchPurchaseCosts()
    ]);
  }, []);

  const fetchSalesPrices = async () => {
    try {
      setLoading(true);
      const token = localStorage.getItem('token');
      const response = await axios.get(`${baseURL}/api/mst/sales-prices`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setSalesPrices(response.data || []);
    } catch (error) {
      console.error('Error fetching sales prices:', error);
      alert('Error fetching sales prices. Please try again.');
    } finally {
      setLoading(false);
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

  const fetchPurchaseCosts = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(`${baseURL}/api/mst/purchase-costs`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setPurchaseCosts(response.data || []);
    } catch (error) {
      console.error('Error fetching purchase costs:', error);
    }
  };

  const calculateMarginInfo = (productId, salesPrice) => {
    if (!productId || !salesPrice) return null;
    
    // Find purchase cost for this product
    const purchaseCost = purchaseCosts.find(cost => 
      cost.product_id === productId && cost.cost_type === 'standard'
    );
    
    if (!purchaseCost) return null;
    
    const margin = salesPrice - purchaseCost.purchase_cost;
    const marginPercent = (margin / salesPrice) * 100;
    
    return {
      purchaseCost: purchaseCost.purchase_cost,
      salesPrice: salesPrice,
      margin: margin,
      marginPercent: marginPercent
    };
  };

  const handleInputChange = (field, value) => {
    setFormData(prev => ({
      ...prev,
      [field]: value
    }));
    
    // Calculate margin info when product or price changes
    if (field === 'product_id' || field === 'sales_price') {
      const productId = field === 'product_id' ? value : formData.product_id;
      const price = field === 'sales_price' ? parseFloat(value) : parseFloat(formData.sales_price);
      
      if (productId && price) {
        setMarginInfo(calculateMarginInfo(productId, price));
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
    
    if (!formData.rate_card_id) {
      newErrors.rate_card_id = 'Rate card is required';
    }
    
    if (!formData.product_id) {
      newErrors.product_id = 'Product is required';
    }
    
    if (!formData.sales_price || formData.sales_price <= 0) {
      newErrors.sales_price = 'Valid sales price is required';
    }
    
    if (!formData.pricing_type) {
      newErrors.pricing_type = 'Pricing type is required';
    }
    
    if (!formData.effective_date) {
      newErrors.effective_date = 'Effective date is required';
    }
    
    // Check for duplicate (same rate card + product)
    const existingPrice = salesPrices.find(price => 
      price.rate_card_id === formData.rate_card_id &&
      price.product_id === formData.product_id &&
      (!isEditing || price.id !== formData.id)
    );
    if (existingPrice) {
      newErrors.product_id = 'Price already exists for this product in this rate card';
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
        ? `${baseURL}/api/mst/sales-prices/${formData.id}`
        : `${baseURL}/api/mst/sales-prices`;
      
      const method = isEditing ? 'put' : 'post';
      
      const submitData = {
        ...formData,
        sales_price: parseFloat(formData.sales_price)
      };
      
      await axios[method](url, submitData, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      alert(`Sales price ${isEditing ? 'updated' : 'created'} successfully!`);
      setIsDialogOpen(false);
      resetForm();
      fetchSalesPrices();
    } catch (error) {
      console.error('Error saving sales price:', error);
      const errorMessage = error.response?.data?.detail || 'Error saving sales price. Please try again.';
      alert(errorMessage);
    } finally {
      setSaving(false);
    }
  };

  const handleEdit = (price) => {
    const formatDate = (dateStr) => {
      if (!dateStr) return new Date().toISOString().split('T')[0];
      const date = new Date(dateStr);
      return date.toISOString().split('T')[0];
    };

    setFormData({
      id: price.id,
      rate_card_id: price.rate_card_id || '',
      product_id: price.product_id || '',
      sales_price: price.sales_price?.toString() || '',
      pricing_type: price.pricing_type || 'one_time',
      effective_date: formatDate(price.effective_date),
      is_active: price.is_active !== false
    });
    setIsEditing(true);
    setIsDialogOpen(true);
    
    // Calculate margin info for editing
    if (price.product_id && price.sales_price) {
      setMarginInfo(calculateMarginInfo(price.product_id, price.sales_price));
    }
  };

  const handleDelete = async (price) => {
    const productName = getProductName(price.product_id);
    const rateCardName = getRateCardName(price.rate_card_id);
    if (!window.confirm(`Are you sure you want to delete sales price for "${productName}" in "${rateCardName}"?`)) {
      return;
    }
    
    try {
      const token = localStorage.getItem('token');
      await axios.delete(`${baseURL}/api/mst/sales-prices/${price.id}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      alert('Sales price deleted successfully!');
      fetchSalesPrices();
    } catch (error) {
      console.error('Error deleting sales price:', error);
      alert('Error deleting sales price. Please try again.');
    }
  };

  const resetForm = () => {
    setFormData({
      rate_card_id: '',
      product_id: '',
      sales_price: '',
      pricing_type: 'one_time',
      effective_date: new Date().toISOString().split('T')[0],
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

  const getRateCardName = (rateCardId) => {
    const rateCard = rateCards.find(card => card.id === rateCardId);
    return rateCard?.rate_card_name || 'Unknown Rate Card';
  };

  const getProductName = (productId) => {
    const product = products.find(prod => prod.id === productId);
    return product?.name || 'Unknown Product';
  };

  const getProductSQU = (productId) => {
    const product = products.find(prod => prod.id === productId);
    return product?.squ_code || 'N/A';
  };

  const getMarginForPrice = (price) => {
    const marginInfo = calculateMarginInfo(price.product_id, price.sales_price);
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

  const filteredPrices = salesPrices.filter(price => {
    const productName = getProductName(price.product_id);
    const productSQU = getProductSQU(price.product_id);
    const rateCardName = getRateCardName(price.rate_card_id);
    
    const matchesSearch = 
      productName.toLowerCase().includes(searchTerm.toLowerCase()) ||
      productSQU.toLowerCase().includes(searchTerm.toLowerCase()) ||
      rateCardName.toLowerCase().includes(searchTerm.toLowerCase()) ||
      price.pricing_type?.toLowerCase().includes(searchTerm.toLowerCase());
    
    const matchesRateCard = selectedRateCard === 'all' || price.rate_card_id === selectedRateCard;
    const matchesProduct = selectedProduct === 'all' || price.product_id === selectedProduct;
    
    return matchesSearch && matchesRateCard && matchesProduct;
  });

  // Bulk Price Setting Feature
  const handleBulkPriceSet = async (rateCardId) => {
    if (!window.confirm('Set prices for all products in this rate card?')) return;
    
    try {
      const token = localStorage.getItem('token');
      const baseMultiplier = rateCardId === 'premium' ? 1.5 : rateCardId === 'bulk' ? 0.8 : 1.0;
      
      for (const product of products) {
        const existingPrice = salesPrices.find(p => 
          p.rate_card_id === rateCardId && p.product_id === product.id
        );
        
        if (!existingPrice) {
          const purchaseCost = purchaseCosts.find(c => 
            c.product_id === product.id && c.cost_type === 'standard'
          );
          
          if (purchaseCost) {
            const basePrice = purchaseCost.purchase_cost * 1.5; // 50% markup
            const finalPrice = basePrice * baseMultiplier;
            
            const priceData = {
              rate_card_id: rateCardId,
              product_id: product.id,
              sales_price: finalPrice,
              pricing_type: 'one_time',
              effective_date: new Date().toISOString().split('T')[0],
              is_active: true
            };
            
            await axios.post(`${baseURL}/api/mst/sales-prices`, priceData, {
              headers: { Authorization: `Bearer ${token}` }
            });
          }
        }
      }
      
      alert('Bulk prices set successfully!');
      fetchSalesPrices();
    } catch (error) {
      console.error('Error setting bulk prices:', error);
      alert('Error setting bulk prices. Please try again.');
    }
  };

  return (
    <div className="container mx-auto p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <DollarSign className="w-8 h-8 text-green-600" />
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Sales Prices</h1>
            <p className="text-gray-600">Manage selling prices for products in rate cards</p>
          </div>
        </div>
        <div className="flex gap-2">
          <Button onClick={openNewDialog} className="flex items-center gap-2">
            <Plus className="w-4 h-4" />
            Add Sales Price
          </Button>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-6">
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Total Price Records</p>
                <p className="text-2xl font-bold text-gray-900">{salesPrices.length}</p>
              </div>
              <DollarSign className="w-8 h-8 text-green-500" />
            </div>
          </CardContent>
        </Card>
        
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Products Priced</p>
                <p className="text-2xl font-bold text-blue-600">
                  {new Set(salesPrices.map(price => price.product_id)).size}
                </p>
              </div>
              <Package className="w-8 h-8 text-blue-500" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Rate Cards</p>
                <p className="text-2xl font-bold text-purple-600">
                  {new Set(salesPrices.map(price => price.rate_card_id)).size}
                </p>
              </div>
              <Calculator className="w-8 h-8 text-purple-500" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Avg Price</p>
                <p className="text-2xl font-bold text-orange-600">
                  {salesPrices.length > 0 
                    ? formatCurrency(salesPrices.reduce((sum, price) => sum + (price.sales_price || 0), 0) / salesPrices.length)
                    : formatCurrency(0)
                  }
                </p>
              </div>
              <CheckCircle className="w-8 h-8 text-orange-500" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Quick Actions for Rate Cards */}
      <Card className="mb-6">
        <CardHeader>
          <CardTitle>Quick Actions by Rate Card</CardTitle>
          <CardDescription>Set prices for all products in a rate card</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {rateCards.map((rateCard) => (
              <div key={rateCard.id} className="border rounded-lg p-4">
                <div className="flex items-center justify-between mb-2">
                  <h4 className="font-medium">{rateCard.rate_card_name}</h4>
                  <Badge variant="outline">{rateCard.rate_card_code}</Badge>
                </div>
                <p className="text-sm text-gray-600 mb-3">
                  {salesPrices.filter(p => p.rate_card_id === rateCard.id).length} products priced
                </p>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => handleBulkPriceSet(rateCard.id)}
                  className="w-full"
                >
                  <Calculator className="w-4 h-4 mr-2" />
                  Set Bulk Prices
                </Button>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

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
                  placeholder="Search by product name, SQU code, rate card, or pricing type..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="pl-10"
                />
              </div>
            </div>
            <div className="flex gap-2">
              <Select value={selectedRateCard} onValueChange={setSelectedRateCard}>
                <SelectTrigger className="w-48">
                  <SelectValue placeholder="Filter by rate card" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Rate Cards</SelectItem>
                  {rateCards.map((rateCard) => (
                    <SelectItem key={rateCard.id} value={rateCard.id}>
                      {rateCard.rate_card_name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
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
                <Download className="w-4 h-4 mr-2" />
                Export
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Sales Prices Table */}
      <Card>
        <CardHeader>
          <CardTitle>Sales Prices List ({filteredPrices.length})</CardTitle>
          <CardDescription>
            Manage selling prices with margin analysis
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
                  <TableHead>Product</TableHead>
                  <TableHead>Rate Card</TableHead>
                  <TableHead className="text-right">Sales Price</TableHead>
                  <TableHead className="text-right hidden lg:table-cell">Purchase Cost</TableHead>
                  <TableHead className="text-right hidden lg:table-cell">Margin</TableHead>
                  <TableHead className="hidden md:table-cell">Type</TableHead>
                  <TableHead className="hidden sm:table-cell">Status</TableHead>
                  <TableHead className="text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {filteredPrices.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={8} className="text-center py-8 text-gray-500">
                      {searchTerm || selectedRateCard !== 'all' || selectedProduct !== 'all' 
                        ? 'No sales prices found matching your criteria.' 
                        : 'No sales prices found. Create your first sales price!'}
                    </TableCell>
                  </TableRow>
                ) : (
                  filteredPrices.map((price) => {
                    const marginInfo = getMarginForPrice(price);
                    return (
                      <TableRow key={price.id}>
                        <TableCell className="font-medium">
                          <div>
                            <div className="font-medium">{getProductName(price.product_id)}</div>
                            <div className="text-sm text-gray-500">
                              SQU: {getProductSQU(price.product_id)}
                            </div>
                          </div>
                        </TableCell>
                        <TableCell>
                          <Badge variant="secondary" className="text-xs">
                            {getRateCardName(price.rate_card_id)}
                          </Badge>
                        </TableCell>
                        <TableCell className="text-right font-mono font-bold text-green-600">
                          {formatCurrency(price.sales_price)}
                        </TableCell>
                        <TableCell className="text-right font-mono hidden lg:table-cell">
                          {marginInfo ? formatCurrency(marginInfo.purchaseCost) : 'N/A'}
                        </TableCell>
                        <TableCell className="text-right hidden lg:table-cell">
                          {marginInfo ? (
                            <div>
                              <div className={`font-medium ${marginInfo.marginPercent > 0 ? 'text-green-600' : 'text-red-600'}`}>
                                {marginInfo.marginPercent.toFixed(1)}%
                              </div>
                              <div className="text-sm text-gray-500 font-mono">
                                {formatCurrency(marginInfo.margin)}
                              </div>
                            </div>
                          ) : (
                            'N/A'
                          )}
                        </TableCell>
                        <TableCell className="hidden md:table-cell">
                          <Badge variant="outline" className="capitalize">
                            {price.pricing_type?.replace('_', ' ')}
                          </Badge>
                        </TableCell>
                        <TableCell className="hidden sm:table-cell">
                          <Badge variant={price.is_active !== false ? "success" : "destructive"}>
                            {price.is_active !== false ? "Active" : "Inactive"}
                          </Badge>
                        </TableCell>
                        <TableCell className="text-right">
                          <div className="flex justify-end gap-2">
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => handleEdit(price)}
                            >
                              <Edit className="w-4 h-4" />
                            </Button>
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => handleDelete(price)}
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
              {isEditing ? 'Edit Sales Price' : 'Add New Sales Price'}
            </DialogTitle>
            <DialogDescription>
              {isEditing 
                ? 'Update the sales price information below.' 
                : 'Create a new sales price for a product in a rate card.'
              }
            </DialogDescription>
          </DialogHeader>
          
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="grid gap-4">
              <div>
                <Label htmlFor="rate_card_id">Rate Card *</Label>
                <Select
                  value={formData.rate_card_id}
                  onValueChange={(value) => handleInputChange('rate_card_id', value)}
                >
                  <SelectTrigger className={errors.rate_card_id ? 'border-red-500' : ''}>
                    <SelectValue placeholder="Select a rate card" />
                  </SelectTrigger>
                  <SelectContent>
                    {rateCards.map((rateCard) => (
                      <SelectItem key={rateCard.id} value={rateCard.id}>
                        {rateCard.rate_card_name} ({rateCard.rate_card_code})
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                {errors.rate_card_id && (
                  <p className="text-sm text-red-500 mt-1">{errors.rate_card_id}</p>
                )}
              </div>

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
                  <Label htmlFor="sales_price">Sales Price (₹) *</Label>
                  <Input
                    id="sales_price"
                    type="number"
                    min="0"
                    step="0.01"
                    value={formData.sales_price}
                    onChange={(e) => handleInputChange('sales_price', e.target.value)}
                    placeholder="0.00"
                    className={`font-mono ${errors.sales_price ? 'border-red-500' : ''}`}
                  />
                  {errors.sales_price && (
                    <p className="text-sm text-red-500 mt-1">{errors.sales_price}</p>
                  )}
                </div>

                <div>
                  <Label htmlFor="pricing_type">Pricing Type *</Label>
                  <Select
                    value={formData.pricing_type}
                    onValueChange={(value) => handleInputChange('pricing_type', value)}
                  >
                    <SelectTrigger className={errors.pricing_type ? 'border-red-500' : ''}>
                      <SelectValue placeholder="Select pricing type" />
                    </SelectTrigger>
                    <SelectContent>
                      {pricingTypes.map((type) => (
                        <SelectItem key={type} value={type}>
                          <span className="capitalize">{type.replace('_', ' ')}</span>
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                  {errors.pricing_type && (
                    <p className="text-sm text-red-500 mt-1">{errors.pricing_type}</p>
                  )}
                </div>
              </div>

              {/* Margin Information */}
              {marginInfo && (
                <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                  <h4 className="font-medium text-green-900 mb-2">Margin Analysis</h4>
                  <div className="grid grid-cols-2 gap-4 text-sm">
                    <div>
                      <span className="text-gray-600">Purchase Cost:</span>
                      <span className="font-mono font-medium ml-2">
                        {formatCurrency(marginInfo.purchaseCost)}
                      </span>
                    </div>
                    <div>
                      <span className="text-gray-600">Margin:</span>
                      <span className={`font-mono font-medium ml-2 ${marginInfo.marginPercent > 0 ? 'text-green-600' : 'text-red-600'}`}>
                        {marginInfo.marginPercent.toFixed(1)}%
                      </span>
                    </div>
                    <div className="col-span-2">
                      <span className="text-gray-600">Profit:</span>
                      <span className={`font-mono font-medium ml-2 ${marginInfo.margin > 0 ? 'text-green-600' : 'text-red-600'}`}>
                        {formatCurrency(marginInfo.margin)}
                      </span>
                    </div>
                  </div>
                </div>
              )}

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

export default SalesPricesManager;