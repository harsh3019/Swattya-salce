import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Separator } from '@/components/ui/separator';
import { Progress } from '@/components/ui/progress';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import StageManagement from './StageManagement';
import { 
  ArrowLeft, 
  Edit, 
  FileText, 
  TrendingUp, 
  DollarSign, 
  Users, 
  Calendar,
  Building,
  User,
  Target,
  Award,
  ChevronRight,
  Plus,
  Eye,
  Download
} from 'lucide-react';
import { usePermissions } from '../contexts/PermissionContext';
import axios from 'axios';

const OpportunityDetail = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const { permissions } = usePermissions();
  const [opportunity, setOpportunity] = useState(null);
  const [quotations, setQuotations] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [stageDialogOpen, setStageDialogOpen] = useState(false);
  
  // Master data
  const [stages, setStages] = useState([]);
  const [companies, setCompanies] = useState([]);
  const [currencies, setCurrencies] = useState([]);
  const [users, setUsers] = useState([]);

  const baseURL = process.env.REACT_APP_BACKEND_URL;

  useEffect(() => {
    if (id) {
      fetchOpportunity();
      fetchQuotations();
      fetchMasterData();
    }
  }, [id]);

  // Refresh data when returning to this page (e.g., from stage management)
  useEffect(() => {
    const handleFocus = () => {
      if (id) {
        fetchOpportunity();
        fetchQuotations();
      }
    };

    window.addEventListener('focus', handleFocus);
    // Also listen for page visibility changes
    document.addEventListener('visibilitychange', () => {
      if (!document.hidden && id) {
        fetchOpportunity();
        fetchQuotations();
      }
    });

    return () => {
      window.removeEventListener('focus', handleFocus);
      document.removeEventListener('visibilitychange', handleFocus);
    };
  }, [id]);

  const fetchOpportunity = async () => {
    try {
      setLoading(true);
      setError(null);
      const token = localStorage.getItem('token');
      const response = await axios.get(`${baseURL}/api/opportunities/${id}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setOpportunity(response.data);
    } catch (error) {
      console.error('Error fetching opportunity:', error);
      setError('Failed to fetch opportunity details');
    } finally {
      setLoading(false);
    }
  };

  const fetchQuotations = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(`${baseURL}/api/opportunities/${id}/quotations`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setQuotations(response.data || []);
    } catch (error) {
      console.error('Error fetching quotations:', error);
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
    }
  };

  const getStageInfo = (stageId) => {
    // Handle both stage ID (UUID) and stage number (1-8)
    let stage;
    if (typeof stageId === 'number' || !isNaN(stageId)) {
      // If it's a number, find by stage_order
      stage = stages.find(s => s.stage_order === parseInt(stageId));
    } else {
      // If it's a UUID, find by ID
      stage = stages.find(s => s.id === stageId);
    }
    return stage ? { 
      name: stage.stage_name, 
      code: stage.stage_code,
      order: stage.stage_order 
    } : { name: 'Unknown', code: 'L0', order: 0 };
  };

  const getCompanyInfo = (companyId) => {
    const company = companies.find(c => c.id === companyId);
    return company ? {
      name: company.company_name,
      industry: company.industry,
      type: company.company_type
    } : { name: 'Unknown Company', industry: '', type: '' };
  };

  const getCurrencyInfo = (currencyId) => {
    const currency = currencies.find(c => c.id === currencyId);
    return currency ? {
      symbol: currency.symbol,
      code: currency.code,
      name: currency.name
    } : { symbol: '₹', code: 'INR', name: 'Indian Rupee' };
  };

  const getUserName = (userId) => {
    const user = users.find(u => u.id === userId);
    return user ? user.username : 'Unknown User';
  };

  const formatCurrency = (amount, currencyId = null) => {
    const currency = getCurrencyInfo(currencyId);
    return `${currency.symbol}${Number(amount).toLocaleString('en-IN')}`;
  };

  const getStatusBadgeColor = (status) => {
    if (!status) return 'bg-gray-100 text-gray-800 border-gray-200';
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

  const getQuotationStatusColor = (status) => {
    switch (status?.toLowerCase()) {
      case 'draft': return 'bg-gray-100 text-gray-800 border-gray-200';
      case 'approved': return 'bg-green-100 text-green-800 border-green-200';
      case 'rejected': return 'bg-red-100 text-red-800 border-red-200';
      case 'expired': return 'bg-orange-100 text-orange-800 border-orange-200';
      default: return 'bg-gray-100 text-gray-800 border-gray-200';
    }
  };

  const getProfitabilityColor = (percentage) => {
    if (percentage >= 50) return 'text-green-600';
    if (percentage >= 25) return 'text-yellow-600';
    if (percentage >= 0) return 'text-orange-600';
    return 'text-red-600';
  };

  const handleEdit = () => {
    navigate(`/opportunities/edit/${id}`);
  };

  const handleSelectQuotation = async (quotationId) => {
    try {
      const token = localStorage.getItem('token');
      await axios.patch(`${baseURL}/api/opportunities/${id}/quotations/${quotationId}/select`, {}, {
        headers: { Authorization: `Bearer ${token}` }
      });
      fetchQuotations(); // Refresh quotations list
    } catch (error) {
      console.error('Error selecting quotation:', error);
      alert('Error selecting quotation. Please try again.');
    }
  };

  const handleStageUpdate = () => {
    fetchOpportunity();
    fetchQuotations();
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
          <h2 className="text-2xl font-bold text-gray-900 mb-2">Opportunity Not Found</h2>
          <p className="text-gray-600 mb-4">The opportunity you're looking for doesn't exist or you don't have permission to view it.</p>
          <Button onClick={() => navigate('/opportunities')} variant="outline">
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back to Opportunities
          </Button>
        </div>
      </div>
    );
  }

  const currentStage = getStageInfo(opportunity.current_stage);
  const companyInfo = getCompanyInfo(opportunity.company_id);
  const currencyInfo = getCurrencyInfo(opportunity.currency_id);

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
            <h1 className="text-3xl font-bold text-gray-900">{opportunity.project_title}</h1>
            <p className="text-gray-600 mt-1">
              <span className="font-mono text-sm">{opportunity.opportunity_id}</span>
              {opportunity.lead_id && (
                <span className="ml-2 text-sm">
                  • Converted from Lead <span className="font-mono">{opportunity.lead_id}</span>
                </span>
              )}
            </p>
          </div>
        </div>
        <div className="flex items-center space-x-2">
          <Button 
            variant="outline"
            onClick={() => navigate(`/opportunities/${id}/stages`)}
            className="bg-purple-50 hover:bg-purple-100 text-purple-700 border-purple-200"
          >
            <Target className="w-4 h-4 mr-2" />
            Manage Stages
          </Button>
          {permissions.some(p => p.permission === 'Edit' && p.menu === 'Opportunities') && (
            <Button onClick={handleEdit} className="bg-blue-600 hover:bg-blue-700">
              <Edit className="w-4 h-4 mr-2" />
              Edit Details
            </Button>
          )}
        </div>
      </div>

      {/* Stage Ribbon */}
      <Card className="border-l-4 border-l-blue-500">
        <CardHeader>
          <CardTitle className="text-lg flex items-center gap-2">
            <Target className="w-5 h-5 text-blue-600" />
            Pipeline Stage Progress
          </CardTitle>
          <CardDescription>
            Current stage: {currentStage.code} - {currentStage.name}
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {/* Progress Bar */}
            <div className="relative">
              <Progress 
                value={(currentStage.order / 8) * 100} 
                className="h-3"
              />
              <div className="absolute inset-0 flex items-center justify-center">
                <span className="text-xs font-medium text-white">
                  Stage {currentStage.order} of 8
                </span>
              </div>
            </div>
            
            {/* Stage Badges */}
            <div className="flex flex-wrap gap-2">
              {stages
                .sort((a, b) => a.stage_order - b.stage_order)
                .map((stage) => (
                  <Badge 
                    key={stage.id}
                    variant={stage.id === opportunity.stage_id ? "default" : "outline"}
                    className={`${
                      stage.id === opportunity.stage_id
                        ? 'bg-blue-600 text-white border-blue-600'
                        : getStageBadgeColor(stage.stage_code)
                    } ${stage.stage_order <= currentStage.order ? 'opacity-100' : 'opacity-50'}`}
                  >
                    {stage.stage_code}
                  </Badge>
                ))}
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Summary Panel */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Expected Revenue</p>
                <p className="text-2xl font-bold text-green-600">
                  {formatCurrency(opportunity.expected_revenue, opportunity.currency_id)}
                </p>
              </div>
              <DollarSign className="h-8 w-8 text-green-500" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Weighted Revenue</p>
                <p className="text-2xl font-bold text-purple-600">
                  {formatCurrency(opportunity.weighted_revenue, opportunity.currency_id)}
                </p>
              </div>
              <TrendingUp className="h-8 w-8 text-purple-500" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Win Probability</p>
                <div className="flex items-center gap-2 mt-1">
                  <div className="w-16 bg-gray-200 rounded-full h-2">
                    <div 
                      className="bg-gradient-to-r from-red-500 via-yellow-500 to-green-500 h-2 rounded-full"
                      style={{ width: `${opportunity.win_probability}%` }}
                    ></div>
                  </div>
                  <span className="text-lg font-bold">{opportunity.win_probability}%</span>
                </div>
              </div>
              <Award className="h-8 w-8 text-orange-500" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Status</p>
                <Badge variant="outline" className={getStatusBadgeColor(opportunity.status)}>
                  {opportunity.status}
                </Badge>
              </div>
              <Target className="h-8 w-8 text-blue-500" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Main Content Tabs */}
      <Tabs defaultValue="overview" className="space-y-4">
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="quotations">
            Quotations ({quotations.length})
          </TabsTrigger>
          <TabsTrigger value="activities">Activities</TabsTrigger>
          <TabsTrigger value="documents">Documents</TabsTrigger>
        </TabsList>

        {/* Overview Tab */}
        <TabsContent value="overview" className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Opportunity Information */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <FileText className="w-5 h-5" />
                  Opportunity Information
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="text-sm font-medium text-gray-500">Project Title</label>
                    <p className="font-medium text-gray-900">{opportunity.project_title}</p>
                  </div>
                  <div>
                    <label className="text-sm font-medium text-gray-500">Opportunity ID</label>
                    <p className="font-mono text-sm text-blue-600">{opportunity.opportunity_id}</p>
                  </div>
                  <div>
                    <label className="text-sm font-medium text-gray-500">Current Stage</label>
                    <Badge variant="outline" className={getStageBadgeColor(currentStage.code)}>
                      {currentStage.code} - {currentStage.name}
                    </Badge>
                  </div>
                  <div>
                    <label className="text-sm font-medium text-gray-500">Status</label>
                    <Badge variant="outline" className={getStatusBadgeColor(opportunity.status)}>
                      {opportunity.status}
                    </Badge>
                  </div>
                </div>
                
                {opportunity.product_interest && (
                  <div>
                    <label className="text-sm font-medium text-gray-500">Product Interest</label>
                    <p className="text-gray-700 mt-1">{opportunity.product_interest}</p>
                  </div>
                )}
                
                {/* Stage-specific Information */}
                <div className="border-t pt-4">
                  <label className="text-sm font-medium text-gray-500 mb-2 block">Stage Progress Details</label>
                  <div className="space-y-2 text-sm">
                    {opportunity.region_id && (
                      <div className="flex justify-between">
                        <span className="text-gray-500">Region (L1):</span>
                        <span className="text-gray-900">Selected</span>
                      </div>
                    )}
                    {opportunity.budget && (
                      <div className="flex justify-between">
                        <span className="text-gray-500">Budget (L2):</span>
                        <span className="text-gray-900">{formatCurrency(parseFloat(opportunity.budget), opportunity.currency_id)}</span>
                      </div>
                    )}
                    {opportunity.qualification_status && (
                      <div className="flex justify-between">
                        <span className="text-gray-500">Qualification (L2):</span>
                        <span className="text-gray-900">{opportunity.qualification_status}</span>
                      </div>
                    )}
                    {opportunity.submission_date && (
                      <div className="flex justify-between">
                        <span className="text-gray-500">Proposal Submitted (L3):</span>
                        <span className="text-gray-900">{new Date(opportunity.submission_date).toLocaleDateString()}</span>
                      </div>
                    )}
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Company & Contact Information */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Building className="w-5 h-5" />
                  Company & Contact
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div>
                  <label className="text-sm font-medium text-gray-500">Company</label>
                  <p className="font-medium text-gray-900">{companyInfo.name}</p>
                  {companyInfo.industry && (
                    <p className="text-sm text-gray-600">{companyInfo.industry}</p>
                  )}
                </div>
                <div>
                  <label className="text-sm font-medium text-gray-500">Lead Owner</label>
                  <div className="flex items-center gap-2">
                    <User className="w-4 h-4 text-gray-400" />
                    <span className="text-gray-900">{getUserName(opportunity.lead_owner_id)}</span>
                  </div>
                </div>
                {opportunity.assigned_to_user_ids?.length > 0 && (
                  <div>
                    <label className="text-sm font-medium text-gray-500">Assigned Users</label>
                    <div className="flex items-center gap-2">
                      <Users className="w-4 h-4 text-gray-400" />
                      <span className="text-gray-900">
                        {opportunity.assigned_to_user_ids.length} user(s) assigned
                      </span>
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Financial Information */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <DollarSign className="w-5 h-5" />
                  Financial Details
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="text-sm font-medium text-gray-500">Expected Revenue</label>
                    <p className="text-lg font-semibold text-green-600">
                      {formatCurrency(opportunity.expected_revenue, opportunity.currency_id)}
                    </p>
                  </div>
                  <div>
                    <label className="text-sm font-medium text-gray-500">Weighted Revenue</label>
                    <p className="text-lg font-semibold text-purple-600">
                      {formatCurrency(opportunity.weighted_revenue, opportunity.currency_id)}
                    </p>
                  </div>
                  <div>
                    <label className="text-sm font-medium text-gray-500">Currency</label>
                    <p className="text-gray-900">{currencyInfo.name} ({currencyInfo.code})</p>
                  </div>
                  <div>
                    <label className="text-sm font-medium text-gray-500">Win Probability</label>
                    <div className="flex items-center gap-2">
                      <div className="w-20 bg-gray-200 rounded-full h-2">
                        <div 
                          className="bg-gradient-to-r from-red-500 via-yellow-500 to-green-500 h-2 rounded-full"
                          style={{ width: `${opportunity.win_probability}%` }}
                        ></div>
                      </div>
                      <span className="font-medium">{opportunity.win_probability}%</span>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Timeline Information */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Calendar className="w-5 h-5" />
                  Timeline
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div>
                  <label className="text-sm font-medium text-gray-500">Created</label>
                  <p className="text-gray-900">
                    {new Date(opportunity.created_at).toLocaleString('en-IN')}
                  </p>
                </div>
                <div>
                  <label className="text-sm font-medium text-gray-500">Last Updated</label>
                  <p className="text-gray-900">
                    {new Date(opportunity.updated_at).toLocaleString('en-IN')}
                  </p>
                </div>
                {opportunity.convert_date && (
                  <div>
                    <label className="text-sm font-medium text-gray-500">Converted Date</label>
                    <p className="text-gray-900">
                      {new Date(opportunity.convert_date).toLocaleString('en-IN')}
                    </p>
                  </div>
                )}
                {opportunity.close_date && (
                  <div>
                    <label className="text-sm font-medium text-gray-500">Expected Close Date</label>
                    <p className="text-gray-900">
                      {new Date(opportunity.close_date).toLocaleString('en-IN')}
                    </p>
                  </div>
                )}
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* Quotations Tab */}
        <TabsContent value="quotations" className="space-y-4">
          <div className="flex justify-between items-center">
            <h3 className="text-lg font-semibold">Quotations ({quotations.length})</h3>
            {/* Only show Create Quotation button in L4 stage (Proposal) */}
            {permissions.some(p => p.permission === 'Add' && p.menu === 'Opportunities') && 
             currentStage.code === 'L4' && (
              <Button 
                className="bg-blue-600 hover:bg-blue-700"
                onClick={() => navigate(`/opportunities/${id}/quotations/create`)}
              >
                <Plus className="w-4 h-4 mr-2" />
                Create Quotation
              </Button>
            )}
            {/* Show stage-specific messages */}
            {currentStage.code === 'L4' && quotations.length === 0 && (
              <div className="text-sm text-gray-700 bg-blue-50 border border-blue-200 rounded px-4 py-3">
                <div className="flex items-center gap-2 mb-2">
                  <div className="w-2 h-2 bg-blue-500 rounded-full"></div>
                  <strong>Ready for Quotation Creation</strong>
                </div>
                <p>This opportunity is in <strong>L4 - Proposal</strong> stage. You can now create detailed quotations with:</p>
                <ul className="mt-2 ml-4 text-xs space-y-1">
                  <li>• Multi-phase project structure</li>
                  <li>• Detailed item breakdown with pricing</li>
                  <li>• Real-time profitability calculations</li>
                  <li>• Professional quotation documents</li>
                </ul>
              </div>
            )}
            {currentStage.code !== 'L4' && (
              <div className="text-sm text-gray-600 bg-yellow-50 border border-yellow-200 rounded px-3 py-2">
                📋 Quotations can only be created in <strong>L4 - Proposal</strong> stage
              </div>
            )}
          </div>

          {quotations.length === 0 ? (
            <Card>
              <CardContent className="p-12 text-center">
                <FileText className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                <h3 className="text-lg font-medium text-gray-900 mb-2">No quotations yet</h3>
                {currentStage.code === 'L4' ? (
                  <>
                    <p className="text-gray-600 mb-2">Create your first quotation to start the proposal process</p>
                    <p className="text-sm text-gray-500 mb-4">
                      Build comprehensive quotations with phases, groups, and items. 
                      Track costs, calculate profitability, and manage multiple proposal options.
                    </p>
                    {permissions.some(p => p.permission === 'Add' && p.menu === 'Opportunities') && (
                      <Button 
                        className="bg-blue-600 hover:bg-blue-700"
                        onClick={() => navigate(`/opportunities/${id}/quotations/create`)}
                      >
                        <Plus className="w-4 h-4 mr-2" />
                        Create First Quotation
                      </Button>
                    )}
                  </>
                ) : (
                  <>
                    <p className="text-gray-600 mb-2">
                      Move opportunity to <strong>L4 - Proposal</strong> stage to create quotations
                    </p>
                    <p className="text-xs text-gray-500">
                      Complete L1-L3 stages to unlock quotation creation functionality
                    </p>
                  </>
                )}
              </CardContent>
            </Card>
          ) : (
            <div className="space-y-4">
              {/* Quotation Selection Info */}
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                <div className="flex items-center gap-2">
                  <Award className="w-5 h-5 text-blue-600" />
                  <h4 className="font-medium text-blue-900">Quotation Management</h4>
                </div>
                <p className="text-sm text-blue-700 mt-1">
                  You can create multiple quotations, but only <strong>one can be selected</strong> to proceed with the opportunity.
                </p>
              </div>
              
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {quotations.map((quotation) => (
                  <Card key={quotation.id} className="hover:shadow-md transition-shadow">
                    <CardHeader>
                      <div className="flex justify-between items-start">
                        <div>
                          <CardTitle className="text-lg">{quotation.quotation_name}</CardTitle>
                          <CardDescription className="font-mono text-sm">
                            {quotation.quotation_id}
                          </CardDescription>
                        </div>
                        <div className="flex flex-col gap-1">
                          <Badge variant="outline" className={getQuotationStatusColor(quotation.status)}>
                            {quotation.status}
                          </Badge>
                          {quotation.is_selected && (
                            <Badge className="bg-green-600 text-white">
                              Selected
                            </Badge>
                          )}
                        </div>
                      </div>
                    </CardHeader>
                    <CardContent>
                      <div className="space-y-3">
                        <div className="flex justify-between">
                          <span className="text-sm text-gray-600">Grand Total</span>
                          <span className="font-semibold">
                            {formatCurrency(quotation.grand_total, opportunity.currency_id)}
                          </span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-sm text-gray-600">Profitability</span>
                          <span className={`font-semibold ${getProfitabilityColor(quotation.profitability_percent)}`}>
                            {quotation.profitability_percent.toFixed(1)}%
                          </span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-sm text-gray-600">Version</span>
                          <span className="text-sm font-medium">v{quotation.version_no}</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-sm text-gray-600">Valid Until</span>
                          <span className="text-sm">
                            {new Date(quotation.validity_date).toLocaleDateString('en-IN')}
                          </span>
                        </div>
                        <div className="flex gap-2 pt-2">
                          <Button 
                            variant="outline" 
                            size="sm" 
                            className="flex-1"
                            onClick={() => navigate(`/opportunities/${id}/quotations/${quotation.id}`)}
                          >
                            <Eye className="w-4 h-4 mr-1" />
                            View
                          </Button>
                          <Button variant="outline" size="sm" className="flex-1">
                            <Download className="w-4 h-4 mr-1" />
                            Download
                          </Button>
                        </div>
                        {!quotation.is_selected && quotation.status === 'Approved' && (
                          <Button 
                            size="sm" 
                            className="w-full bg-green-600 hover:bg-green-700"
                            onClick={() => handleSelectQuotation(quotation.id)}
                          >
                            Select This Quotation
                          </Button>
                        )}
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            </div>
          )}
        </TabsContent>

        {/* Activities Tab */}
        <TabsContent value="activities">
          <Card>
            <CardContent className="p-12 text-center">
              <Calendar className="w-12 h-12 text-gray-400 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-gray-900 mb-2">Activity Timeline</h3>
              <p className="text-gray-600">Activity tracking will be implemented in the next phase</p>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Documents Tab */}
        <TabsContent value="documents">
          <Card>
            <CardContent className="p-12 text-center">
              <FileText className="w-12 h-12 text-gray-400 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-gray-900 mb-2">Document Management</h3>
              <p className="text-gray-600">Document management will be implemented in the next phase</p>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* Stage Management Dialog */}
      <Dialog open={stageDialogOpen} onOpenChange={setStageDialogOpen}>
        <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="text-xl font-bold text-gray-900">
              Stage Management
            </DialogTitle>
            <DialogDescription>
              Move this opportunity through the L1-L8 sales pipeline
            </DialogDescription>
          </DialogHeader>
          
          {opportunity && (
            <StageManagement
              opportunity={opportunity}
              stages={stages}
              currentStage={getStageInfo(opportunity.current_stage)}
              onStageUpdate={handleStageUpdate}
              onClose={() => setStageDialogOpen(false)}
            />
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default OpportunityDetail;