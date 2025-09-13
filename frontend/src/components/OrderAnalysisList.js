import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Badge } from '@/components/ui/badge';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Separator } from '@/components/ui/separator';
import { 
  FileText, 
  DollarSign, 
  TrendingUp, 
  Clock, 
  Search, 
  Filter, 
  Download,
  Eye,
  Edit,
  Trash2,
  AlertTriangle
} from 'lucide-react';
import PermissionDataTable from './PermissionDataTable';
import { usePermissions } from '../contexts/PermissionContext';
import axios from 'axios';

const OrderAnalysisList = () => {
  const navigate = useNavigate();
  const { permissions } = usePermissions();
  const [orders, setOrders] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [sortField, setSortField] = useState('created_at');
  const [sortDirection, setSortDirection] = useState('desc');
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [statusFilter, setStatusFilter] = useState('All');
  const [customerFilter, setCustomerFilter] = useState('');
  const [dateFromFilter, setDateFromFilter] = useState('');
  const [dateToFilter, setDateToFilter] = useState('');
  const [selectedOrder, setSelectedOrder] = useState(null);
  const [viewDialogOpen, setViewDialogOpen] = useState(false);

  // KPIs
  const [kpis, setKpis] = useState({
    total: 0,
    draft: 0,
    approved: 0,
    fulfilled: 0,
    totalValue: 0
  });

  const baseURL = process.env.REACT_APP_BACKEND_URL;

  useEffect(() => {
    fetchOrders();
  }, [currentPage, statusFilter, customerFilter, dateFromFilter, dateToFilter, sortField, sortDirection]);

  const fetchOrders = async () => {
    try {
      setLoading(true);
      setError(null);
      const token = localStorage.getItem('token');

      const params = new URLSearchParams({
        skip: (currentPage - 1) * 20,
        limit: 20,
        ...(statusFilter !== 'All' && { status: statusFilter }),
        ...(customerFilter && { customer: customerFilter }),
        ...(dateFromFilter && { date_from: dateFromFilter }),
        ...(dateToFilter && { date_to: dateToFilter })
      });

      const response = await axios.get(`${baseURL}/api/order-analysis?${params}`, {
        headers: { Authorization: `Bearer ${token}` }
      });

      setOrders(response.data.orders || []);
      setTotalPages(Math.ceil((response.data.total || 0) / 20));
      
      // Calculate KPIs
      calculateKPIs(response.data.orders || []);
      
    } catch (error) {
      console.error('Error fetching orders:', error);
      setError('Failed to fetch orders');
    } finally {
      setLoading(false);
    }
  };

  const calculateKPIs = (ordersData) => {
    const total = ordersData.length;
    const draft = ordersData.filter(o => o.status === 'Draft').length;
    const approved = ordersData.filter(o => o.status === 'Approved').length;
    const fulfilled = ordersData.filter(o => o.status === 'Fulfilled').length;
    const totalValue = ordersData.reduce((sum, o) => sum + (o.total_amount || 0), 0);

    setKpis({
      total,
      draft,
      approved,
      fulfilled,
      totalValue
    });
  };

  const handleSort = (field) => {
    if (sortField === field) {
      setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc');
    } else {
      setSortField(field);
      setSortDirection('asc');
    }
  };

  const handleViewOrder = (order) => {
    setSelectedOrder(order);
    setViewDialogOpen(true);
  };

  const handleEditOrder = (order) => {
    navigate(`/order-analysis/edit/${order.id}`);
  };

  const handleDeleteOrder = async (order) => {
    if (window.confirm(`Are you sure you want to delete order "${order.order_id}"?`)) {
      try {
        const token = localStorage.getItem('token');
        await axios.delete(`${baseURL}/api/order-analysis/${order.id}`, {
          headers: { Authorization: `Bearer ${token}` }
        });
        alert('Order deleted successfully');
        fetchOrders();
      } catch (error) {
        console.error('Error deleting order:', error);
        alert('Error deleting order. Please try again.');
      }
    }
  };

  const exportToCSV = () => {
    // TODO: Implement CSV export functionality
    alert('CSV export functionality will be implemented');
  };

  const formatCurrency = (amount) => {
    return `₹${Number(amount).toLocaleString('en-IN')}`;
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('en-IN');
  };

  const getStatusBadgeColor = (status) => {
    switch (status) {
      case 'Draft':
        return 'bg-gray-100 text-gray-800 border-gray-200';
      case 'Under Review':
        return 'bg-yellow-100 text-yellow-800 border-yellow-200';
      case 'Approved':
        return 'bg-green-100 text-green-800 border-green-200';
      case 'Fulfilled':
        return 'bg-blue-100 text-blue-800 border-blue-200';
      case 'Cancelled':
        return 'bg-red-100 text-red-800 border-red-200';
      default:
        return 'bg-gray-100 text-gray-800 border-gray-200';
    }
  };

  const getProfitabilityColor = (percentage) => {
    if (percentage >= 50) return 'text-green-600';
    if (percentage >= 25) return 'text-yellow-600';
    if (percentage >= 0) return 'text-orange-600';
    return 'text-red-600';
  };

  const columns = [
    {
      key: 'order_id',
      label: 'Order ID',
      sortable: true,
      render: (order) => (
        <span className="font-mono text-sm font-medium text-blue-600">{order.order_id}</span>
      )
    },
    {
      key: 'customer_name',
      label: 'Customer',
      sortable: true,
      render: (order) => (
        <span className="font-medium text-gray-900">{order.customer_name}</span>
      )
    },
    {
      key: 'order_date',
      label: 'Order Date',
      sortable: true,
      render: (order) => (
        <span className="text-gray-700">{formatDate(order.order_date)}</span>
      )
    },
    {
      key: 'total_amount',
      label: 'Total Amount',
      sortable: true,
      render: (order) => (
        <span className="font-semibold text-green-600">
          {formatCurrency(order.total_amount)}
        </span>
      )
    },
    {
      key: 'status',
      label: 'Status',
      render: (order) => (
        <div className="flex items-center gap-2">
          <Badge variant="outline" className={getStatusBadgeColor(order.status)}>
            {order.status}
          </Badge>
          {order.gc_approval_flag && (
            <AlertTriangle className="w-4 h-4 text-yellow-500" title="GC Approval Required" />
          )}
        </div>
      )
    },
    {
      key: 'profit_margin',
      label: 'Profit Margin',
      sortable: true,
      render: (order) => (
        <div className="flex items-center gap-2">
          <TrendingUp className="w-4 h-4 text-gray-400" />
          <span className={`font-medium ${getProfitabilityColor(order.profit_margin)}`}>
            {order.profit_margin?.toFixed(1) || '0.0'}%
          </span>
        </div>
      )
    }
  ];

  if (loading && currentPage === 1) {
    return (
      <div className="container mx-auto p-6">
        <div className="flex justify-center items-center h-64">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        </div>
      </div>
    );
  }

  return (
    <div className="container mx-auto p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Order Analysis</h1>
          <p className="text-gray-600 mt-1">Manage order analysis and approvals</p>
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-gray-600">Total Orders</CardTitle>
            <FileText className="h-4 w-4 text-blue-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-gray-900">{kpis.total}</div>
            <p className="text-xs text-gray-500 mt-1">All orders</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-gray-600">Draft Orders</CardTitle>
            <Clock className="h-4 w-4 text-yellow-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-gray-900">{kpis.draft}</div>
            <p className="text-xs text-gray-500 mt-1">Pending completion</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-gray-600">Approved Orders</CardTitle>
            <FileText className="h-4 w-4 text-green-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-gray-900">{kpis.approved}</div>
            <p className="text-xs text-gray-500 mt-1">Ready for fulfillment</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-gray-600">Fulfilled Orders</CardTitle>
            <FileText className="h-4 w-4 text-blue-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-gray-900">{kpis.fulfilled}</div>
            <p className="text-xs text-gray-500 mt-1">Completed</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-gray-600">Total Value</CardTitle>
            <DollarSign className="h-4 w-4 text-green-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-gray-900">{formatCurrency(kpis.totalValue)}</div>
            <p className="text-xs text-gray-500 mt-1">Order value</p>
          </CardContent>
        </Card>
      </div>

      {/* Filters */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg font-semibold flex items-center gap-2">
            <Filter className="w-5 h-5" />
            Filters & Search
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <div>
              <Label className="text-sm font-medium text-gray-600">Status</Label>
              <Select value={statusFilter} onValueChange={setStatusFilter}>
                <SelectTrigger>
                  <SelectValue placeholder="Filter by status" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="All">All Statuses</SelectItem>
                  <SelectItem value="Draft">Draft</SelectItem>
                  <SelectItem value="Under Review">Under Review</SelectItem>
                  <SelectItem value="Approved">Approved</SelectItem>
                  <SelectItem value="Fulfilled">Fulfilled</SelectItem>
                  <SelectItem value="Cancelled">Cancelled</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div>
              <Label className="text-sm font-medium text-gray-600">Customer</Label>
              <Input
                placeholder="Search customer..."
                value={customerFilter}
                onChange={(e) => setCustomerFilter(e.target.value)}
              />
            </div>

            <div>
              <Label className="text-sm font-medium text-gray-600">From Date</Label>
              <Input
                type="date"
                value={dateFromFilter}
                onChange={(e) => setDateFromFilter(e.target.value)}
              />
            </div>

            <div>
              <Label className="text-sm font-medium text-gray-600">To Date</Label>
              <Input
                type="date"
                value={dateToFilter}
                onChange={(e) => setDateToFilter(e.target.value)}
              />
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Orders Table */}
      <PermissionDataTable
        data={orders}
        columns={columns}
        loading={loading}
        searchTerm={searchTerm}
        setSearchTerm={setSearchTerm}
        sortField={sortField}
        sortDirection={sortDirection}
        currentPage={currentPage}
        setCurrentPage={setCurrentPage}
        totalPages={totalPages}
        onSort={handleSort}
        onExport={exportToCSV}
        onView={handleViewOrder}
        onEdit={handleEditOrder}
        onDelete={handleDeleteOrder}
        title="Order Analysis"
        description="Manage order analysis and track their status"
        modulePath="/order-analysis"
        entityName="order-analysis"
      />

      {/* Order Details Dialog */}
      <Dialog open={viewDialogOpen} onOpenChange={setViewDialogOpen}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>Order Details</DialogTitle>
            <DialogDescription>
              View complete order acknowledgement information
            </DialogDescription>
          </DialogHeader>
          
          {selectedOrder && (
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label className="text-sm font-medium text-gray-600">Order ID</Label>
                  <p className="font-mono text-sm font-medium text-blue-600">{selectedOrder.order_id}</p>
                </div>
                <div>
                  <Label className="text-sm font-medium text-gray-600">Status</Label>
                  <Badge variant="outline" className={getStatusBadgeColor(selectedOrder.status)}>
                    {selectedOrder.status}
                  </Badge>
                </div>
                <div>
                  <Label className="text-sm font-medium text-gray-600">Customer</Label>
                  <p className="text-sm">{selectedOrder.customer_name}</p>
                </div>
                <div>
                  <Label className="text-sm font-medium text-gray-600">Order Date</Label>
                  <p className="text-sm">{formatDate(selectedOrder.order_date)}</p>
                </div>
                <div>
                  <Label className="text-sm font-medium text-gray-600">Total Amount</Label>
                  <p className="text-lg font-semibold text-green-600">
                    {formatCurrency(selectedOrder.total_amount)}
                  </p>
                </div>
                <div>
                  <Label className="text-sm font-medium text-gray-600">Profit Margin</Label>
                  <p className={`text-lg font-semibold ${getProfitabilityColor(selectedOrder.profit_margin)}`}>
                    {selectedOrder.profit_margin?.toFixed(1) || '0.0'}%
                  </p>
                </div>
              </div>

              {selectedOrder.remarks && (
                <div>
                  <Label className="text-sm font-medium text-gray-600">Remarks</Label>
                  <p className="text-sm text-gray-700 bg-gray-50 p-3 rounded">
                    {selectedOrder.remarks}
                  </p>
                </div>
              )}

              {selectedOrder.items && selectedOrder.items.length > 0 && (
                <div>
                  <Label className="text-sm font-medium text-gray-600">Order Items</Label>
                  <div className="space-y-2 mt-2">
                    {selectedOrder.items.map((item, index) => (
                      <div key={index} className="border rounded p-3 bg-gray-50">
                        <div className="grid grid-cols-4 gap-2 text-sm">
                          <div>
                            <span className="font-medium">{item.product_name}</span>
                          </div>
                          <div>Qty: {item.qty}</div>
                          <div>{formatCurrency(item.unit_price)}</div>
                          <div className="font-semibold text-green-600">
                            {formatCurrency(item.total_price)}
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default OrderAnalysisList;