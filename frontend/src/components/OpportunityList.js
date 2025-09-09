import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Badge } from '@/components/ui/badge';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Separator } from '@/components/ui/separator';
import { Plus, Target, TrendingUp, DollarSign, Award, Search, Filter } from 'lucide-react';
import PermissionDataTable from './PermissionDataTable';
import { usePermissions } from '../contexts/PermissionContext';
import axios from 'axios';

const OpportunityList = () => {
  const navigate = useNavigate();
  const { permissions } = usePermissions();
  const [opportunities, setOpportunities] = useState([]);
  const [kpis, setKpis] = useState({
    total: 0,
    open: 0,
    won: 0,
    lost: 0,
    weighted_pipeline: 0
  });
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [stageFilter, setStageFilter] = useState('all');
  const [statusFilter, setStatusFilter] = useState('all');
  const [selectedOpportunity, setSelectedOpportunity] = useState(null);
  const [viewDialogOpen, setViewDialogOpen] = useState(false);
  
  // Master data
  const [stages, setStages] = useState([]);
  const [companies, setCompanies] = useState([]);
  const [currencies, setCurrencies] = useState([]);
  const [users, setUsers] = useState([]);

  const baseURL = import.meta.env.REACT_APP_BACKEND_URL || process.env.REACT_APP_BACKEND_URL;

  useEffect(() => {
    fetchOpportunities();
    fetchKPIs();
    fetchMasterData();
  }, []);

  const fetchOpportunities = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(`${baseURL}/api/opportunities`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setOpportunities(response.data || []);
    } catch (error) {
      console.error('Error fetching opportunities:', error);
      setOpportunities([]);
    }
  };

  const fetchKPIs = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(`${baseURL}/api/opportunities/kpis`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setKpis(response.data || {
        total: 0,
        open: 0,
        won: 0,
        lost: 0,
        weighted_pipeline: 0
      });
    } catch (error) {
      console.error('Error fetching KPIs:', error);
    }
  };

  const fetchMasterData = async () => {
    try {
      const token = localStorage.getItem('token');
      const [stagesRes, companiesRes, currenciesRes, usersRes] = await Promise.all([
        axios.get(`${baseURL}/api/mst/stages`, { headers: { Authorization: `Bearer ${token}` }}),
        axios.get(`${baseURL}/api/companies`, { headers: { Authorization: `Bearer ${token}` }}),
        axios.get(`${baseURL}/api/mst/currencies`, { headers: { Authorization: `Bearer ${token}` }}),
        axios.get(`${baseURL}/api/users`, { headers: { Authorization: `Bearer ${token}` }})
      ]);
      
      setStages(stagesRes.data || []);
      setCompanies(companiesRes.data || []);
      setCurrencies(currenciesRes.data || []);
      setUsers(usersRes.data || []);
    } catch (error) {
      console.error('Error fetching master data:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleViewOpportunity = (opportunity) => {
    setSelectedOpportunity(opportunity);
    setViewDialogOpen(true);
  };

  const handleAddOpportunity = () => {
    navigate('/opportunities/add');
  };

  const handleEditOpportunity = (opportunity) => {
    navigate(`/opportunities/edit/${opportunity.id}`);
  };

  const handleDeleteOpportunity = async (opportunity) => {
    if (window.confirm(`Are you sure you want to delete opportunity "${opportunity.project_title}"?`)) {
      try {
        const token = localStorage.getItem('token');
        await axios.delete(`${baseURL}/api/opportunities/${opportunity.id}`, {
          headers: { Authorization: `Bearer ${token}` }
        });
        fetchOpportunities();
        fetchKPIs();
      } catch (error) {
        console.error('Error deleting opportunity:', error);
        alert('Error deleting opportunity. Please try again.');
      }
    }
  };

  const getStageInfo = (stageId) => {
    const stage = stages.find(s => s.id === stageId);
    return stage ? { name: stage.stage_name, code: stage.stage_code } : { name: 'Unknown', code: 'L0' };
  };

  const getCompanyName = (companyId) => {
    const company = companies.find(c => c.id === companyId);
    return company ? company.company_name : 'Unknown Company';
  };

  const getCurrencySymbol = (currencyId) => {
    const currency = currencies.find(c => c.id === currencyId);
    return currency ? currency.symbol : '₹';
  };

  const getUserName = (userId) => {
    const user = users.find(u => u.id === userId);
    return user ? user.username : 'Unknown User';
  };

  const formatCurrency = (amount, currencyId = null) => {
    const symbol = getCurrencySymbol(currencyId);
    return `${symbol}${Number(amount).toLocaleString('en-IN')}`;
  };

  const getStatusBadgeColor = (status) => {
    switch (status.toLowerCase()) {
      case 'open': return 'bg-blue-100 text-blue-800 border-blue-200';
      case 'won': return 'bg-green-100 text-green-800 border-green-200';
      case 'lost': return 'bg-red-100 text-red-800 border-red-200';
      case 'on hold': return 'bg-yellow-100 text-yellow-800 border-yellow-200';
      default: return 'bg-gray-100 text-gray-800 border-gray-200';
    }
  };

  const getStageBadgeColor = (stageCode) => {
    const colors = {
      'L1': 'bg-slate-100 text-slate-800 border-slate-200',
      'L2': 'bg-blue-100 text-blue-800 border-blue-200',
      'L3': 'bg-indigo-100 text-indigo-800 border-indigo-200',
      'L4': 'bg-purple-100 text-purple-800 border-purple-200',
      'L5': 'bg-pink-100 text-pink-800 border-pink-200',
      'L6': 'bg-orange-100 text-orange-800 border-orange-200',
      'L7': 'bg-yellow-100 text-yellow-800 border-yellow-200',
      'L8': 'bg-green-100 text-green-800 border-green-200'
    };
    return colors[stageCode] || 'bg-gray-100 text-gray-800 border-gray-200';
  };

  const calculateWinRate = () => {
    const totalClosed = kpis.won + kpis.lost;
    return totalClosed > 0 ? ((kpis.won / totalClosed) * 100).toFixed(1) : '0.0';
  };

  const columns = [
    {
      key: 'opportunity_id',
      label: 'Opportunity ID',
      sortable: true,
      render: (value) => (
        <span className="font-mono text-sm font-medium text-blue-600">{value}</span>
      )
    },
    {
      key: 'project_title',
      label: 'Project Title',
      sortable: true,
      render: (value) => (
        <span className="font-medium text-gray-900">{value}</span>
      )
    },
    {
      key: 'company_id',
      label: 'Company',
      render: (value) => (
        <span className="text-gray-700">{getCompanyName(value)}</span>
      )
    },
    {
      key: 'stage_id',
      label: 'Stage',
      render: (value) => {
        const stage = getStageInfo(value);
        return (
          <Badge variant="outline" className={getStageBadgeColor(stage.code)}>
            {stage.code} - {stage.name}
          </Badge>
        );
      }
    },
    {
      key: 'status',
      label: 'Status',
      render: (value) => (
        <Badge variant="outline" className={getStatusBadgeColor(value)}>
          {value}
        </Badge>
      )
    },
    {
      key: 'expected_revenue',
      label: 'Expected Revenue',
      sortable: true,
      render: (value, row) => (
        <span className="font-medium text-green-600">
          {formatCurrency(value, row.currency_id)}
        </span>
      )
    },
    {
      key: 'weighted_revenue',
      label: 'Weighted Revenue',
      sortable: true,
      render: (value, row) => (
        <span className="font-medium text-purple-600">
          {formatCurrency(value, row.currency_id)}
        </span>
      )
    },
    {
      key: 'win_probability',
      label: 'Win Probability',
      sortable: true,
      render: (value) => (
        <div className="flex items-center gap-2">
          <div className="w-16 bg-gray-200 rounded-full h-2">
            <div 
              className="bg-gradient-to-r from-red-500 via-yellow-500 to-green-500 h-2 rounded-full transition-all duration-300"
              style={{ width: `${value}%` }}
            ></div>
          </div>
          <span className="text-sm font-medium">{value}%</span>
        </div>
      )
    },
    {
      key: 'lead_owner_id',
      label: 'Owner',
      render: (value) => (
        <span className="text-gray-700">{getUserName(value)}</span>
      )
    },
    {
      key: 'created_at',
      label: 'Created',
      sortable: true,
      render: (value) => (
        <span className="text-gray-500 text-sm">
          {new Date(value).toLocaleDateString('en-IN')}
        </span>
      )
    }
  ];

  if (loading) {
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
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Opportunities</h1>
          <p className="text-gray-600 mt-1">Manage sales opportunities and pipeline</p>
        </div>
        {permissions.some(p => p.permission === 'Add' && p.menu === 'Opportunities') && (
          <Button onClick={handleAddOpportunity} className="bg-blue-600 hover:bg-blue-700">
            <Plus className="w-4 h-4 mr-2" />
            Add Opportunity
          </Button>
        )}
      </div>

      {/* KPI Dashboard */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
        <Card className="border-l-4 border-l-blue-500">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-gray-600">Total Opportunities</CardTitle>
            <Target className="h-4 w-4 text-blue-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-gray-900">{kpis.total}</div>
            <p className="text-xs text-gray-500 mt-1">All opportunities in pipeline</p>
          </CardContent>
        </Card>

        <Card className="border-l-4 border-l-green-500">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-gray-600">Open</CardTitle>
            <TrendingUp className="h-4 w-4 text-green-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-gray-900">{kpis.open}</div>
            <p className="text-xs text-gray-500 mt-1">Active opportunities</p>
          </CardContent>
        </Card>

        <Card className="border-l-4 border-l-purple-500">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-gray-600">Pipeline Value</CardTitle>
            <DollarSign className="h-4 w-4 text-purple-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-gray-900">{formatCurrency(kpis.weighted_pipeline)}</div>
            <p className="text-xs text-gray-500 mt-1">Weighted revenue</p>
          </CardContent>
        </Card>

        <Card className="border-l-4 border-l-orange-500">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-gray-600">Weighted Revenue</CardTitle>
            <DollarSign className="h-4 w-4 text-orange-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-gray-900">{formatCurrency(kpis.weighted_pipeline)}</div>
            <p className="text-xs text-gray-500 mt-1">Expected revenue</p>
          </CardContent>
        </Card>

        <Card className="border-l-4 border-l-yellow-500">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-gray-600">Win Rate</CardTitle>
            <Award className="h-4 w-4 text-yellow-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-gray-900">{calculateWinRate()}%</div>
            <p className="text-xs text-gray-500 mt-1">Success rate</p>
          </CardContent>
        </Card>
      </div>

      {/* Filters & Actions */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg font-semibold flex items-center gap-2">
            <Filter className="w-5 h-5" />
            Filters & Actions
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex flex-col lg:flex-row gap-4">
            <div className="flex-1">
              <div className="relative">
                <Search className="absolute left-3 top-3 h-4 w-4 text-gray-400" />
                <Input
                  placeholder="Search opportunities by project title, company, or opportunity ID..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="pl-10"
                />
              </div>
            </div>
            <div className="flex gap-2">
              <Select value={stageFilter} onValueChange={setStageFilter}>
                <SelectTrigger className="w-48">
                  <SelectValue placeholder="Filter by Stage" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Stages</SelectItem>
                  {stages.map((stage) => (
                    <SelectItem key={stage.id} value={stage.id}>
                      {stage.stage_code} - {stage.stage_name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              
              <Select value={statusFilter} onValueChange={setStatusFilter}>
                <SelectTrigger className="w-48">
                  <SelectValue placeholder="Filter by Status" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Status</SelectItem>
                  <SelectItem value="Open">Open</SelectItem>
                  <SelectItem value="Won">Won</SelectItem>
                  <SelectItem value="Lost">Lost</SelectItem>
                  <SelectItem value="On Hold">On Hold</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Data Table */}
      <Card>
        <CardContent className="p-0">
          <PermissionDataTable
            data={opportunities}
            columns={columns}
            searchTerm={searchTerm}
            onView={handleViewOpportunity}
            onEdit={handleEditOpportunity}
            onDelete={handleDeleteOpportunity}
            module="Sales"
            menu="Opportunities"
            emptyStateTitle="No opportunities found"
            emptyStateDescription="Get started by creating your first opportunity"
          />
        </CardContent>
      </Card>

      {/* View Dialog */}
      <Dialog open={viewDialogOpen} onOpenChange={setViewDialogOpen}>
        <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="text-xl font-bold text-gray-900">
              Opportunity Details
            </DialogTitle>
            <DialogDescription>
              Complete information for {selectedOpportunity?.project_title}
            </DialogDescription>
          </DialogHeader>
          
          {selectedOpportunity && (
            <div className="space-y-6">
              {/* Opportunity Information */}
              <div>
                <h3 className="text-lg font-semibold text-gray-900 mb-3">Opportunity Information</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="text-sm font-medium text-gray-500">Opportunity ID</label>
                    <p className="font-mono text-sm font-medium text-blue-600">{selectedOpportunity.opportunity_id}</p>
                  </div>
                  <div>
                    <label className="text-sm font-medium text-gray-500">Project Title</label>
                    <p className="font-medium text-gray-900">{selectedOpportunity.project_title}</p>
                  </div>
                  <div>
                    <label className="text-sm font-medium text-gray-500">Stage</label>
                    <Badge variant="outline" className={getStageBadgeColor(getStageInfo(selectedOpportunity.stage_id).code)}>
                      {getStageInfo(selectedOpportunity.stage_id).code} - {getStageInfo(selectedOpportunity.stage_id).name}
                    </Badge>
                  </div>
                  <div>
                    <label className="text-sm font-medium text-gray-500">Status</label>
                    <Badge variant="outline" className={getStatusBadgeColor(selectedOpportunity.status)}>
                      {selectedOpportunity.status}
                    </Badge>
                  </div>
                </div>
              </div>

              <Separator />

              {/* Company & Contact Information */}
              <div>
                <h3 className="text-lg font-semibold text-gray-900 mb-3">Company & Contact</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="text-sm font-medium text-gray-500">Company</label>
                    <p className="text-gray-900">{getCompanyName(selectedOpportunity.company_id)}</p>
                  </div>
                  <div>
                    <label className="text-sm font-medium text-gray-500">Lead Owner</label>
                    <p className="text-gray-900">{getUserName(selectedOpportunity.lead_owner_id)}</p>
                  </div>
                </div>
              </div>

              <Separator />

              {/* Financial Information */}
              <div>
                <h3 className="text-lg font-semibold text-gray-900 mb-3">Financial Information</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="text-sm font-medium text-gray-500">Expected Revenue</label>
                    <p className="text-lg font-semibold text-green-600">
                      {formatCurrency(selectedOpportunity.expected_revenue, selectedOpportunity.currency_id)}
                    </p>
                  </div>
                  <div>
                    <label className="text-sm font-medium text-gray-500">Weighted Revenue</label>
                    <p className="text-lg font-semibold text-purple-600">
                      {formatCurrency(selectedOpportunity.weighted_revenue, selectedOpportunity.currency_id)}
                    </p>
                  </div>
                  <div>
                    <label className="text-sm font-medium text-gray-500">Win Probability</label>
                    <div className="flex items-center gap-2">
                      <div className="w-24 bg-gray-200 rounded-full h-2">
                        <div 
                          className="bg-gradient-to-r from-red-500 via-yellow-500 to-green-500 h-2 rounded-full"
                          style={{ width: `${selectedOpportunity.win_probability}%` }}
                        ></div>
                      </div>
                      <span className="font-medium">{selectedOpportunity.win_probability}%</span>
                    </div>
                  </div>
                </div>
              </div>

              <Separator />

              {/* Additional Information */}
              {selectedOpportunity.product_interest && (
                <div>
                  <h3 className="text-lg font-semibold text-gray-900 mb-3">Product Interest</h3>
                  <p className="text-gray-700">{selectedOpportunity.product_interest}</p>
                </div>
              )}

              <Separator />

              {/* System Information */}
              <div>
                <h3 className="text-lg font-semibold text-gray-900 mb-3">System Information</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="text-sm font-medium text-gray-500">Created</label>
                    <p className="text-gray-700">
                      {new Date(selectedOpportunity.created_at).toLocaleString('en-IN')}
                    </p>
                  </div>
                  <div>
                    <label className="text-sm font-medium text-gray-500">Last Updated</label>
                    <p className="text-gray-700">
                      {new Date(selectedOpportunity.updated_at).toLocaleString('en-IN')}
                    </p>
                  </div>
                  {selectedOpportunity.lead_id && (
                    <div>
                      <label className="text-sm font-medium text-gray-500">Converted from Lead</label>
                      <p className="font-mono text-sm text-blue-600">{selectedOpportunity.lead_id}</p>
                    </div>
                  )}
                </div>
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default OpportunityList;