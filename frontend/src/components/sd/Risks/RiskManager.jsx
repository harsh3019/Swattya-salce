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
import { Progress } from '../../ui/progress';
import { 
  Plus, 
  Search, 
  Filter,
  AlertTriangle,
  Shield,
  TrendingUp,
  Clock,
  User,
  Calendar,
  DollarSign,
  Eye,
  Edit,
  Trash2,
  CheckCircle,
  AlertCircle,
  XCircle,
  Target,
  BarChart3,
  FileText,
  Users
} from 'lucide-react';
import { toast } from 'sonner';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

// Risk level colors
const RISK_LEVEL_COLORS = {
  'Critical': 'bg-red-100 text-red-800',
  'High': 'bg-orange-100 text-orange-800',
  'Medium': 'bg-yellow-100 text-yellow-800',
  'Low': 'bg-green-100 text-green-800'
};

// Status colors
const STATUS_COLORS = {
  'Identified': 'bg-blue-100 text-blue-800',
  'Analyzed': 'bg-purple-100 text-purple-800',
  'Planned': 'bg-indigo-100 text-indigo-800',
  'Mitigated': 'bg-green-100 text-green-800',
  'Closed': 'bg-gray-100 text-gray-800',
  'Realized': 'bg-red-100 text-red-800'
};

// Mitigation status colors
const MITIGATION_STATUS_COLORS = {
  'Not Started': 'bg-gray-100 text-gray-800',
  'In Progress': 'bg-blue-100 text-blue-800',
  'Completed': 'bg-green-100 text-green-800',
  'On Hold': 'bg-yellow-100 text-yellow-800',
  'Cancelled': 'bg-red-100 text-red-800'
};

const RiskManager = () => {
  const [risks, setRisks] = useState([]);
  const [summary, setSummary] = useState(null);
  const [overdueRisks, setOverdueRisks] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [filterCategory, setFilterCategory] = useState('');
  const [filterStatus, setFilterStatus] = useState('');
  const [filterRiskLevel, setFilterRiskLevel] = useState('');
  const [selectedRisk, setSelectedRisk] = useState(null);
  const [showCreateRisk, setShowCreateRisk] = useState(false);
  const [showAssessment, setShowAssessment] = useState(false);
  const [showReview, setShowReview] = useState(false);

  // Form states
  const [riskForm, setRiskForm] = useState({
    project_id: '',
    title: '',
    description: '',
    category: '',
    probability: '',
    impact: '',
    exposure_value: '',
    currency: 'USD',
    owner_id: '',
    mitigation_strategy: '',
    mitigation_actions: [],
    mitigation_cost: '',
    mitigation_timeline: '',
    contingency_plan: '',
    contingency_cost: '',
    trigger_conditions: [],
    review_frequency: '',
    next_review: '',
    tags: [],
    external_factors: [],
    stakeholders: [],
    notes: ''
  });

  const [assessmentForm, setAssessmentForm] = useState({
    probability: '',
    impact: '',
    comments: ''
  });

  const [reviewForm, setReviewForm] = useState({
    current_probability: '',
    current_impact: '',
    status_change: '',
    mitigation_effectiveness: '',
    recommendations: [],
    action_items: [],
    next_review_date: '',
    review_notes: '',
    attendees: []
  });

  useEffect(() => {
    fetchData();
  }, [filterCategory, filterStatus, filterRiskLevel]);

  const fetchData = async () => {
    try {
      setLoading(true);
      const token = localStorage.getItem('token');
      const headers = { Authorization: `Bearer ${token}` };

      // Build query parameters
      const params = new URLSearchParams();
      if (filterCategory && filterCategory !== 'all_categories') params.append('category', filterCategory);
      if (filterStatus && filterStatus !== 'all_statuses') params.append('status', filterStatus);
      if (filterRiskLevel && filterRiskLevel !== 'all_levels') params.append('risk_level', filterRiskLevel);
      
      const [risksRes, summaryRes, overdueRes] = await Promise.all([
        axios.get(`${BACKEND_URL}/api/sd/risks?${params.toString()}`, { headers }),
        axios.get(`${BACKEND_URL}/api/sd/risks/summary`, { headers }),
        axios.get(`${BACKEND_URL}/api/sd/risks/dashboard/overdue`, { headers })
      ]);

      setRisks(risksRes.data);
      setSummary(summaryRes.data);
      setOverdueRisks(overdueRes.data);
    } catch (error) {
      console.error('Error fetching risk data:', error);
      toast.error('Failed to fetch risk data');
    } finally {
      setLoading(false);
    }
  };

  const handleCreateRisk = async (e) => {
    e.preventDefault();
    try {
      const token = localStorage.getItem('token');
      const headers = { Authorization: `Bearer ${token}` };

      const formData = {
        ...riskForm,
        exposure_value: parseFloat(riskForm.exposure_value) || 0,
        mitigation_cost: parseFloat(riskForm.mitigation_cost) || 0,
        contingency_cost: parseFloat(riskForm.contingency_cost) || 0,
        mitigation_actions: Array.isArray(riskForm.mitigation_actions) 
          ? riskForm.mitigation_actions 
          : riskForm.mitigation_actions.split(',').map(a => a.trim()),
        trigger_conditions: Array.isArray(riskForm.trigger_conditions)
          ? riskForm.trigger_conditions
          : riskForm.trigger_conditions.split(',').map(t => t.trim()),
        tags: Array.isArray(riskForm.tags) 
          ? riskForm.tags 
          : riskForm.tags.split(',').map(t => t.trim()),
        external_factors: Array.isArray(riskForm.external_factors)
          ? riskForm.external_factors
          : riskForm.external_factors.split(',').map(f => f.trim()),
        stakeholders: Array.isArray(riskForm.stakeholders)
          ? riskForm.stakeholders
          : riskForm.stakeholders.split(',').map(s => s.trim()),
        next_review: riskForm.next_review || null
      };

      await axios.post(`${BACKEND_URL}/api/sd/risks/`, formData, { headers });
      
      toast.success('Risk created successfully');
      setShowCreateRisk(false);
      resetRiskForm();
      fetchData();
    } catch (error) {
      console.error('Error creating risk:', error);
      toast.error('Failed to create risk');
    }
  };

  const handleAssessRisk = async (e) => {
    e.preventDefault();
    if (!selectedRisk) return;

    try {
      const token = localStorage.getItem('token');
      const headers = { Authorization: `Bearer ${token}` };

      const params = new URLSearchParams({
        probability: assessmentForm.probability,
        impact: assessmentForm.impact
      });

      if (assessmentForm.comments) {
        params.append('comments', assessmentForm.comments);
      }

      await axios.post(
        `${BACKEND_URL}/api/sd/risks/${selectedRisk.id}/assess?${params.toString()}`, 
        {}, 
        { headers }
      );
      
      toast.success('Risk assessment completed');
      setShowAssessment(false);
      setAssessmentForm({ probability: '', impact: '', comments: '' });
      fetchData();
    } catch (error) {
      console.error('Error assessing risk:', error);
      toast.error('Failed to assess risk');
    }
  };

  const resetRiskForm = () => {
    setRiskForm({
      project_id: '',
      title: '',
      description: '',
      category: '',
      probability: '',
      impact: '',
      exposure_value: '',
      currency: 'USD',
      owner_id: '',
      mitigation_strategy: '',
      mitigation_actions: [],
      mitigation_cost: '',
      mitigation_timeline: '',
      contingency_plan: '',
      contingency_cost: '',
      trigger_conditions: [],
      review_frequency: '',
      next_review: '',
      tags: [],
      external_factors: [],
      stakeholders: [],
      notes: ''
    });
  };

  const getRiskLevel = (score) => {
    if (score >= 15) return 'Critical';
    if (score >= 10) return 'High';
    if (score >= 5) return 'Medium';
    return 'Low';
  };

  const filteredRisks = risks.filter(risk => {
    return risk.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
           risk.description.toLowerCase().includes(searchTerm.toLowerCase()) ||
           risk.category.toLowerCase().includes(searchTerm.toLowerCase());
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
        <h1 className="text-3xl font-bold text-slate-800 mb-2">Risk Management</h1>
        <p className="text-slate-600">Identify, assess, and mitigate project risks</p>
      </div>

      {/* Summary Cards */}
      {summary && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-6 mb-8">
          <Card className="border-0 shadow-sm bg-gradient-to-br from-blue-50 to-blue-100">
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-blue-600">Total Risks</p>
                  <p className="text-3xl font-bold text-blue-800 mt-2">{summary.total_risks}</p>
                </div>
                <Shield className="w-12 h-12 text-blue-600" />
              </div>
            </CardContent>
          </Card>
          
          <Card className="border-0 shadow-sm bg-gradient-to-br from-red-50 to-red-100">
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-red-600">Critical Risks</p>
                  <p className="text-3xl font-bold text-red-800 mt-2">{summary.critical_risks}</p>
                </div>
                <AlertTriangle className="w-12 h-12 text-red-600" />
              </div>
            </CardContent>
          </Card>
          
          <Card className="border-0 shadow-sm bg-gradient-to-br from-orange-50 to-orange-100">
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-orange-600">High Risks</p>
                  <p className="text-3xl font-bold text-orange-800 mt-2">{summary.high_risks}</p>
                </div>
                <TrendingUp className="w-12 h-12 text-orange-600" />
              </div>
            </CardContent>
          </Card>
          
          <Card className="border-0 shadow-sm bg-gradient-to-br from-purple-50 to-purple-100">
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-purple-600">Overdue Reviews</p>
                  <p className="text-3xl font-bold text-purple-800 mt-2">{summary.overdue_reviews}</p>
                </div>
                <Clock className="w-12 h-12 text-purple-600" />
              </div>
            </CardContent>
          </Card>
          
          <Card className="border-0 shadow-sm bg-gradient-to-br from-green-50 to-green-100">
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-green-600">Avg. Risk Score</p>
                  <p className="text-3xl font-bold text-green-800 mt-2">{summary.average_risk_score}</p>
                </div>
                <BarChart3 className="w-12 h-12 text-green-600" />
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      <Tabs defaultValue="risks" className="w-full">
        <TabsList className="grid w-full grid-cols-3">
          <TabsTrigger value="risks">Risk Register</TabsTrigger>
          <TabsTrigger value="overdue">Overdue Reviews</TabsTrigger>
          <TabsTrigger value="matrix">Risk Matrix</TabsTrigger>
        </TabsList>

        {/* Risk Register Tab */}
        <TabsContent value="risks" className="space-y-6">
          {/* Filters and Actions */}
          <div className="flex flex-col sm:flex-row gap-4 items-start sm:items-center justify-between">
            <div className="flex flex-col sm:flex-row gap-4 flex-1">
              <div className="relative flex-1 max-w-sm">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
                <Input
                  placeholder="Search risks..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="pl-10"
                />
              </div>
              
              <Select value={filterCategory} onValueChange={setFilterCategory}>
                <SelectTrigger className="w-[180px]">
                  <SelectValue placeholder="Filter by category" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all_categories">All Categories</SelectItem>
                  <SelectItem value="technical">Technical</SelectItem>
                  <SelectItem value="operational">Operational</SelectItem>
                  <SelectItem value="financial">Financial</SelectItem>
                  <SelectItem value="legal">Legal</SelectItem>
                  <SelectItem value="market">Market</SelectItem>
                  <SelectItem value="resource">Resource</SelectItem>
                  <SelectItem value="schedule">Schedule</SelectItem>
                  <SelectItem value="quality">Quality</SelectItem>
                </SelectContent>
              </Select>
              
              <Select value={filterStatus} onValueChange={setFilterStatus}>
                <SelectTrigger className="w-[180px]">
                  <SelectValue placeholder="Filter by status" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all_statuses">All Statuses</SelectItem>
                  <SelectItem value="Identified">Identified</SelectItem>
                  <SelectItem value="Analyzed">Analyzed</SelectItem>
                  <SelectItem value="Planned">Planned</SelectItem>
                  <SelectItem value="Mitigated">Mitigated</SelectItem>
                  <SelectItem value="Closed">Closed</SelectItem>
                  <SelectItem value="Realized">Realized</SelectItem>
                </SelectContent>
              </Select>
              
              <Select value={filterRiskLevel} onValueChange={setFilterRiskLevel}>
                <SelectTrigger className="w-[180px]">
                  <SelectValue placeholder="Filter by risk level" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all_levels">All Risk Levels</SelectItem>
                  <SelectItem value="Critical">Critical</SelectItem>
                  <SelectItem value="High">High</SelectItem>
                  <SelectItem value="Medium">Medium</SelectItem>
                  <SelectItem value="Low">Low</SelectItem>
                </SelectContent>
              </Select>
            </div>
            
            <Dialog open={showCreateRisk} onOpenChange={setShowCreateRisk}>
              <DialogTrigger asChild>
                <Button>
                  <Plus className="w-4 h-4 mr-2" />
                  Add Risk
                </Button>
              </DialogTrigger>
              <DialogContent className="max-w-4xl max-h-[80vh] overflow-y-auto">
                <DialogHeader>
                  <DialogTitle>Create New Risk</DialogTitle>
                  <DialogDescription>
                    Identify a new risk for the project
                  </DialogDescription>
                </DialogHeader>
                <form onSubmit={handleCreateRisk} className="space-y-4">
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <Label htmlFor="title">Risk Title *</Label>
                      <Input
                        id="title"
                        value={riskForm.title}
                        onChange={(e) => setRiskForm({...riskForm, title: e.target.value})}
                        placeholder="Enter risk title"
                        required
                      />
                    </div>
                    
                    <div>
                      <Label htmlFor="category">Category *</Label>
                      <Select value={riskForm.category} onValueChange={(value) => setRiskForm({...riskForm, category: value})}>
                        <SelectTrigger>
                          <SelectValue placeholder="Select category" />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="technical">Technical</SelectItem>
                          <SelectItem value="operational">Operational</SelectItem>
                          <SelectItem value="financial">Financial</SelectItem>
                          <SelectItem value="legal">Legal</SelectItem>
                          <SelectItem value="market">Market</SelectItem>
                          <SelectItem value="resource">Resource</SelectItem>
                          <SelectItem value="schedule">Schedule</SelectItem>
                          <SelectItem value="quality">Quality</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                  </div>
                  
                  <div>
                    <Label htmlFor="description">Description *</Label>
                    <Textarea
                      id="description"
                      value={riskForm.description}
                      onChange={(e) => setRiskForm({...riskForm, description: e.target.value})}
                      placeholder="Detailed risk description"
                      required
                    />
                  </div>
                  
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <Label htmlFor="probability">Probability *</Label>
                      <Select value={riskForm.probability} onValueChange={(value) => setRiskForm({...riskForm, probability: value})}>
                        <SelectTrigger>
                          <SelectValue placeholder="Select probability" />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="Very Low">Very Low (1)</SelectItem>
                          <SelectItem value="Low">Low (2)</SelectItem>
                          <SelectItem value="Medium">Medium (3)</SelectItem>
                          <SelectItem value="High">High (4)</SelectItem>
                          <SelectItem value="Very High">Very High (5)</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                    
                    <div>
                      <Label htmlFor="impact">Impact *</Label>
                      <Select value={riskForm.impact} onValueChange={(value) => setRiskForm({...riskForm, impact: value})}>
                        <SelectTrigger>
                          <SelectValue placeholder="Select impact" />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="Negligible">Negligible (1)</SelectItem>
                          <SelectItem value="Minor">Minor (2)</SelectItem>
                          <SelectItem value="Moderate">Moderate (3)</SelectItem>
                          <SelectItem value="Major">Major (4)</SelectItem>
                          <SelectItem value="Catastrophic">Catastrophic (5)</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                  </div>
                  
                  <div className="grid grid-cols-3 gap-4">
                    <div>
                      <Label htmlFor="exposure_value">Financial Exposure</Label>
                      <Input
                        id="exposure_value"
                        type="number"
                        step="0.01"
                        value={riskForm.exposure_value}
                        onChange={(e) => setRiskForm({...riskForm, exposure_value: e.target.value})}
                        placeholder="0.00"
                      />
                    </div>
                    
                    <div>
                      <Label htmlFor="currency">Currency</Label>
                      <Select value={riskForm.currency} onValueChange={(value) => setRiskForm({...riskForm, currency: value})}>
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
                    
                    <div>
                      <Label htmlFor="project_id">Project ID *</Label>
                      <Input
                        id="project_id"
                        value={riskForm.project_id}
                        onChange={(e) => setRiskForm({...riskForm, project_id: e.target.value})}
                        placeholder="Enter project ID"
                        required
                      />
                    </div>
                  </div>
                  
                  <div>
                    <Label htmlFor="mitigation_strategy">Mitigation Strategy</Label>
                    <Textarea
                      id="mitigation_strategy"
                      value={riskForm.mitigation_strategy}
                      onChange={(e) => setRiskForm({...riskForm, mitigation_strategy: e.target.value})}
                      placeholder="Describe the mitigation strategy"
                    />
                  </div>
                  
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <Label htmlFor="review_frequency">Review Frequency</Label>
                      <Select value={riskForm.review_frequency} onValueChange={(value) => setRiskForm({...riskForm, review_frequency: value})}>
                        <SelectTrigger>
                          <SelectValue placeholder="Select frequency" />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="Weekly">Weekly</SelectItem>
                          <SelectItem value="Bi-weekly">Bi-weekly</SelectItem>
                          <SelectItem value="Monthly">Monthly</SelectItem>
                          <SelectItem value="Quarterly">Quarterly</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                    
                    <div>
                      <Label htmlFor="next_review">Next Review Date</Label>
                      <Input
                        id="next_review"
                        type="date"
                        value={riskForm.next_review}
                        onChange={(e) => setRiskForm({...riskForm, next_review: e.target.value})}
                      />
                    </div>
                  </div>
                  
                  <div className="flex justify-end space-x-2">
                    <Button type="button" variant="outline" onClick={() => setShowCreateRisk(false)}>
                      Cancel
                    </Button>
                    <Button type="submit">Create Risk</Button>
                  </div>
                </form>
              </DialogContent>
            </Dialog>
          </div>

          {/* Risks Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {filteredRisks.map((risk) => {
              const riskLevel = getRiskLevel(risk.risk_score || 0);
              
              return (
                <Card key={risk.id} className="border hover:shadow-md transition-shadow">
                  <CardHeader className="pb-3">
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <CardTitle className="text-lg mb-1">{risk.title}</CardTitle>
                        <p className="text-sm text-gray-500">{risk.risk_id}</p>
                      </div>
                      <div className="flex flex-col gap-2">
                        <Badge className={RISK_LEVEL_COLORS[riskLevel] || 'bg-gray-100 text-gray-800'}>
                          {riskLevel}
                        </Badge>
                        <Badge className={STATUS_COLORS[risk.status] || 'bg-gray-100 text-gray-800'}>
                          {risk.status}
                        </Badge>
                      </div>
                    </div>
                  </CardHeader>
                  
                  <CardContent>
                    <div className="space-y-3">
                      <div className="flex justify-between items-center">
                        <span className="text-sm text-gray-600">Category</span>
                        <span className="text-sm font-medium capitalize">{risk.category}</span>
                      </div>
                      
                      <div className="flex justify-between items-center">
                        <span className="text-sm text-gray-600">Risk Score</span>
                        <span className="text-sm font-medium">{risk.risk_score || 0}/25</span>
                      </div>
                      
                      <div className="flex justify-between items-center">
                        <span className="text-sm text-gray-600">Probability</span>
                        <span className="text-sm font-medium">{risk.probability}</span>
                      </div>
                      
                      <div className="flex justify-between items-center">
                        <span className="text-sm text-gray-600">Impact</span>
                        <span className="text-sm font-medium">{risk.impact}</span>
                      </div>
                      
                      {risk.exposure_value > 0 && (
                        <div className="flex justify-between items-center">
                          <span className="text-sm text-gray-600">Exposure</span>
                          <span className="text-sm font-medium">
                            {risk.currency} {risk.exposure_value.toFixed(2)}
                          </span>
                        </div>
                      )}
                      
                      {risk.mitigation_status && (
                        <div className="flex justify-between items-center">
                          <span className="text-sm text-gray-600">Mitigation</span>
                          <Badge className={MITIGATION_STATUS_COLORS[risk.mitigation_status] || 'bg-gray-100 text-gray-800'}>
                            {risk.mitigation_status}
                          </Badge>
                        </div>
                      )}
                      
                      {/* Risk Score Progress Bar */}
                      <div className="w-full">
                        <div className="flex justify-between items-center mb-1">
                          <span className="text-xs text-gray-500">Risk Level</span>
                          <span className="text-xs text-gray-500">{((risk.risk_score || 0) / 25 * 100).toFixed(0)}%</span>
                        </div>
                        <Progress 
                          value={(risk.risk_score || 0) / 25 * 100} 
                          className="h-2"
                        />
                      </div>
                    </div>
                    
                    <div className="flex justify-end space-x-2 mt-4">
                      <Button 
                        size="sm" 
                        variant="outline"
                        onClick={() => {
                          setSelectedRisk(risk);
                          setShowAssessment(true);
                        }}
                      >
                        <Target className="w-4 h-4" />
                      </Button>
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
          
          {filteredRisks.length === 0 && (
            <Card className="border-dashed border-2 border-gray-300">
              <CardContent className="flex flex-col items-center justify-center py-12">
                <Shield className="w-12 h-12 text-gray-400 mb-4" />
                <p className="text-lg font-medium text-gray-600 mb-2">No Risks Found</p>
                <p className="text-sm text-gray-500 mb-4">
                  {searchTerm || filterCategory || filterStatus || filterRiskLevel
                    ? 'Try adjusting your search criteria' 
                    : 'Get started by identifying your first risk'
                  }
                </p>
                {!searchTerm && !filterCategory && !filterStatus && !filterRiskLevel && (
                  <Button onClick={() => setShowCreateRisk(true)}>
                    <Plus className="w-4 h-4 mr-2" />
                    Add First Risk
                  </Button>
                )}
              </CardContent>
            </Card>
          )}
        </TabsContent>

        {/* Overdue Reviews Tab */}
        <TabsContent value="overdue" className="space-y-6">
          <div className="flex justify-between items-center">
            <div>
              <h2 className="text-xl font-semibold">Overdue Risk Reviews</h2>
              <p className="text-sm text-gray-600">Risks that require immediate review attention</p>
            </div>
          </div>
          
          <div className="space-y-4">
            {overdueRisks.map((risk) => (
              <Card key={risk.id} className="border-l-4 border-l-red-500 hover:shadow-sm transition-shadow">
                <CardContent className="p-6">
                  <div className="flex items-start justify-between">
                    <div className="flex items-start space-x-4">
                      <div className="w-10 h-10 bg-red-100 rounded-lg flex items-center justify-center">
                        <Clock className="w-5 h-5 text-red-600" />
                      </div>
                      <div>
                        <h3 className="font-medium text-lg">{risk.title}</h3>
                        <p className="text-sm text-gray-500 mb-2">{risk.risk_id}</p>
                        <div className="flex items-center space-x-4 text-sm text-gray-600">
                          <span>Category: {risk.category}</span>
                          <span>Score: {risk.risk_score}/25</span>
                          <span>Due: {new Date(risk.next_review).toLocaleDateString()}</span>
                        </div>
                      </div>
                    </div>
                    
                    <div className="text-right">
                      <Badge className={RISK_LEVEL_COLORS[getRiskLevel(risk.risk_score)] || 'bg-gray-100 text-gray-800'}>
                        {getRiskLevel(risk.risk_score)}
                      </Badge>
                      <Button 
                        size="sm" 
                        className="mt-2"
                        onClick={() => {
                          setSelectedRisk(risk);
                          setShowReview(true);
                        }}
                      >
                        Review Now
                      </Button>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
            
            {overdueRisks.length === 0 && (
              <Card className="border-dashed border-2 border-gray-300">
                <CardContent className="flex flex-col items-center justify-center py-12">
                  <CheckCircle className="w-12 h-12 text-green-400 mb-4" />
                  <p className="text-lg font-medium text-gray-600 mb-2">All Reviews Up to Date</p>
                  <p className="text-sm text-gray-500">
                    Great job! All risk reviews are current.
                  </p>
                </CardContent>
              </Card>
            )}
          </div>
        </TabsContent>

        {/* Risk Matrix Tab */}
        <TabsContent value="matrix" className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Card>
              <CardHeader>
                <CardTitle>Risk Scoring Matrix</CardTitle>
                <CardDescription>Probability × Impact = Risk Score</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-6 gap-2 text-xs">
                  <div></div>
                  <div className="font-semibold text-center">1</div>
                  <div className="font-semibold text-center">2</div>
                  <div className="font-semibold text-center">3</div>
                  <div className="font-semibold text-center">4</div>
                  <div className="font-semibold text-center">5</div>
                  
                  <div className="font-semibold">5</div>
                  <div className="bg-yellow-200 p-2 text-center">5</div>
                  <div className="bg-orange-200 p-2 text-center">10</div>
                  <div className="bg-red-200 p-2 text-center">15</div>
                  <div className="bg-red-400 p-2 text-center">20</div>
                  <div className="bg-red-600 text-white p-2 text-center">25</div>
                  
                  <div className="font-semibold">4</div>
                  <div className="bg-green-200 p-2 text-center">4</div>
                  <div className="bg-yellow-200 p-2 text-center">8</div>
                  <div className="bg-orange-200 p-2 text-center">12</div>
                  <div className="bg-red-200 p-2 text-center">16</div>
                  <div className="bg-red-400 text-white p-2 text-center">20</div>
                  
                  <div className="font-semibold">3</div>
                  <div className="bg-green-200 p-2 text-center">3</div>
                  <div className="bg-yellow-200 p-2 text-center">6</div>
                  <div className="bg-yellow-200 p-2 text-center">9</div>
                  <div className="bg-orange-200 p-2 text-center">12</div>
                  <div className="bg-red-200 p-2 text-center">15</div>
                  
                  <div className="font-semibold">2</div>
                  <div className="bg-green-200 p-2 text-center">2</div>
                  <div className="bg-green-200 p-2 text-center">4</div>
                  <div className="bg-yellow-200 p-2 text-center">6</div>
                  <div className="bg-yellow-200 p-2 text-center">8</div>
                  <div className="bg-orange-200 p-2 text-center">10</div>
                  
                  <div className="font-semibold">1</div>
                  <div className="bg-green-200 p-2 text-center">1</div>
                  <div className="bg-green-200 p-2 text-center">2</div>
                  <div className="bg-green-200 p-2 text-center">3</div>
                  <div className="bg-green-200 p-2 text-center">4</div>
                  <div className="bg-yellow-200 p-2 text-center">5</div>
                </div>
                <div className="mt-4 text-xs text-gray-600">
                  <p>Probability (1-5) × Impact (1-5) = Risk Score (1-25)</p>
                </div>
              </CardContent>
            </Card>
            
            <Card>
              <CardHeader>
                <CardTitle>Risk Level Definitions</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex items-center space-x-3">
                  <div className="w-4 h-4 bg-green-500 rounded"></div>
                  <div>
                    <p className="font-medium">Low (1-4)</p>
                    <p className="text-sm text-gray-600">Acceptable risk, monitor regularly</p>
                  </div>
                </div>
                <div className="flex items-center space-x-3">
                  <div className="w-4 h-4 bg-yellow-500 rounded"></div>
                  <div>
                    <p className="font-medium">Medium (5-9)</p>
                    <p className="text-sm text-gray-600">Manage and mitigate where possible</p>
                  </div>
                </div>
                <div className="flex items-center space-x-3">
                  <div className="w-4 h-4 bg-orange-500 rounded"></div>
                  <div>
                    <p className="font-medium">High (10-14)</p>
                    <p className="text-sm text-gray-600">Requires active management and mitigation</p>
                  </div>
                </div>
                <div className="flex items-center space-x-3">
                  <div className="w-4 h-4 bg-red-500 rounded"></div>
                  <div>
                    <p className="font-medium">Critical (15-25)</p>
                    <p className="text-sm text-gray-600">Immediate action required, escalate to management</p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>
      </Tabs>

      {/* Risk Assessment Dialog */}
      <Dialog open={showAssessment} onOpenChange={setShowAssessment}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Assess Risk</DialogTitle>
            <DialogDescription>
              Update the probability and impact assessment for {selectedRisk?.title}
            </DialogDescription>
          </DialogHeader>
          <form onSubmit={handleAssessRisk} className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label htmlFor="assess_probability">Probability</Label>
                <Select value={assessmentForm.probability} onValueChange={(value) => setAssessmentForm({...assessmentForm, probability: value})}>
                  <SelectTrigger>
                    <SelectValue placeholder="Select probability" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="Very Low">Very Low (1)</SelectItem>
                    <SelectItem value="Low">Low (2)</SelectItem>
                    <SelectItem value="Medium">Medium (3)</SelectItem>
                    <SelectItem value="High">High (4)</SelectItem>
                    <SelectItem value="Very High">Very High (5)</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              
              <div>
                <Label htmlFor="assess_impact">Impact</Label>
                <Select value={assessmentForm.impact} onValueChange={(value) => setAssessmentForm({...assessmentForm, impact: value})}>
                  <SelectTrigger>
                    <SelectValue placeholder="Select impact" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="Negligible">Negligible (1)</SelectItem>
                    <SelectItem value="Minor">Minor (2)</SelectItem>
                    <SelectItem value="Moderate">Moderate (3)</SelectItem>
                    <SelectItem value="Major">Major (4)</SelectItem>
                    <SelectItem value="Catastrophic">Catastrophic (5)</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>
            
            <div>
              <Label htmlFor="assess_comments">Assessment Comments</Label>
              <Textarea
                id="assess_comments"
                value={assessmentForm.comments}
                onChange={(e) => setAssessmentForm({...assessmentForm, comments: e.target.value})}
                placeholder="Optional assessment comments"
              />
            </div>
            
            <div className="flex justify-end space-x-2">
              <Button type="button" variant="outline" onClick={() => setShowAssessment(false)}>
                Cancel
              </Button>
              <Button type="submit">Update Assessment</Button>
            </div>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default RiskManager;