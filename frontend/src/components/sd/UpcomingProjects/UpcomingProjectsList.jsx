import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { Card, CardContent, CardHeader, CardTitle } from '../../ui/card';
import { Badge } from '../../ui/badge';
import { Button } from '../../ui/button';
import { Input } from '../../ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../../ui/select';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../../ui/table';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from '../../ui/dialog';
import { 
  CheckCircle, 
  AlertTriangle, 
  Clock, 
  FileText, 
  ArrowRight, 
  Search,
  Filter,
  Plus,
  Eye,
  RefreshCcw,
  Check,
  X,
  AlertCircle,
  Shield,
  DollarSign
} from 'lucide-react';
import { toast } from 'sonner';

const baseURL = process.env.REACT_APP_BACKEND_URL || import.meta.env.REACT_APP_BACKEND_URL;

const UpcomingProjectsList = () => {
  const navigate = useNavigate();
  const [projects, setProjects] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  const [refreshing, setRefreshing] = useState(false);
  
  // Action states
  const [selectedProject, setSelectedProject] = useState(null);
  const [showDetailsModal, setShowDetailsModal] = useState(false);
  const [showConvertModal, setShowConvertModal] = useState(false);
  const [showRejectModal, setShowRejectModal] = useState(false);
  const [actionLoading, setActionLoading] = useState(false);

  // Stats state
  const [stats, setStats] = useState({
    total: 0,
    pending: 0,
    validated: 0,
    converted: 0,
    rejected: 0
  });

  useEffect(() => {
    fetchProjects();
  }, [statusFilter]);

  const fetchProjects = async () => {
    try {
      setLoading(true);
      const token = localStorage.getItem('token');
      
      const params = new URLSearchParams();
      if (statusFilter !== 'all') {
        params.append('status', statusFilter);
      }
      
      const response = await axios.get(`${baseURL}/api/sd/upcoming-projects/?${params.toString()}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      setProjects(response.data);
      calculateStats(response.data);
      setError(null);
    } catch (error) {
      console.error('Error fetching upcoming projects:', error);
      setError('Failed to fetch upcoming projects');
    } finally {
      setLoading(false);
    }
  };

  const calculateStats = (projectsData) => {
    const stats = {
      total: projectsData.length,
      pending: 0,
      validated: 0,
      converted: 0,
      rejected: 0
    };

    projectsData.forEach(project => {
      switch (project.order_status) {
        case 'Pending':
          stats.pending++;
          break;
        case 'Converted':
          stats.converted++;
          break;
        case 'Rejected':
          stats.rejected++;
          break;
        default:
          break;
      }
      
      if (project.validation_status === 'Valid') {
        stats.validated++;
      }
    });

    setStats(stats);
  };

  const handleRefresh = async () => {
    setRefreshing(true);
    await fetchProjects();
    setRefreshing(false);
  };

  const handleViewDetails = async (project) => {
    setSelectedProject(project);
    
    // Fetch additional opportunity and quotation details
    try {
      const token = localStorage.getItem('token');
      const headers = { Authorization: `Bearer ${token}` };
      
      // Fetch opportunity details
      if (project.opp_id) {
        const oppResponse = await axios.get(`${baseURL}/api/opportunities?opportunity_id=${project.opp_id}`, { headers });
        if (oppResponse.data && oppResponse.data.length > 0) {
          setSelectedProject(prev => ({
            ...prev,
            opportunity_details: oppResponse.data[0]
          }));
        }
      }
      
      // Fetch quotation details for this opportunity
      if (project.opp_id) {
        const quotationResponse = await axios.get(`${baseURL}/api/quotations?opportunity_id=${project.opp_id}`, { headers });
        if (quotationResponse.data) {
          setSelectedProject(prev => ({
            ...prev,
            quotations: quotationResponse.data
          }));
        }
      }
      
    } catch (error) {
      console.error('Error fetching additional details:', error);
    }
    
    setShowDetailsModal(true);
  };

  const handleConvertToProject = async (project) => {
    try {
      setActionLoading(true);
      const token = localStorage.getItem('token');
      
      const response = await axios.post(
        `${baseURL}/api/sd/upcoming-projects/${project.id}/convert`,
        {},
        { headers: { Authorization: `Bearer ${token}` } }
      );
      
      if (response.status === 200) {
        toast.success('Project converted successfully!');
        setShowConvertModal(false);
        setSelectedProject(null);
        await fetchProjects(); // Refresh the list
      }
    } catch (error) {
      console.error('Error converting project:', error);
      toast.error(error.response?.data?.detail || 'Failed to convert project');
    } finally {
      setActionLoading(false);
    }
  };

  const handleRejectProject = async (project, reason = '') => {
    try {
      setActionLoading(true);
      const token = localStorage.getItem('token');
      
      const response = await axios.post(
        `${baseURL}/api/sd/upcoming-projects/${project.id}/reject`,
        { reason },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      
      if (response.status === 200) {
        toast.success('Project rejected successfully');
        setShowRejectModal(false);
        setSelectedProject(null);
        await fetchProjects(); // Refresh the list
      }
    } catch (error) {
      console.error('Error rejecting project:', error);
      toast.error(error.response?.data?.detail || 'Failed to reject project');
    } finally {
      setActionLoading(false);
    }
  };

  const filteredProjects = projects.filter(project =>
    (project.customer_name?.toLowerCase().includes(searchTerm.toLowerCase()) || false) ||
    (project.order_id?.toLowerCase().includes(searchTerm.toLowerCase()) || false) ||
    (project.pot_id?.toLowerCase().includes(searchTerm.toLowerCase()) || false)
  );

  const getStatusBadge = (status) => {
    const statusConfig = {
      'Pending': { color: 'bg-yellow-100 text-yellow-800', icon: Clock },
      'Converted': { color: 'bg-green-100 text-green-800', icon: CheckCircle },
      'Rejected': { color: 'bg-red-100 text-red-800', icon: AlertTriangle }
    };

    const config = statusConfig[status] || { color: 'bg-gray-100 text-gray-800', icon: Clock };
    const IconComponent = config.icon;

    return (
      <Badge className={`${config.color} flex items-center gap-1`}>
        <IconComponent className="w-3 h-3" />
        {status}
      </Badge>
    );
  };

  const getValidationBadge = (status) => {
    const statusConfig = {
      'Valid': { color: 'bg-green-100 text-green-800', icon: CheckCircle },
      'Invalid': { color: 'bg-red-100 text-red-800', icon: AlertTriangle },
      'Pending GC Sign-off': { color: 'bg-blue-100 text-blue-800', icon: Clock }
    };

    const config = statusConfig[status] || { color: 'bg-gray-100 text-gray-800', icon: Clock };
    const IconComponent = config.icon;

    return (
      <Badge className={`${config.color} flex items-center gap-1`}>
        <IconComponent className="w-3 h-3" />
        {status}
      </Badge>
    );
  };

  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(amount);
  };

  const formatDate = (dateString) => {
    if (!dateString) return 'Not set';
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    });
  };

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <h1 className="text-3xl font-bold text-gray-900">Upcoming Projects</h1>
        </div>
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <h1 className="text-3xl font-bold text-gray-900">Upcoming Projects</h1>
        </div>
        <Card>
          <CardContent className="p-6">
            <div className="text-center">
              <AlertTriangle className="mx-auto h-12 w-12 text-red-500" />
              <h3 className="mt-2 text-lg font-medium text-gray-900">Error Loading Projects</h3>
              <p className="mt-1 text-gray-500">{error}</p>
              <Button onClick={fetchProjects} className="mt-4">
                <RefreshCcw className="w-4 h-4 mr-2" />
                Try Again
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Upcoming Projects</h1>
          <p className="text-gray-600 mt-1">
            Manage project validation and conversion from won opportunities
          </p>
        </div>
        <div className="flex items-center gap-3">
          <Button
            onClick={handleRefresh}
            variant="outline"
            disabled={refreshing}
          >
            <RefreshCcw className={`w-4 h-4 mr-2 ${refreshing ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Total Projects</p>
                <p className="text-2xl font-bold text-gray-900">{stats.total}</p>
              </div>
              <FileText className="h-8 w-8 text-blue-500" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Pending</p>
                <p className="text-2xl font-bold text-yellow-600">{stats.pending}</p>
              </div>
              <Clock className="h-8 w-8 text-yellow-500" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Validated</p>
                <p className="text-2xl font-bold text-green-600">{stats.validated}</p>
              </div>
              <CheckCircle className="h-8 w-8 text-green-500" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Converted</p>
                <p className="text-2xl font-bold text-blue-600">{stats.converted}</p>
              </div>
              <ArrowRight className="h-8 w-8 text-blue-500" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Rejected</p>
                <p className="text-2xl font-bold text-red-600">{stats.rejected}</p>
              </div>
              <AlertTriangle className="h-8 w-8 text-red-500" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Filters */}
      <Card>
        <CardContent className="p-4">
          <div className="flex flex-col sm:flex-row gap-4">
            <div className="flex-1">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 h-4 w-4" />
                <Input
                  placeholder="Search by customer, order ID, or POT ID..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="pl-10"
                />
              </div>
            </div>
            <div className="w-48">
              <Select value={statusFilter} onValueChange={setStatusFilter}>
                <SelectTrigger>
                  <Filter className="w-4 h-4 mr-2" />
                  <SelectValue placeholder="Filter by status" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Status</SelectItem>
                  <SelectItem value="Pending">Pending</SelectItem>
                  <SelectItem value="Converted">Converted</SelectItem>
                  <SelectItem value="Rejected">Rejected</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Projects Table */}
      <Card>
        <CardHeader>
          <CardTitle>Projects List ({filteredProjects.length})</CardTitle>
        </CardHeader>
        <CardContent>
          {filteredProjects.length === 0 ? (
            <div className="text-center py-12">
              <FileText className="mx-auto h-12 w-12 text-gray-400" />
              <h3 className="mt-2 text-lg font-medium text-gray-900">No projects found</h3>
              <p className="mt-1 text-gray-500">
                {searchTerm || statusFilter !== 'all' 
                  ? 'Try adjusting your search or filter criteria.' 
                  : 'Won opportunities will automatically appear here.'}
              </p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Customer</TableHead>
                    <TableHead>Order ID</TableHead>
                    <TableHead>POT ID</TableHead>
                    <TableHead>Setup Cost</TableHead>
                    <TableHead>Order Status</TableHead>
                    <TableHead>Validation</TableHead>
                    <TableHead>GC Signoff</TableHead>
                    <TableHead>Created</TableHead>
                    <TableHead>Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {filteredProjects.map((project) => (
                    <TableRow key={project.id}>
                      <TableCell>
                        <div>
                          <div className="font-medium text-gray-900">
                            {project.customer_name || 'Unknown Customer'}
                          </div>
                          <div className="text-sm text-gray-500">
                            {project.opp_id || 'N/A'}
                          </div>
                        </div>
                      </TableCell>
                      <TableCell>
                        <code className="text-sm bg-gray-100 px-2 py-1 rounded">
                          {project.order_id || 'N/A'}
                        </code>
                      </TableCell>
                      <TableCell>
                        <code className="text-sm bg-blue-100 px-2 py-1 rounded">
                          {project.pot_id || 'N/A'}
                        </code>
                      </TableCell>
                      <TableCell>
                        <div className="font-medium">
                          {formatCurrency(project.setup_cost)}
                        </div>
                      </TableCell>
                      <TableCell>
                        {getStatusBadge(project.order_status)}
                      </TableCell>
                      <TableCell>
                        {getValidationBadge(project.validation_status)}
                      </TableCell>
                      <TableCell>
                        {project.gc_signoff_required ? (
                          getStatusBadge(project.gc_signoff_status)
                        ) : (
                          <Badge className="bg-gray-100 text-gray-600">
                            Not Required
                          </Badge>
                        )}
                      </TableCell>
                      <TableCell>
                        <div className="text-sm text-gray-900">
                          {formatDate(project.created_at)}
                        </div>
                      </TableCell>
                      <TableCell>
                        <div className="flex items-center gap-2">
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => handleViewDetails(project)}
                          >
                            <Eye className="w-4 h-4 mr-1" />
                            View
                          </Button>
                        </div>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Project Details Modal */}
      <Dialog open={showDetailsModal} onOpenChange={setShowDetailsModal}>
        <DialogContent className="max-w-6xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="flex items-center justify-between">
              <span>Project Details - {selectedProject?.customer_name || 'Selected Project'}</span>
              <div className="flex items-center gap-2">
                {selectedProject?.order_status === 'Pending' && (
                  <>
                    <Button
                      size="sm"
                      className="bg-green-600 hover:bg-green-700"
                      onClick={() => {
                        setShowDetailsModal(false);
                        setShowConvertModal(true);
                      }}
                      disabled={actionLoading}
                    >
                      <Check className="w-4 h-4 mr-1" />
                      Convert to Project
                    </Button>
                    
                    <Button
                      size="sm"
                      variant="destructive"
                      onClick={() => {
                        setShowDetailsModal(false);
                        setShowRejectModal(true);
                      }}
                      disabled={actionLoading}
                    >
                      <X className="w-4 h-4 mr-1" />
                      Reject
                    </Button>
                  </>
                )}
              </div>
            </DialogTitle>
            <DialogDescription>
              Complete information for project including opportunity and quotation details
            </DialogDescription>
          </DialogHeader>
          
          {selectedProject && (
            <div className="space-y-6">
              {/* Project Summary Cards */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <Card className="border-blue-200 bg-blue-50">
                  <CardContent className="p-4">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-sm font-medium text-blue-600">Setup Cost</p>
                        <p className="text-2xl font-bold text-blue-800">{formatCurrency(selectedProject.setup_cost)}</p>
                      </div>
                      <DollarSign className="w-8 h-8 text-blue-600" />
                    </div>
                  </CardContent>
                </Card>
                
                <Card className="border-green-200 bg-green-50">
                  <CardContent className="p-4">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-sm font-medium text-green-600">Order Status</p>
                        <div className="mt-1">{getStatusBadge(selectedProject.order_status)}</div>
                      </div>
                      <Shield className="w-8 h-8 text-green-600" />
                    </div>
                  </CardContent>
                </Card>
                
                <Card className="border-purple-200 bg-purple-50">
                  <CardContent className="p-4">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-sm font-medium text-purple-600">Validation</p>
                        <div className="mt-1">{getValidationBadge(selectedProject.validation_status)}</div>
                      </div>
                      <CheckCircle className="w-8 h-8 text-purple-600" />
                    </div>
                  </CardContent>
                </Card>
              </div>

              {/* Project Information */}
              <Card>
                <CardHeader>
                  <CardTitle>Project Information</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                    <div>
                      <label className="text-sm font-medium text-gray-600">Customer</label>
                      <p className="text-lg font-semibold text-gray-900">{selectedProject.customer_name || 'N/A'}</p>
                    </div>
                    <div>
                      <label className="text-sm font-medium text-gray-600">Order ID</label>
                      <p className="text-lg font-mono text-gray-900">{selectedProject.order_id || 'N/A'}</p>
                    </div>
                    <div>
                      <label className="text-sm font-medium text-gray-600">POT ID</label>
                      <p className="text-lg font-mono text-gray-900">{selectedProject.pot_id || 'N/A'}</p>
                    </div>
                    <div>
                      <label className="text-sm font-medium text-gray-600">Opportunity ID</label>
                      <p className="text-lg font-mono text-gray-900">{selectedProject.opp_id || 'N/A'}</p>
                    </div>
                    <div>
                      <label className="text-sm font-medium text-gray-600">Created</label>
                      <p className="text-lg text-gray-900">{formatDate(selectedProject.created_at)}</p>
                    </div>
                    <div>
                      <label className="text-sm font-medium text-gray-600">Last Updated</label>
                      <p className="text-lg text-gray-900">{formatDate(selectedProject.updated_at)}</p>
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* Opportunity Details */}
              {selectedProject.opportunity_details && (
                <Card>
                  <CardHeader>
                    <CardTitle>Opportunity Details</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                      <div>
                        <label className="text-sm font-medium text-gray-600">Opportunity Name</label>
                        <p className="text-lg font-semibold text-gray-900">
                          {selectedProject.opportunity_details.name || selectedProject.opportunity_details.project_title || 'N/A'}
                        </p>
                      </div>
                      <div>
                        <label className="text-sm font-medium text-gray-600">Expected Revenue</label>
                        <p className="text-lg font-semibold text-green-600">
                          {selectedProject.opportunity_details.currency_symbol || '$'} 
                          {selectedProject.opportunity_details.expected_revenue?.toLocaleString() || '0'}
                        </p>
                      </div>
                      <div>
                        <label className="text-sm font-medium text-gray-600">Win Probability</label>
                        <p className="text-lg font-semibold text-blue-600">
                          {selectedProject.opportunity_details.win_probability || 0}%
                        </p>
                      </div>
                      <div>
                        <label className="text-sm font-medium text-gray-600">Current Stage</label>
                        <Badge variant="outline">L{selectedProject.opportunity_details.current_stage || 'N/A'}</Badge>
                      </div>
                      <div>
                        <label className="text-sm font-medium text-gray-600">Status</label>
                        <Badge className={
                          selectedProject.opportunity_details.status === 'Won' ? 'bg-green-100 text-green-800' :
                          selectedProject.opportunity_details.status === 'Lost' ? 'bg-red-100 text-red-800' :
                          selectedProject.opportunity_details.status === 'Open' ? 'bg-blue-100 text-blue-800' :
                          'bg-gray-100 text-gray-800'
                        }>
                          {selectedProject.opportunity_details.status || 'N/A'}
                        </Badge>
                      </div>
                      <div>
                        <label className="text-sm font-medium text-gray-600">Close Date</label>
                        <p className="text-lg text-gray-900">
                          {selectedProject.opportunity_details.close_date ? 
                            formatDate(selectedProject.opportunity_details.close_date) : 'N/A'
                          }
                        </p>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              )}

              {/* Quotations */}
              {selectedProject.quotations && selectedProject.quotations.length > 0 && (
                <Card>
                  <CardHeader>
                    <CardTitle>Quotations ({selectedProject.quotations.length})</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-4">
                      {selectedProject.quotations.map((quotation, index) => (
                        <div key={quotation.id || index} className="border rounded-lg p-4 bg-gray-50">
                          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                            <div>
                              <label className="text-sm font-medium text-gray-600">Quotation ID</label>
                              <p className="text-sm font-mono text-gray-900">{quotation.quotation_id || 'N/A'}</p>
                            </div>
                            <div>
                              <label className="text-sm font-medium text-gray-600">Total Amount</label>
                              <p className="text-sm font-semibold text-green-600">
                                {quotation.currency_symbol || '$'} {quotation.total_amount?.toLocaleString() || '0'}
                              </p>
                            </div>
                            <div>
                              <label className="text-sm font-medium text-gray-600">Status</label>
                              <Badge className={quotation.is_selected ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'}>
                                {quotation.is_selected ? 'Selected' : 'Draft'}
                              </Badge>
                            </div>
                            <div>
                              <label className="text-sm font-medium text-gray-600">Created</label>
                              <p className="text-sm text-gray-900">{formatDate(quotation.created_at)}</p>
                            </div>
                          </div>
                          
                          {quotation.notes && (
                            <div className="mt-3">
                              <label className="text-sm font-medium text-gray-600">Notes</label>
                              <p className="text-sm text-gray-700 mt-1">{quotation.notes}</p>
                            </div>
                          )}
                        </div>
                      ))}
                    </div>
                  </CardContent>
                </Card>
              )}

              {/* Status Information */}
              <Card>
                <CardHeader>
                  <CardTitle>Status Information</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                    <div>
                      <label className="text-sm font-medium text-gray-600">LOI Status</label>
                      <div className="mt-1">{getStatusBadge(selectedProject.loi_status)}</div>
                    </div>
                    <div>
                      <label className="text-sm font-medium text-gray-600">GC Signoff Required</label>
                      <p className="text-lg text-gray-900">{selectedProject.gc_signoff_required ? 'Yes' : 'No'}</p>
                    </div>
                    {selectedProject.gc_signoff_required && (
                      <div>
                        <label className="text-sm font-medium text-gray-600">GC Signoff Status</label>
                        <div className="mt-1">{getStatusBadge(selectedProject.gc_signoff_status)}</div>
                      </div>
                    )}
                    {selectedProject.validation_date && (
                      <div>
                        <label className="text-sm font-medium text-gray-600">Validation Date</label>
                        <p className="text-lg text-gray-900">{formatDate(selectedProject.validation_date)}</p>
                      </div>
                    )}
                    {selectedProject.loi_approved_on && (
                      <div>
                        <label className="text-sm font-medium text-gray-600">LOI Approved</label>
                        <p className="text-lg text-gray-900">{formatDate(selectedProject.loi_approved_on)}</p>
                      </div>
                    )}
                  </div>
                </CardContent>
              </Card>

              {/* Notes */}
              {selectedProject.discrepancy_notes && (
                <Card>
                  <CardHeader>
                    <CardTitle>Notes</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="p-3 bg-gray-50 rounded-lg">
                      <p className="text-gray-700">{selectedProject.discrepancy_notes}</p>
                    </div>
                  </CardContent>
                </Card>
              )}
            </div>
          )}
        </DialogContent>
      </Dialog>

      {/* Convert to Project Modal */}
      <Dialog open={showConvertModal} onOpenChange={setShowConvertModal}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Convert to Active Project</DialogTitle>
            <DialogDescription>
              Are you sure you want to convert this project to an active project? This action will move it to the active projects list.
            </DialogDescription>
          </DialogHeader>
          
          {selectedProject && (
            <div className="space-y-4">
              <div className="p-4 bg-blue-50 rounded-lg">
                <h4 className="font-medium text-blue-900">{selectedProject.customer_name}</h4>
                <p className="text-sm text-blue-700">Order ID: {selectedProject.order_id}</p>
                <p className="text-sm text-blue-700">Setup Cost: {formatCurrency(selectedProject.setup_cost)}</p>
              </div>
              
              <div className="flex justify-end space-x-2">
                <Button variant="outline" onClick={() => setShowConvertModal(false)} disabled={actionLoading}>
                  Cancel
                </Button>
                <Button 
                  onClick={() => handleConvertToProject(selectedProject)}
                  disabled={actionLoading}
                  className="bg-green-600 hover:bg-green-700"
                >
                  {actionLoading ? 'Converting...' : 'Convert to Project'}
                </Button>
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>

      {/* Reject Project Modal */}
      <Dialog open={showRejectModal} onOpenChange={setShowRejectModal}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Reject Project</DialogTitle>
            <DialogDescription>
              Are you sure you want to reject this project? This action cannot be undone.
            </DialogDescription>
          </DialogHeader>
          
          {selectedProject && (
            <div className="space-y-4">
              <div className="p-4 bg-red-50 rounded-lg">
                <h4 className="font-medium text-red-900">{selectedProject.customer_name}</h4>
                <p className="text-sm text-red-700">Order ID: {selectedProject.order_id}</p>
                <p className="text-sm text-red-700">Setup Cost: {formatCurrency(selectedProject.setup_cost)}</p>
              </div>
              
              <div className="flex justify-end space-x-2">
                <Button variant="outline" onClick={() => setShowRejectModal(false)} disabled={actionLoading}>
                  Cancel
                </Button>
                <Button 
                  variant="destructive"
                  onClick={() => handleRejectProject(selectedProject)}
                  disabled={actionLoading}
                >
                  {actionLoading ? 'Rejecting...' : 'Reject Project'}
                </Button>
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default UpcomingProjectsList;