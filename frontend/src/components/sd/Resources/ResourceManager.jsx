import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Button } from '../../ui/button';
import { Input } from '../../ui/input';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../../ui/card';
import { Badge } from '../../ui/badge';
import { Alert, AlertDescription } from '../../ui/alert';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from '../../ui/dialog';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../../ui/select';
import { Textarea } from '../../ui/textarea';
import { Label } from '../../ui/label';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../../ui/tabs';
import { 
  Plus, 
  Search, 
  Filter,
  Server,
  Cloud,
  HardDrive,
  Laptop,
  Shield,
  Network,
  AlertTriangle,
  TrendingUp,
  Package,
  ShoppingCart,
  Calendar,
  User,
  MapPin,
  DollarSign,
  BarChart3,
  Eye,
  Edit,
  Trash2
} from 'lucide-react';
import { toast } from 'sonner';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

// Resource type icons mapping
const RESOURCE_TYPE_ICONS = {
  cloud: Cloud,
  server: Server,
  license: Package,
  hardware: HardDrive,
  software: Laptop,
  network: Network
};

// Status color mapping
const STATUS_COLORS = {
  'Active': 'bg-green-100 text-green-800',
  'Inactive': 'bg-gray-100 text-gray-800',
  'Maintenance': 'bg-yellow-100 text-yellow-800',
  'Retired': 'bg-red-100 text-red-800'
};

const ResourceManager = () => {
  const [resources, setResources] = useState([]);
  const [summary, setSummary] = useState(null);
  const [purchaseRequests, setPurchaseRequests] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [filterType, setFilterType] = useState('');
  const [filterStatus, setFilterStatus] = useState('');
  const [selectedResource, setSelectedResource] = useState(null);
  const [showCreateResource, setShowCreateResource] = useState(false);
  const [showCreatePR, setShowCreatePR] = useState(false);

  // Form states
  const [resourceForm, setResourceForm] = useState({
    type: '',
    name: '',
    description: '',
    sku: '',
    available_qty: '',
    unit_cost: '',
    currency: 'USD',
    specifications: '',
    vendor: '',
    model: '',
    location: '',
    procurement_date: '',
    warranty_expiry: '',
    maintenance_schedule: '',
    owner_id: '',
    tags: [],
    notes: ''
  });

  const [prForm, setPrForm] = useState({
    project_id: '',
    resource_id: '',
    sku: '',
    description: '',
    quantity: '',
    estimated_cost: '',
    unit_cost: '',
    currency: 'USD',
    justification: '',
    priority: 'Medium',
    required_by: '',
    specifications: '',
    comments: ''
  });

  useEffect(() => {
    fetchData();
  }, [filterType, filterStatus]);

  const fetchData = async () => {
    try {
      setLoading(true);
      const token = localStorage.getItem('token');
      const headers = { Authorization: `Bearer ${token}` };

      // Fetch resources with filters
      const resourceParams = new URLSearchParams();
      if (filterType) resourceParams.append('type', filterType);
      if (filterStatus) resourceParams.append('status', filterStatus);
      
      const [resourcesRes, summaryRes, prRes] = await Promise.all([
        axios.get(`${BACKEND_URL}/api/sd/resources?${resourceParams.toString()}`, { headers }),
        axios.get(`${BACKEND_URL}/api/sd/resources/summary`, { headers }),
        axios.get(`${BACKEND_URL}/api/sd/resources/purchase-requests/`, { headers })
      ]);

      setResources(resourcesRes.data);
      setSummary(summaryRes.data);
      setPurchaseRequests(prRes.data);
    } catch (error) {
      console.error('Error fetching resource data:', error);
      toast.error('Failed to fetch resource data');
    } finally {
      setLoading(false);
    }
  };

  const handleCreateResource = async (e) => {
    e.preventDefault();
    try {
      const token = localStorage.getItem('token');
      const headers = { Authorization: `Bearer ${token}` };

      const formData = {
        ...resourceForm,
        available_qty: parseFloat(resourceForm.available_qty),
        unit_cost: parseFloat(resourceForm.unit_cost),
        specifications: resourceForm.specifications ? JSON.parse(resourceForm.specifications) : null,
        tags: Array.isArray(resourceForm.tags) ? resourceForm.tags : resourceForm.tags.split(',').map(t => t.trim()),
        procurement_date: resourceForm.procurement_date || null,
        warranty_expiry: resourceForm.warranty_expiry || null
      };

      await axios.post(`${BACKEND_URL}/api/sd/resources/`, formData, { headers });
      
      toast.success('Resource created successfully');
      setShowCreateResource(false);
      setResourceForm({
        type: '',
        name: '',
        description: '',
        sku: '',
        available_qty: '',
        unit_cost: '',
        currency: 'USD',
        specifications: '',
        vendor: '',
        model: '',
        location: '',
        procurement_date: '',
        warranty_expiry: '',
        maintenance_schedule: '',
        owner_id: '',
        tags: [],
        notes: ''
      });
      fetchData();
    } catch (error) {
      console.error('Error creating resource:', error);
      toast.error('Failed to create resource');
    }
  };

  const handleCreatePR = async (e) => {
    e.preventDefault();
    try {
      const token = localStorage.getItem('token');
      const headers = { Authorization: `Bearer ${token}` };

      const formData = {
        ...prForm,
        quantity: parseFloat(prForm.quantity),
        estimated_cost: parseFloat(prForm.estimated_cost) || 0,
        unit_cost: parseFloat(prForm.unit_cost) || 0,
        specifications: prForm.specifications ? JSON.parse(prForm.specifications) : null,
        required_by: prForm.required_by || null,
        tags: []
      };

      await axios.post(`${BACKEND_URL}/api/sd/resources/purchase-requests/`, formData, { headers });
      
      toast.success('Purchase request created successfully');
      setShowCreatePR(false);
      setPrForm({
        project_id: '',
        resource_id: '',
        sku: '',
        description: '',
        quantity: '',
        estimated_cost: '',
        unit_cost: '',
        currency: 'USD',
        justification: '',
        priority: 'Medium',
        required_by: '',
        specifications: '',
        comments: ''
      });
      fetchData();
    } catch (error) {
      console.error('Error creating purchase request:', error);
      toast.error('Failed to create purchase request');
    }
  };

  const filteredResources = resources.filter(resource => {
    return resource.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
           resource.sku?.toLowerCase().includes(searchTerm.toLowerCase()) ||
           resource.type.toLowerCase().includes(searchTerm.toLowerCase());
  });

  if (loading) {
    return (
      <div className="flex items-center justify-center p-8">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="p-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-slate-800 mb-2">Resource Management</h1>
        <p className="text-slate-600">Manage IT resources, allocations, and purchase requests</p>
      </div>

      {/* Summary Cards */}
      {summary && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <Card className="border-0 shadow-sm bg-gradient-to-br from-blue-50 to-blue-100">
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-blue-600">Total Resources</p>
                  <p className="text-3xl font-bold text-blue-800 mt-2">{summary.total_resources}</p>
                </div>
                <Package className="w-12 h-12 text-blue-600" />
              </div>
            </CardContent>
          </Card>
          
          <Card className="border-0 shadow-sm bg-gradient-to-br from-green-50 to-green-100">
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-green-600">Active Resources</p>
                  <p className="text-3xl font-bold text-green-800 mt-2">{summary.active_resources}</p>
                </div>
                <TrendingUp className="w-12 h-12 text-green-600" />
              </div>
            </CardContent>
          </Card>
          
          <Card className="border-0 shadow-sm bg-gradient-to-br from-orange-50 to-orange-100">
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-orange-600">High Utilization</p>
                  <p className="text-3xl font-bold text-orange-800 mt-2">{summary.high_utilization_resources}</p>
                </div>
                <AlertTriangle className="w-12 h-12 text-orange-600" />
              </div>
            </CardContent>
          </Card>
          
          <Card className="border-0 shadow-sm bg-gradient-to-br from-purple-50 to-purple-100">
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-purple-600">Pending PRs</p>
                  <p className="text-3xl font-bold text-purple-800 mt-2">{summary.pending_purchase_requests}</p>
                </div>
                <ShoppingCart className="w-12 h-12 text-purple-600" />
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      <Tabs defaultValue="resources" className="w-full">
        <TabsList className="grid w-full grid-cols-2">
          <TabsTrigger value="resources">Resources</TabsTrigger>
          <TabsTrigger value="purchase-requests">Purchase Requests</TabsTrigger>
        </TabsList>

        {/* Resources Tab */}
        <TabsContent value="resources" className="space-y-6">
          {/* Filters and Actions */}
          <div className="flex flex-col sm:flex-row gap-4 items-start sm:items-center justify-between">
            <div className="flex flex-col sm:flex-row gap-4 flex-1">
              <div className="relative flex-1 max-w-sm">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
                <Input
                  placeholder="Search resources..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="pl-10"
                />
              </div>
              
              <Select value={filterType} onValueChange={setFilterType}>
                <SelectTrigger className="w-[180px]">
                  <SelectValue placeholder="Filter by type" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all_types">All Types</SelectItem>
                  <SelectItem value="cloud">Cloud</SelectItem>
                  <SelectItem value="server">Server</SelectItem>
                  <SelectItem value="license">License</SelectItem>
                  <SelectItem value="hardware">Hardware</SelectItem>
                  <SelectItem value="software">Software</SelectItem>
                  <SelectItem value="network">Network</SelectItem>
                </SelectContent>
              </Select>
              
              <Select value={filterStatus} onValueChange={setFilterStatus}>
                <SelectTrigger className="w-[180px]">
                  <SelectValue placeholder="Filter by status" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all_statuses">All Statuses</SelectItem>
                  <SelectItem value="Active">Active</SelectItem>
                  <SelectItem value="Inactive">Inactive</SelectItem>
                  <SelectItem value="Maintenance">Maintenance</SelectItem>
                  <SelectItem value="Retired">Retired</SelectItem>
                </SelectContent>
              </Select>
            </div>
            
            <Dialog open={showCreateResource} onOpenChange={setShowCreateResource}>
              <DialogTrigger asChild>
                <Button>
                  <Plus className="w-4 h-4 mr-2" />
                  Add Resource
                </Button>
              </DialogTrigger>
              <DialogContent className="max-w-2xl max-h-[80vh] overflow-y-auto">
                <DialogHeader>
                  <DialogTitle>Create New Resource</DialogTitle>
                  <DialogDescription>
                    Add a new IT resource to the inventory
                  </DialogDescription>
                </DialogHeader>
                <form onSubmit={handleCreateResource} className="space-y-4">
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <Label htmlFor="type">Resource Type *</Label>
                      <Select value={resourceForm.type} onValueChange={(value) => setResourceForm({...resourceForm, type: value})}>
                        <SelectTrigger>
                          <SelectValue placeholder="Select type" />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="cloud">Cloud</SelectItem>
                          <SelectItem value="server">Server</SelectItem>
                          <SelectItem value="license">License</SelectItem>
                          <SelectItem value="hardware">Hardware</SelectItem>
                          <SelectItem value="software">Software</SelectItem>
                          <SelectItem value="network">Network</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                    
                    <div>
                      <Label htmlFor="name">Resource Name *</Label>
                      <Input
                        id="name"
                        value={resourceForm.name}
                        onChange={(e) => setResourceForm({...resourceForm, name: e.target.value})}
                        placeholder="Enter resource name"
                        required
                      />
                    </div>
                  </div>
                  
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <Label htmlFor="sku">SKU</Label>
                      <Input
                        id="sku"
                        value={resourceForm.sku}
                        onChange={(e) => setResourceForm({...resourceForm, sku: e.target.value})}
                        placeholder="Stock Keeping Unit"
                      />
                    </div>
                    
                    <div>
                      <Label htmlFor="available_qty">Available Quantity *</Label>
                      <Input
                        id="available_qty"
                        type="number"
                        value={resourceForm.available_qty}
                        onChange={(e) => setResourceForm({...resourceForm, available_qty: e.target.value})}
                        placeholder="0"
                        required
                      />
                    </div>
                  </div>
                  
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <Label htmlFor="unit_cost">Unit Cost</Label>
                      <Input
                        id="unit_cost"
                        type="number"
                        step="0.01"
                        value={resourceForm.unit_cost}
                        onChange={(e) => setResourceForm({...resourceForm, unit_cost: e.target.value})}
                        placeholder="0.00"
                      />
                    </div>
                    
                    <div>
                      <Label htmlFor="currency">Currency</Label>
                      <Select value={resourceForm.currency} onValueChange={(value) => setResourceForm({...resourceForm, currency: value})}>
                        <SelectTrigger>
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="USD">USD</SelectItem>
                          <SelectItem value="EUR">EUR</SelectItem>
                          <SelectItem value="INR">INR</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                  </div>
                  
                  <div>
                    <Label htmlFor="description">Description</Label>
                    <Textarea
                      id="description"
                      value={resourceForm.description}
                      onChange={(e) => setResourceForm({...resourceForm, description: e.target.value})}
                      placeholder="Resource description"
                    />
                  </div>
                  
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <Label htmlFor="vendor">Vendor</Label>
                      <Input
                        id="vendor"
                        value={resourceForm.vendor}
                        onChange={(e) => setResourceForm({...resourceForm, vendor: e.target.value})}
                        placeholder="Vendor name"
                      />
                    </div>
                    
                    <div>
                      <Label htmlFor="model">Model</Label>
                      <Input
                        id="model"
                        value={resourceForm.model}
                        onChange={(e) => setResourceForm({...resourceForm, model: e.target.value})}
                        placeholder="Model/version"
                      />
                    </div>
                  </div>
                  
                  <div>
                    <Label htmlFor="location">Location</Label>
                    <Input
                      id="location"
                      value={resourceForm.location}
                      onChange={(e) => setResourceForm({...resourceForm, location: e.target.value})}
                      placeholder="Physical/logical location"
                    />
                  </div>
                  
                  <div className="flex justify-end space-x-2">
                    <Button type="button" variant="outline" onClick={() => setShowCreateResource(false)}>
                      Cancel
                    </Button>
                    <Button type="submit">Create Resource</Button>
                  </div>
                </form>
              </DialogContent>
            </Dialog>
          </div>

          {/* Resources Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {filteredResources.map((resource) => {
              const IconComponent = RESOURCE_TYPE_ICONS[resource.type] || Package;
              const utilization = resource.utilization || 0;
              const utilizationColor = utilization >= 80 ? 'text-red-600' : utilization >= 50 ? 'text-yellow-600' : 'text-green-600';
              
              return (
                <Card key={resource.id} className="border hover:shadow-md transition-shadow">
                  <CardHeader className="pb-3">
                    <div className="flex items-start justify-between">
                      <div className="flex items-center space-x-3">
                        <div className="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center">
                          <IconComponent className="w-5 h-5 text-blue-600" />
                        </div>
                        <div>
                          <CardTitle className="text-lg">{resource.name}</CardTitle>
                          <p className="text-sm text-gray-500">{resource.resource_id}</p>
                        </div>
                      </div>
                      <Badge className={STATUS_COLORS[resource.status] || 'bg-gray-100 text-gray-800'}>
                        {resource.status}
                      </Badge>
                    </div>
                  </CardHeader>
                  
                  <CardContent>
                    <div className="space-y-3">
                      <div className="flex justify-between items-center">
                        <span className="text-sm text-gray-600">Type</span>
                        <span className="text-sm font-medium capitalize">{resource.type}</span>
                      </div>
                      
                      <div className="flex justify-between items-center">
                        <span className="text-sm text-gray-600">Available</span>
                        <span className="text-sm font-medium">
                          {resource.available_qty - (resource.assigned_qty || 0)} / {resource.available_qty}
                        </span>
                      </div>
                      
                      <div className="flex justify-between items-center">
                        <span className="text-sm text-gray-600">Utilization</span>
                        <span className={`text-sm font-medium ${utilizationColor}`}>
                          {utilization.toFixed(1)}%
                        </span>
                      </div>
                      
                      {resource.unit_cost > 0 && (
                        <div className="flex justify-between items-center">
                          <span className="text-sm text-gray-600">Unit Cost</span>
                          <span className="text-sm font-medium">
                            {resource.currency} {resource.unit_cost.toFixed(2)}
                          </span>
                        </div>
                      )}
                      
                      {resource.vendor && (
                        <div className="flex justify-between items-center">
                          <span className="text-sm text-gray-600">Vendor</span>
                          <span className="text-sm font-medium">{resource.vendor}</span>
                        </div>
                      )}
                      
                      {/* Progress bar for utilization */}
                      <div className="w-full bg-gray-200 rounded-full h-2">
                        <div 
                          className={`h-2 rounded-full ${utilization >= 80 ? 'bg-red-500' : utilization >= 50 ? 'bg-yellow-500' : 'bg-green-500'}`}
                          style={{ width: `${Math.min(utilization, 100)}%` }}
                        ></div>
                      </div>
                    </div>
                    
                    <div className="flex justify-end space-x-2 mt-4">
                      <Button size="sm" variant="outline">
                        <Eye className="w-4 h-4" />
                      </Button>
                      <Button size="sm" variant="outline">
                        <Edit className="w-4 h-4" />
                      </Button>
                    </div>
                  </CardContent>
                </Card>
              );
            })}
          </div>
          
          {filteredResources.length === 0 && (
            <Card className="border-dashed border-2 border-gray-300">
              <CardContent className="flex flex-col items-center justify-center py-12">
                <Package className="w-12 h-12 text-gray-400 mb-4" />
                <p className="text-lg font-medium text-gray-600 mb-2">No Resources Found</p>
                <p className="text-sm text-gray-500 mb-4">
                  {searchTerm || filterType || filterStatus 
                    ? 'Try adjusting your search criteria' 
                    : 'Get started by adding your first resource'
                  }
                </p>
                {!searchTerm && !filterType && !filterStatus && (
                  <Button onClick={() => setShowCreateResource(true)}>
                    <Plus className="w-4 h-4 mr-2" />
                    Add First Resource
                  </Button>
                )}
              </CardContent>
            </Card>
          )}
        </TabsContent>

        {/* Purchase Requests Tab */}
        <TabsContent value="purchase-requests" className="space-y-6">
          <div className="flex justify-between items-center">
            <div>
              <h2 className="text-xl font-semibold">Purchase Requests</h2>
              <p className="text-sm text-gray-600">Manage resource procurement requests</p>
            </div>
            
            <Dialog open={showCreatePR} onOpenChange={setShowCreatePR}>
              <DialogTrigger asChild>
                <Button>
                  <Plus className="w-4 h-4 mr-2" />
                  New Purchase Request
                </Button>
              </DialogTrigger>
              <DialogContent className="max-w-2xl max-h-[80vh] overflow-y-auto">
                <DialogHeader>
                  <DialogTitle>Create Purchase Request</DialogTitle>
                  <DialogDescription>
                    Submit a new purchase request for resources
                  </DialogDescription>
                </DialogHeader>
                <form onSubmit={handleCreatePR} className="space-y-4">
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <Label htmlFor="sku">SKU *</Label>
                      <Input
                        id="sku"
                        value={prForm.sku}
                        onChange={(e) => setPrForm({...prForm, sku: e.target.value})}
                        placeholder="Stock Keeping Unit"
                        required
                      />
                    </div>
                    
                    <div>
                      <Label htmlFor="quantity">Quantity *</Label>
                      <Input
                        id="quantity"
                        type="number"
                        value={prForm.quantity}
                        onChange={(e) => setPrForm({...prForm, quantity: e.target.value})}
                        placeholder="0"
                        required
                      />
                    </div>
                  </div>
                  
                  <div>
                    <Label htmlFor="pr_description">Description *</Label>
                    <Textarea
                      id="pr_description"
                      value={prForm.description}
                      onChange={(e) => setPrForm({...prForm, description: e.target.value})}
                      placeholder="Describe the item needed"
                      required
                    />
                  </div>
                  
                  <div className="grid grid-cols-3 gap-4">
                    <div>
                      <Label htmlFor="estimated_cost">Estimated Total Cost</Label>
                      <Input
                        id="estimated_cost"
                        type="number"
                        step="0.01"
                        value={prForm.estimated_cost}
                        onChange={(e) => setPrForm({...prForm, estimated_cost: e.target.value})}
                        placeholder="0.00"
                      />
                    </div>
                    
                    <div>
                      <Label htmlFor="unit_cost">Unit Cost</Label>
                      <Input
                        id="unit_cost"
                        type="number"
                        step="0.01"
                        value={prForm.unit_cost}
                        onChange={(e) => setPrForm({...prForm, unit_cost: e.target.value})}
                        placeholder="0.00"
                      />
                    </div>
                    
                    <div>
                      <Label htmlFor="pr_currency">Currency</Label>
                      <Select value={prForm.currency} onValueChange={(value) => setPrForm({...prForm, currency: value})}>
                        <SelectTrigger>
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="USD">USD</SelectItem>
                          <SelectItem value="EUR">EUR</SelectItem>
                          <SelectItem value="INR">INR</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                  </div>
                  
                  <div>
                    <Label htmlFor="justification">Business Justification *</Label>
                    <Textarea
                      id="justification"
                      value={prForm.justification}
                      onChange={(e) => setPrForm({...prForm, justification: e.target.value})}
                      placeholder="Explain why this purchase is needed"
                      required
                    />
                  </div>
                  
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <Label htmlFor="priority">Priority</Label>
                      <Select value={prForm.priority} onValueChange={(value) => setPrForm({...prForm, priority: value})}>
                        <SelectTrigger>
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="Low">Low</SelectItem>
                          <SelectItem value="Medium">Medium</SelectItem>
                          <SelectItem value="High">High</SelectItem>
                          <SelectItem value="Critical">Critical</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                    
                    <div>
                      <Label htmlFor="required_by">Required By</Label>
                      <Input
                        id="required_by"
                        type="date"
                        value={prForm.required_by}
                        onChange={(e) => setPrForm({...prForm, required_by: e.target.value})}
                      />
                    </div>
                  </div>
                  
                  <div className="flex justify-end space-x-2">
                    <Button type="button" variant="outline" onClick={() => setShowCreatePR(false)}>
                      Cancel
                    </Button>
                    <Button type="submit">Submit Request</Button>
                  </div>
                </form>
              </DialogContent>
            </Dialog>
          </div>
          
          {/* Purchase Requests List */}
          <div className="space-y-4">
            {purchaseRequests.map((pr) => (
              <Card key={pr.id} className="border hover:shadow-sm transition-shadow">
                <CardContent className="p-6">
                  <div className="flex items-start justify-between">
                    <div className="flex items-start space-x-4">
                      <div className="w-10 h-10 bg-purple-100 rounded-lg flex items-center justify-center">
                        <ShoppingCart className="w-5 h-5 text-purple-600" />
                      </div>
                      <div>
                        <h3 className="font-medium text-lg">{pr.description}</h3>
                        <p className="text-sm text-gray-500 mb-2">{pr.pr_id}</p>
                        <div className="flex items-center space-x-4 text-sm text-gray-600">
                          <span>SKU: {pr.sku}</span>
                          <span>Qty: {pr.quantity}</span>
                          {pr.estimated_cost > 0 && (
                            <span>Est. Cost: {pr.currency} {pr.estimated_cost.toFixed(2)}</span>
                          )}
                        </div>
                      </div>
                    </div>
                    
                    <div className="text-right">
                      <Badge 
                        className={
                          pr.status === 'Pending' ? 'bg-yellow-100 text-yellow-800' :
                          pr.status === 'Approved' ? 'bg-green-100 text-green-800' :
                          pr.status === 'Rejected' ? 'bg-red-100 text-red-800' :
                          'bg-gray-100 text-gray-800'
                        }
                      >
                        {pr.status}
                      </Badge>
                      <p className="text-sm text-gray-500 mt-1">
                        Priority: {pr.priority}
                      </p>
                    </div>
                  </div>
                  
                  {pr.justification && (
                    <div className="mt-4 p-3 bg-gray-50 rounded-lg">
                      <p className="text-sm text-gray-700">
                        <strong>Justification:</strong> {pr.justification}
                      </p>
                    </div>
                  )}
                </CardContent>
              </Card>
            ))}
            
            {purchaseRequests.length === 0 && (
              <Card className="border-dashed border-2 border-gray-300">
                <CardContent className="flex flex-col items-center justify-center py-12">
                  <ShoppingCart className="w-12 h-12 text-gray-400 mb-4" />
                  <p className="text-lg font-medium text-gray-600 mb-2">No Purchase Requests</p>
                  <p className="text-sm text-gray-500 mb-4">
                    Create your first purchase request to get started
                  </p>
                  <Button onClick={() => setShowCreatePR(true)}>
                    <Plus className="w-4 h-4 mr-2" />
                    Create First Request
                  </Button>
                </CardContent>
              </Card>
            )}
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default ResourceManager;