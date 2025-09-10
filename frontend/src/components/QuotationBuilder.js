import React, { useState, useEffect, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import { 
  ArrowLeft, 
  Plus, 
  Trash2, 
  Calculator, 
  FileText, 
  Package,
  Layers,
  DollarSign,
  TrendingUp,
  Save,
  Eye
} from 'lucide-react';
import { usePermissions } from '../contexts/PermissionContext';
import axios from 'axios';

const QuotationBuilder = () => {
  const { opportunityId, quotationId } = useParams();
  const navigate = useNavigate();
  const { permissions } = usePermissions();
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState(null);

  // Form data
  const [quotationData, setQuotationData] = useState({
    quotation_name: '',
    rate_card_id: '',
    validity_date: '',
    phases: []
  });

  // Master data
  const [opportunity, setOpportunity] = useState(null);
  const [rateCards, setRateCards] = useState([]);
  const [products, setProducts] = useState([]);
  const [currencies, setCurrencies] = useState([]);
  const [salesPrices, setSalesPrices] = useState([]);
  const [primaryCategories, setPrimaryCategories] = useState([]);

  // Totals
  const [totals, setTotals] = useState({
    total_recurring: 0,
    total_one_time: 0,
    grand_total: 0,
    total_cost: 0,
    profitability_percent: 0
  });

  const baseURL = process.env.REACT_APP_BACKEND_URL;

  useEffect(() => {
    fetchData();
  }, [opportunityId, quotationId]);

  useEffect(() => {
    calculateTotals();
  }, [quotationData.phases]);

  const fetchData = async () => {
    try {
      setLoading(true);
      setError(null);
      const token = localStorage.getItem('token');

      // Fetch opportunity details
      const opportunityRes = await axios.get(`${baseURL}/api/opportunities/${opportunityId}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setOpportunity(opportunityRes.data);

      // Fetch master data
      const [rateCardsRes, productsRes, currenciesRes, primaryCategoriesRes] = await Promise.all([
        axios.get(`${baseURL}/api/mst/rate-cards`, { headers: { Authorization: `Bearer ${token}` }}),
        axios.get(`${baseURL}/api/mst/products`, { headers: { Authorization: `Bearer ${token}` }}),
        axios.get(`${baseURL}/api/mst/currencies`, { headers: { Authorization: `Bearer ${token}` }}),
        axios.get(`${baseURL}/api/mst/primary-categories`, { headers: { Authorization: `Bearer ${token}` }})
      ]);

      setRateCards(rateCardsRes.data || []);
      setProducts(productsRes.data || []);
      setCurrencies(currenciesRes.data || []);
      setPrimaryCategories(primaryCategoriesRes.data || []);

      // If editing existing quotation, fetch quotation data
      if (quotationId && quotationId !== 'create') {
        const quotationRes = await axios.get(`${baseURL}/api/opportunities/${opportunityId}/quotations/${quotationId}`, {
          headers: { Authorization: `Bearer ${token}` }
        });
        setQuotationData(quotationRes.data);
        
        // Fetch sales prices for the existing rate card
        if (quotationRes.data.rate_card_id) {
          await fetchSalesPrices(quotationRes.data.rate_card_id);
        }
      } else {
        // Initialize with default structure
        initializeDefaultStructure();
      }
    } catch (error) {
      console.error('Error fetching data:', error);
      setError('Failed to fetch quotation data');
    } finally {
      setLoading(false);
    }
  };

  const fetchSalesPrices = async (rateCardId) => {
    if (!rateCardId) return;
    
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(`${baseURL}/api/mst/sales-prices/${rateCardId}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setSalesPrices(response.data || []);
    } catch (error) {
      console.error('Error fetching sales prices:', error);
      setSalesPrices([]);
    }
  };

  const initializeDefaultStructure = () => {
    const defaultDate = new Date();
    defaultDate.setMonth(defaultDate.getMonth() + 1);

    setQuotationData({
      quotation_name: `Quotation for ${opportunity?.project_title || 'Opportunity'}`,
      rate_card_id: rateCards[0]?.id || '',
      validity_date: defaultDate.toISOString().split('T')[0],
      phases: [
        {
          id: generateId(),
          phase_name: 'Phase 1 - Setup & Configuration',
          phase_order: 1,
          start_date: '',
          tenure_months: 12,
          groups: [
            {
              id: generateId(),
              group_name: 'Software Licenses',
              group_order: 1,
              items: []
            }
          ]
        }
      ]
    });
  };

  const generateId = () => {
    return Date.now().toString() + Math.random().toString(36).substr(2, 9);
  };

  const addPhase = () => {
    const newPhase = {
      id: generateId(),
      phase_name: `Phase ${quotationData.phases.length + 1}`,
      phase_order: quotationData.phases.length + 1,
      start_date: '',
      tenure_months: 12,
      groups: []
    };
    setQuotationData(prev => ({
      ...prev,
      phases: [...prev.phases, newPhase]
    }));
  };

  const addGroup = useCallback((phaseIndex, event) => {
    event?.preventDefault();
    event?.stopPropagation();
    
    // Prevent rapid consecutive clicks
    const now = Date.now();
    if (window.lastGroupAddTime && (now - window.lastGroupAddTime) < 500) {
      return;
    }
    window.lastGroupAddTime = now;
    
    setQuotationData(prev => {
      const currentGroupsCount = prev.phases[phaseIndex]?.groups?.length || 0;
      const newGroup = {
        id: generateId(),
        group_name: `Group ${currentGroupsCount + 1}`,
        group_order: currentGroupsCount + 1,
        primary_category_id: '',
        items: []
      };
      
      const updatedPhases = [...prev.phases];
      updatedPhases[phaseIndex].groups.push(newGroup);
      return { ...prev, phases: updatedPhases };
    });
  }, []);

  const addItem = useCallback((phaseIndex, groupIndex, event) => {
    event?.preventDefault();
    event?.stopPropagation();
    
    // Prevent rapid consecutive clicks
    const now = Date.now();
    if (window.lastItemAddTime && (now - window.lastItemAddTime) < 500) {
      return;
    }
    window.lastItemAddTime = now;

    setQuotationData(prev => {
      const currentItemsCount = prev.phases[phaseIndex]?.groups[groupIndex]?.items?.length || 0;
      const newItem = {
        id: generateId(),
        product_id: '',
        qty: 1,
        unit: 'License',
        recurring_sale_price: 0,
        one_time_sale_price: 0,
        purchase_cost_snapshot: 0,
        tenure_months: 12,
        total_recurring: 0,
        total_one_time: 0,
        total_cost: 0
      };

      const updatedPhases = [...prev.phases];
      updatedPhases[phaseIndex].groups[groupIndex].items.push(newItem);
      return { ...prev, phases: updatedPhases };
    });
  }, []);

  const getProductPricing = (productId) => {
    const salesPrice = salesPrices.find(sp => sp.product_id === productId);
    const product = products.find(p => p.id === productId);
    
    return {
      recurring_sale_price: salesPrice?.recurring_sale_price || 0,
      one_time_sale_price: salesPrice?.one_time_sale_price || 0,
      purchase_cost_snapshot: salesPrice?.purchase_cost || 0,
      unit: product?.unit || 'License'
    };
  };

  const getFilteredProducts = (primaryCategoryId) => {
    if (!primaryCategoryId) return [];
    return products.filter(product => product.primary_category_id === primaryCategoryId);
  };

  const updateItem = (phaseIndex, groupIndex, itemIndex, field, value) => {
    setQuotationData(prev => {
      const updatedPhases = [...prev.phases];
      const item = updatedPhases[phaseIndex].groups[groupIndex].items[itemIndex];
      
      // If product is being changed, auto-populate pricing
      if (field === 'product_id' && value) {
        const pricing = getProductPricing(value);
        item.product_id = value;
        item.recurring_sale_price = pricing.recurring_sale_price;
        item.one_time_sale_price = pricing.one_time_sale_price;
        item.purchase_cost_snapshot = pricing.purchase_cost_snapshot;
        item.unit = pricing.unit;
      } else {
        item[field] = value;
      }
      
      // Recalculate item totals
      const qty = parseFloat(item.qty) || 0;
      const tenure = parseFloat(item.tenure_months) || 1;
      
      item.total_recurring = (parseFloat(item.recurring_sale_price) || 0) * qty * tenure;
      item.total_one_time = (parseFloat(item.one_time_sale_price) || 0) * qty;
      item.total_cost = (parseFloat(item.purchase_cost_snapshot) || 0) * qty * tenure;

      return { ...prev, phases: updatedPhases };
    });
  };

  const removeItem = (phaseIndex, groupIndex, itemIndex) => {
    setQuotationData(prev => {
      const updatedPhases = [...prev.phases];
      updatedPhases[phaseIndex].groups[groupIndex].items.splice(itemIndex, 1);
      return { ...prev, phases: updatedPhases };
    });
  };

  const removeGroup = (phaseIndex, groupIndex) => {
    setQuotationData(prev => {
      const updatedPhases = [...prev.phases];
      updatedPhases[phaseIndex].groups.splice(groupIndex, 1);
      return { ...prev, phases: updatedPhases };
    });
  };

  const removePhase = (phaseIndex) => {
    setQuotationData(prev => ({
      ...prev,
      phases: prev.phases.filter((_, index) => index !== phaseIndex)
    }));
  };

  const calculateTotals = () => {
    let totalRecurring = 0;
    let totalOneTime = 0;
    let totalCost = 0;

    quotationData.phases.forEach(phase => {
      phase.groups.forEach(group => {
        group.items.forEach(item => {
          totalRecurring += item.total_recurring || 0;
          totalOneTime += item.total_one_time || 0;
          totalCost += item.total_cost || 0;
        });
      });
    });

    const grandTotal = totalRecurring + totalOneTime;
    const profitabilityPercent = grandTotal > 0 ? ((grandTotal - totalCost) / grandTotal) * 100 : 0;

    setTotals({
      total_recurring: totalRecurring,
      total_one_time: totalOneTime,
      grand_total: grandTotal,
      total_cost: totalCost,
      profitability_percent: profitabilityPercent
    });
  };

  const handleSave = async (isDraft = true) => {
    try {
      setSaving(true);
      const token = localStorage.getItem('token');

      const quotationPayload = {
        ...quotationData,
        ...totals
      };

      let response;
      if (quotationId && quotationId !== 'create') {
        // Update existing quotation
        response = await axios.put(`${baseURL}/api/opportunities/${opportunityId}/quotations/${quotationId}`, quotationPayload, {
          headers: { Authorization: `Bearer ${token}` }
        });
      } else {
        // Create new quotation
        response = await axios.post(`${baseURL}/api/opportunities/${opportunityId}/quotations`, quotationPayload, {
          headers: { Authorization: `Bearer ${token}` }
        });
      }

      alert(isDraft ? 'Quotation saved as draft!' : 'Quotation saved successfully!');
      navigate(`/opportunities/${opportunityId}`);
    } catch (error) {
      console.error('Error saving quotation:', error);
      alert('Error saving quotation. Please try again.');
    } finally {
      setSaving(false);
    }
  };

  const formatCurrency = (amount) => {
    return `₹${Number(amount).toLocaleString('en-IN')}`;
  };

  const getProfitabilityColor = (percentage) => {
    if (percentage >= 50) return 'text-green-600';
    if (percentage >= 25) return 'text-yellow-600';
    if (percentage >= 0) return 'text-orange-600';
    return 'text-red-600';
  };

  if (loading) {
    return (
      <div className="container mx-auto p-6">
        <div className="flex justify-center items-center h-64">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        </div>
      </div>
    );
  }

  if (error || !opportunity) {
    return (
      <div className="container mx-auto p-6">
        <div className="text-center py-12">
          <h2 className="text-2xl font-bold text-gray-900 mb-2">Error Loading Quotation</h2>
          <p className="text-gray-600 mb-4">{error || 'Unable to load quotation data'}</p>
          <Button onClick={() => navigate(`/opportunities/${opportunityId}`)} variant="outline">
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back to Opportunity
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className="container mx-auto p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-4">
          <Button 
            variant="ghost" 
            size="sm" 
            onClick={() => navigate(`/opportunities/${opportunityId}`)}
            className="text-gray-600"
          >
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back to Opportunity
          </Button>
          <div>
            <h1 className="text-3xl font-bold text-gray-900">
              {quotationId === 'create' ? 'Create Quotation' : 'Edit Quotation'}
            </h1>
            <p className="text-gray-600 mt-1">
              {opportunity.project_title} • {opportunity.opportunity_id}
            </p>
          </div>
        </div>
        <div className="flex items-center space-x-2">
          <Button 
            variant="outline" 
            onClick={() => handleSave(true)}
            disabled={saving}
          >
            <Save className="w-4 h-4 mr-2" />
            Save Draft
          </Button>
          <Button 
            onClick={() => handleSave(false)}
            disabled={saving}
            className="bg-blue-600 hover:bg-blue-700"
          >
            <FileText className="w-4 h-4 mr-2" />
            {saving ? 'Saving...' : 'Save Quotation'}
          </Button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* Main Content */}
        <div className="lg:col-span-3">
          {/* Basic Information */}
          <Card className="mb-6">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <FileText className="w-5 h-5" />
                Quotation Details
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <Label htmlFor="quotation_name">Quotation Name</Label>
                  <Input
                    id="quotation_name"
                    value={quotationData.quotation_name}
                    onChange={(e) => setQuotationData(prev => ({...prev, quotation_name: e.target.value}))}
                    placeholder="Enter quotation name"
                  />
                </div>
                <div>
                  <Label htmlFor="rate_card_id">Rate Card</Label>
                  <Select 
                    value={quotationData.rate_card_id} 
                    onValueChange={(value) => {
                      setQuotationData(prev => ({...prev, rate_card_id: value}));
                      fetchSalesPrices(value);
                    }}
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="Select rate card" />
                    </SelectTrigger>
                    <SelectContent>
                      {rateCards.map((card) => (
                        <SelectItem key={card.id} value={card.id}>
                          {card.name}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div>
                  <Label htmlFor="validity_date">Valid Until</Label>
                  <Input
                    id="validity_date"
                    type="date"
                    value={quotationData.validity_date}
                    onChange={(e) => setQuotationData(prev => ({...prev, validity_date: e.target.value}))}
                  />
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Phases */}
          <div className="space-y-6">
            {quotationData.phases.map((phase, phaseIndex) => (
              <Card key={phase.id} className="border-l-4 border-l-blue-500">
                <CardHeader>
                  <div className="flex justify-between items-center mb-3">
                    <CardTitle className="flex items-center gap-2">
                      <Layers className="w-5 h-5 text-blue-600" />
                      <Input
                        value={phase.phase_name}
                        onChange={(e) => {
                          setQuotationData(prev => {
                            const updatedPhases = [...prev.phases];
                            updatedPhases[phaseIndex].phase_name = e.target.value;
                            return { ...prev, phases: updatedPhases };
                          });
                        }}
                        className="text-lg font-semibold border-none p-0 h-auto"
                      />
                    </CardTitle>
                    <div className="flex gap-2">
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={(e) => addGroup(phaseIndex, e)}
                      >
                        <Plus className="w-4 h-4 mr-1" />
                        Add Group
                      </Button>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => removePhase(phaseIndex)}
                        className="text-red-600 hover:text-red-700"
                      >
                        <Trash2 className="w-4 h-4" />
                      </Button>
                    </div>
                  </div>
                  
                  {/* Phase Timeline Details */}
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-3 border-t border-gray-100">
                    <div>
                      <Label className="text-sm font-medium text-gray-600">Start Date</Label>
                      <Input
                        type="date"
                        value={phase.start_date}
                        onChange={(e) => {
                          setQuotationData(prev => {
                            const updatedPhases = [...prev.phases];
                            updatedPhases[phaseIndex].start_date = e.target.value;
                            return { ...prev, phases: updatedPhases };
                          });
                        }}
                        className="mt-1"
                      />
                    </div>
                    <div>
                      <Label className="text-sm font-medium text-gray-600">Tenure (Months)</Label>
                      <Input
                        type="number"
                        min="1"
                        value={phase.tenure_months}
                        onChange={(e) => {
                          setQuotationData(prev => {
                            const updatedPhases = [...prev.phases];
                            updatedPhases[phaseIndex].tenure_months = parseInt(e.target.value) || 1;
                            return { ...prev, phases: updatedPhases };
                          });
                        }}
                        className="mt-1"
                        placeholder="12"
                      />
                    </div>
                  </div>
                </CardHeader>
                <CardContent>
                  {/* Groups */}
                  <div className="space-y-4">
                    {phase.groups.map((group, groupIndex) => (
                      <Card key={group.id} className="border border-gray-200">
                        <CardHeader className="pb-3">
                          <div className="flex justify-between items-center mb-3">
                            <CardTitle className="text-md flex items-center gap-2">
                              <Package className="w-4 h-4 text-gray-600" />
                              <Input
                                value={group.group_name}
                                onChange={(e) => {
                                  setQuotationData(prev => {
                                    const updatedPhases = [...prev.phases];
                                    updatedPhases[phaseIndex].groups[groupIndex].group_name = e.target.value;
                                    return { ...prev, phases: updatedPhases };
                                  });
                                }}
                                className="text-md font-semibold border-none p-0 h-auto"
                              />
                            </CardTitle>
                            <div className="flex gap-2">
                              <Button
                                variant="outline"
                                size="sm"
                                onClick={(e) => addItem(phaseIndex, groupIndex, e)}
                                disabled={!group.primary_category_id}
                              >
                                <Plus className="w-4 h-4 mr-1" />
                                Add Item
                              </Button>
                              <Button
                                variant="outline"
                                size="sm"
                                onClick={() => removeGroup(phaseIndex, groupIndex)}
                                className="text-red-600 hover:text-red-700"
                              >
                                <Trash2 className="w-4 h-4" />
                              </Button>
                            </div>
                          </div>
                          
                          {/* Primary Category Selection */}
                          <div className="border-t pt-3">
                            <Label className="text-sm font-medium text-gray-600">Primary Category</Label>
                            <Select 
                              value={group.primary_category_id} 
                              onValueChange={(value) => {
                                setQuotationData(prev => {
                                  const updatedPhases = [...prev.phases];
                                  updatedPhases[phaseIndex].groups[groupIndex].primary_category_id = value;
                                  // Clear existing items when category changes
                                  updatedPhases[phaseIndex].groups[groupIndex].items = [];
                                  return { ...prev, phases: updatedPhases };
                                });
                              }}
                            >
                              <SelectTrigger className="mt-1">
                                <SelectValue placeholder="Select primary category" />
                              </SelectTrigger>
                              <SelectContent>
                                {primaryCategories.map((category) => (
                                  <SelectItem key={category.id} value={category.id}>
                                    {category.name}
                                  </SelectItem>
                                ))}
                              </SelectContent>
                            </Select>
                          </div>
                        </CardHeader>
                        <CardContent>
                          {/* Items */}
                          <div className="space-y-3">
                            {group.items.map((item, itemIndex) => (
                              <div key={item.id} className="border border-gray-100 rounded p-4">
                                <div className="grid grid-cols-1 md:grid-cols-7 gap-3">
                                  <div>
                                    <Label className="text-xs">Product</Label>
                                    <Select 
                                      value={item.product_id} 
                                      onValueChange={(value) => updateItem(phaseIndex, groupIndex, itemIndex, 'product_id', value)}
                                    >
                                      <SelectTrigger className="h-8">
                                        <SelectValue placeholder="Select" />
                                      </SelectTrigger>
                                      <SelectContent>
                                        {getFilteredProducts(group.primary_category_id).map((product) => (
                                          <SelectItem key={product.id} value={product.id}>
                                            {product.name}
                                          </SelectItem>
                                        ))}
                                      </SelectContent>
                                    </Select>
                                  </div>
                                  <div>
                                    <Label className="text-xs">Qty</Label>
                                    <Input
                                      type="number"
                                      className="h-8"
                                      value={item.qty}
                                      onChange={(e) => updateItem(phaseIndex, groupIndex, itemIndex, 'qty', e.target.value)}
                                    />
                                  </div>
                                  <div>
                                    <Label className="text-xs">Unit</Label>
                                    <Input
                                      className="h-8 bg-gray-50"
                                      value={item.unit}
                                      disabled
                                      placeholder="Auto-filled from product"
                                    />
                                  </div>
                                  <div>
                                    <Label className="text-xs">Recurring Price</Label>
                                    <Input
                                      type="number"
                                      className="h-8 bg-gray-50"
                                      value={item.recurring_sale_price}
                                      disabled
                                      placeholder="Auto-filled from rate card"
                                    />
                                  </div>
                                  <div>
                                    <Label className="text-xs">One-time Price</Label>
                                    <Input
                                      type="number"
                                      className="h-8 bg-gray-50"
                                      value={item.one_time_sale_price}
                                      disabled
                                      placeholder="Auto-filled from rate card"
                                    />
                                  </div>
                                  <div>
                                    <Label className="text-xs">Cost</Label>
                                    <Input
                                      type="number"
                                      className="h-8 bg-gray-50"
                                      value={item.purchase_cost_snapshot}
                                      disabled
                                      placeholder="Auto-filled from rate card"
                                    />
                                  </div>
                                  <div className="flex items-end">
                                    <Button
                                      variant="outline"
                                      size="sm"
                                      onClick={() => removeItem(phaseIndex, groupIndex, itemIndex)}
                                      className="h-8 text-red-600 hover:text-red-700"
                                    >
                                      <Trash2 className="w-4 h-4" />
                                    </Button>
                                  </div>
                                </div>
                                <div className="grid grid-cols-3 gap-3 mt-2 text-sm">
                                  <div>
                                    <span className="text-gray-600">Total Recurring: </span>
                                    <span className="font-medium">{formatCurrency(item.total_recurring)}</span>
                                  </div>
                                  <div>
                                    <span className="text-gray-600">Total One-time: </span>
                                    <span className="font-medium">{formatCurrency(item.total_one_time)}</span>
                                  </div>
                                  <div>
                                    <span className="text-gray-600">Total Cost: </span>
                                    <span className="font-medium">{formatCurrency(item.total_cost)}</span>
                                  </div>
                                </div>
                              </div>
                            ))}
                            {group.items.length === 0 && (
                              <div className="text-center py-8 text-gray-500">
                                <Package className="w-8 h-8 mx-auto mb-2 text-gray-400" />
                                <p>No items in this group</p>
                                <Button
                                  variant="outline"
                                  size="sm"
                                  onClick={(e) => addItem(phaseIndex, groupIndex, e)}
                                  className="mt-2"
                                >
                                  <Plus className="w-4 h-4 mr-1" />
                                  Add First Item
                                </Button>
                              </div>
                            )}
                          </div>
                        </CardContent>
                      </Card>
                    ))}
                    {phase.groups.length === 0 && (
                      <div className="text-center py-8 text-gray-500 border-2 border-dashed border-gray-200 rounded">
                        <Layers className="w-8 h-8 mx-auto mb-2 text-gray-400" />
                        <p>No groups in this phase</p>
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={(e) => addGroup(phaseIndex, e)}
                          className="mt-2"
                        >
                          <Plus className="w-4 h-4 mr-1" />
                          Add First Group
                        </Button>
                      </div>
                    )}
                  </div>
                </CardContent>
              </Card>
            ))}
            
            <Button 
              variant="outline" 
              onClick={addPhase}
              className="w-full border-dashed border-2"
            >
              <Plus className="w-4 h-4 mr-2" />
              Add New Phase
            </Button>
          </div>
        </div>

        {/* Sidebar - Totals & Summary */}
        <div className="lg:col-span-1">
          <Card className="sticky top-6">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Calculator className="w-5 h-5" />
                Live Totals
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-3">
                <div className="flex justify-between">
                  <span className="text-sm text-gray-600">Recurring Revenue</span>
                  <span className="font-semibold text-blue-600">
                    {formatCurrency(totals.total_recurring)}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm text-gray-600">One-time Revenue</span>
                  <span className="font-semibold text-green-600">
                    {formatCurrency(totals.total_one_time)}
                  </span>
                </div>
                <Separator />
                <div className="flex justify-between">
                  <span className="text-sm font-medium">Grand Total</span>
                  <span className="text-lg font-bold text-purple-600">
                    {formatCurrency(totals.grand_total)}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm text-gray-600">Total Cost</span>
                  <span className="font-semibold text-red-600">
                    {formatCurrency(totals.total_cost)}
                  </span>
                </div>
                <Separator />
                <div className="flex justify-between items-center">
                  <span className="text-sm font-medium">Profitability</span>
                  <div className="text-right">
                    <div className={`text-lg font-bold ${getProfitabilityColor(totals.profitability_percent)}`}>
                      {totals.profitability_percent.toFixed(1)}%
                    </div>
                    <div className="text-xs text-gray-500">
                      {formatCurrency(totals.grand_total - totals.total_cost)} profit
                    </div>
                  </div>
                </div>
              </div>

              <Separator />

              <div className="space-y-2">
                <h4 className="text-sm font-medium text-gray-900">Quick Actions</h4>
                <div className="space-y-2">
                  <Button 
                    variant="outline" 
                    size="sm" 
                    className="w-full"
                    onClick={() => handleSave(true)}
                    disabled={saving}
                  >
                    <Save className="w-4 h-4 mr-2" />
                    Save Draft
                  </Button>
                  <Button 
                    size="sm" 
                    className="w-full bg-blue-600 hover:bg-blue-700"
                    onClick={() => handleSave(false)}
                    disabled={saving}
                  >
                    <FileText className="w-4 h-4 mr-2" />
                    Save & Finish
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
};

export default QuotationBuilder;