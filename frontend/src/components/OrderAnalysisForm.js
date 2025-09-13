import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { 
  ArrowLeft, 
  Save, 
  FileText, 
  Upload,
  AlertTriangle,
  CheckCircle,
  DollarSign,
  Package,
  TrendingUp
} from 'lucide-react';
import { usePermissions } from '../contexts/PermissionContext';
import axios from 'axios';

const OrderAnalysisForm = () => {
  const { opportunityId } = useParams();
  const navigate = useNavigate();
  const { permissions } = usePermissions();
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState(null);
  const [anomalies, setAnomalies] = useState([]);

  // Form data
  const [formData, setFormData] = useState({
    opportunity_id: '',
    customer_name: '',
    order_date: new Date().toISOString().split('T')[0],
    total_amount: 0,
    currency_id: '',
    profit_margin: 0,
    remarks: '',
    items: []
  });

  // Auto-fetched data
  const [autoData, setAutoData] = useState({});
  const [opportunity, setOpportunity] = useState(null);

  const baseURL = process.env.REACT_APP_BACKEND_URL;

  useEffect(() => {
    if (opportunityId) {
      checkOAEligibility();
    }
  }, [opportunityId]);

  const checkOAEligibility = async () => {
    try {
      setLoading(true);
      setError(null);
      const token = localStorage.getItem('token');

      // Check if OA can be created for this opportunity
      const eligibilityRes = await axios.get(`${baseURL}/api/opportunities/${opportunityId}/can-create-oa`, {
        headers: { Authorization: `Bearer ${token}` }
      });

      if (!eligibilityRes.data.valid) {
        setError(eligibilityRes.data.errors.join(', '));
        return;
      }

      // Get auto-fetched OA data
      const autoDataRes = await axios.get(`${baseURL}/api/opportunities/${opportunityId}/oa-data`, {
        headers: { Authorization: `Bearer ${token}` }
      });

      const data = autoDataRes.data;
      setAutoData(data);
      setAnomalies(data.anomalies || []);

      // Pre-fill form with auto-fetched data
      setFormData({
        opportunity_id: opportunityId,
        customer_name: data.customer_name,
        order_date: new Date().toISOString().split('T')[0],
        total_amount: data.total_amount,
        currency_id: data.currency_id,
        profit_margin: data.profit_margin,
        remarks: '',
        items: data.items || []
      });

    } catch (error) {
      console.error('Error checking OA eligibility:', error);
      setError(error.response?.data?.detail || 'Error loading order data');
    } finally {
      setLoading(false);
    }
  };

  const handleInputChange = (field, value) => {
    setFormData(prev => ({
      ...prev,
      [field]: value
    }));
  };

  const handleSave = async () => {
    try {
      setSaving(true);
      const token = localStorage.getItem('token');

      const response = await axios.post(`${baseURL}/api/order-analysis`, formData, {
        headers: { Authorization: `Bearer ${token}` }
      });

      alert('Order Acknowledgement created successfully!');
      navigate('/order-acknowledgements');
    } catch (error) {
      console.error('Error saving OA:', error);
      alert(error.response?.data?.detail || 'Error saving Order Acknowledgement');
    } finally {
      setSaving(false);
    }
  };

  const formatCurrency = (amount, currencySymbol = '₹') => {
    return `${currencySymbol}${Number(amount).toLocaleString('en-IN')}`;
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

  if (error) {
    return (
      <div className="container mx-auto p-6">
        <div className="text-center py-12">
          <AlertTriangle className="w-12 h-12 text-red-500 mx-auto mb-4" />
          <h2 className="text-2xl font-bold text-gray-900 mb-2">Cannot Create Order</h2>
          <p className="text-gray-600 mb-4">{error}</p>
          <Button onClick={() => navigate('/opportunities')} variant="outline">
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back to Opportunities
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
            onClick={() => navigate('/opportunities')}
            className="text-gray-600"
          >
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back to Opportunities
          </Button>
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Create Order Analysis</h1>
            <p className="text-gray-600 mt-1">
              Generate order analysis from won opportunity
            </p>
          </div>
        </div>
        <div className="flex items-center space-x-2">
          <Button 
            onClick={handleSave}
            disabled={saving}
            className="bg-blue-600 hover:bg-blue-700"
          >
            <Save className="w-4 h-4 mr-2" />
            {saving ? 'Saving...' : 'Create Order'}
          </Button>
        </div>
      </div>

      {/* Anomalies Alert */}
      {anomalies.length > 0 && (
        <Alert className="border-yellow-200 bg-yellow-50">
          <AlertTriangle className="h-4 w-4 text-yellow-600" />
          <AlertDescription className="text-yellow-800">
            <strong>Anomalies Detected:</strong>
            <ul className="mt-2 list-disc list-inside space-y-1">
              {anomalies.map((anomaly, index) => (
                <li key={index}>{anomaly}</li>
              ))}
            </ul>
          </AlertDescription>
        </Alert>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Main Form */}
        <div className="lg:col-span-2 space-y-6">
          {/* Order Details */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <FileText className="w-5 h-5" />
                Order Details
              </CardTitle>
              <CardDescription>
                Basic information for the order acknowledgement
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <Label htmlFor="customer_name">Customer Name *</Label>
                  <Input
                    id="customer_name"
                    value={formData.customer_name}
                    onChange={(e) => handleInputChange('customer_name', e.target.value)}
                    placeholder="Customer company name"
                    disabled // Auto-fetched from opportunity
                  />
                  <p className="text-xs text-gray-500 mt-1">Auto-fetched from opportunity</p>
                </div>
                
                <div>
                  <Label htmlFor="order_date">Order Date *</Label>
                  <Input
                    id="order_date"
                    type="date"
                    value={formData.order_date}
                    onChange={(e) => handleInputChange('order_date', e.target.value)}
                  />
                </div>
              </div>

              <div>
                <Label htmlFor="remarks">Remarks</Label>
                <Textarea
                  id="remarks"
                  value={formData.remarks}
                  onChange={(e) => handleInputChange('remarks', e.target.value)}
                  placeholder="Additional notes or comments..."
                  rows={3}
                  maxLength={500}
                />
                <p className="text-xs text-gray-500 mt-1">
                  {formData.remarks.length}/500 characters
                </p>
              </div>
            </CardContent>
          </Card>

          {/* Order Items */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Package className="w-5 h-5" />
                Order Items
              </CardTitle>
              <CardDescription>
                Items auto-fetched from selected quotation
              </CardDescription>
            </CardHeader>
            <CardContent>
              {formData.items.length > 0 ? (
                <div className="space-y-4">
                  {formData.items.map((item, index) => (
                    <div key={index} className="border rounded-lg p-4 bg-gray-50">
                      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                        <div>
                          <Label className="text-sm font-medium">Product</Label>
                          <p className="text-sm text-gray-700">{item.product_name}</p>
                        </div>
                        <div>
                          <Label className="text-sm font-medium">Quantity</Label>
                          <p className="text-sm text-gray-700">{item.qty} {item.unit}</p>
                        </div>
                        <div>
                          <Label className="text-sm font-medium">Unit Price</Label>
                          <p className="text-sm text-gray-700">
                            {formatCurrency(item.unit_price, autoData.currency_symbol)}
                          </p>
                        </div>
                        <div>
                          <Label className="text-sm font-medium">Total</Label>
                          <p className="text-sm font-semibold text-green-600">
                            {formatCurrency(item.total_price, autoData.currency_symbol)}
                          </p>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-gray-500 text-center py-8">No items found in quotation</p>
              )}
            </CardContent>
          </Card>
        </div>

        {/* Summary Sidebar */}
        <div className="space-y-6">
          {/* Financial Summary */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <DollarSign className="w-5 h-5" />
                Financial Summary
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <Label className="text-sm text-gray-600">Total Amount</Label>
                <p className="text-2xl font-bold text-green-600">
                  {formatCurrency(formData.total_amount, autoData.currency_symbol)}
                </p>
              </div>

              <Separator />

              <div>
                <Label className="text-sm text-gray-600">Profit Margin</Label>
                <div className="flex items-center gap-2">
                  <TrendingUp className="w-4 h-4 text-gray-400" />
                  <span className={`font-bold ${getProfitabilityColor(formData.profit_margin)}`}>
                    {formData.profit_margin.toFixed(1)}%
                  </span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2 mt-2">
                  <div 
                    className={`h-2 rounded-full ${
                      formData.profit_margin >= 50 ? 'bg-green-500' :
                      formData.profit_margin >= 25 ? 'bg-yellow-500' :
                      formData.profit_margin >= 0 ? 'bg-orange-500' : 'bg-red-500'
                    }`}
                    style={{ width: `${Math.min(formData.profit_margin, 100)}%` }}
                  ></div>
                </div>
              </div>

              <Separator />

              <div className="space-y-2">
                <div className="flex justify-between text-sm">
                  <span className="text-gray-600">Items Count:</span>
                  <span className="font-medium">{formData.items.length}</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-gray-600">Currency:</span>
                  <span className="font-medium">{autoData.currency_symbol}</span>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Status Information */}
          <Card>
            <CardHeader>
              <CardTitle className="text-sm">Order Status</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                <div className="flex items-center gap-2">
                  <CheckCircle className="w-4 h-4 text-green-500" />
                  <span className="text-sm">Opportunity: Won</span>
                </div>
                <div className="flex items-center gap-2">
                  <CheckCircle className="w-4 h-4 text-blue-500" />
                  <span className="text-sm">Status: Draft (after creation)</span>
                </div>
                {formData.total_amount > 500000 && (
                  <div className="flex items-center gap-2">
                    <AlertTriangle className="w-4 h-4 text-yellow-500" />
                    <span className="text-sm">High-value: GC approval required</span>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>

          {/* File Upload Placeholder */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-sm">
                <Upload className="w-4 h-4" />
                Attachments
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="border-2 border-dashed border-gray-300 rounded-lg p-4 text-center">
                <Upload className="w-8 h-8 text-gray-400 mx-auto mb-2" />
                <p className="text-sm text-gray-600">Attachments can be added</p>
                <p className="text-xs text-gray-500">after order creation</p>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
};

export default OrderAnalysisForm;