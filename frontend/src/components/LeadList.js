import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Badge } from './ui/badge';
import { Label } from './ui/label';
import { Input } from './ui/input';
import { Button } from './ui/button';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './ui/select';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogFooter } from './ui/dialog';
import { Alert, AlertDescription } from './ui/alert';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Separator } from './ui/separator';
import { AlertCircle, Target, TrendingUp, Clock, CheckCircle2, AlertTriangle, Eye, Edit, Trash2, FileDown, Plus, Filter, Search, RefreshCw } from 'lucide-react';
import { toast } from 'sonner';
import { useNavigate } from 'react-router-dom';
import PermissionDataTable from './PermissionDataTable';
import LeadChangeStatusModal from './LeadChangeStatusModal';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export const LeadList = () => {
  const navigate = useNavigate();
  
  // Data state
  const [leads, setLeads] = useState([]);
  const [kpis, setKpis] = useState({
    total: 0,
    pending: 0,
    approved: 0,
    escalated: 0
  });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  
  // Filters and search
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  const [approvalStatusFilter, setApprovalStatusFilter] = useState('all');
  const [tenderTypeFilter, setTenderTypeFilter] = useState('all');
  const [sortField, setSortField] = useState('');
  const [sortDirection, setSortDirection] = useState('asc');
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  
  // Dialog states
  const [viewingLead, setViewingLead] = useState(null);
  const [statusChangeModal, setStatusChangeModal] = useState({
    isOpen: false,
    leadId: null,
    lead: null
  });
  
  // Master data
  const [companies, setCompanies] = useState([]);
  const [productServices, setProductServices] = useState([]);
  const [subTenderTypes, setSubTenderTypes] = useState([]);

  useEffect(() => {
    loadData();
    loadMasterData();
  }, []);

  useEffect(() => {
    loadLeads();
  }, [searchTerm, statusFilter, approvalStatusFilter, tenderTypeFilter, sortField, sortDirection, currentPage]);

  const loadData = async () => {
    try {
      setLoading(true);
      await Promise.all([loadKpis(), loadLeads()]);
    } catch (err) {
      console.error('Failed to load data:', err);
      setError('Failed to load lead data');
    } finally {
      setLoading(false);
    }
  };

  const loadKpis = async () => {
    try {
      const response = await axios.get(`${API}/leads/kpis`);
      setKpis(response.data || { total: 0, pending: 0, approved: 0, escalated: 0 });
    } catch (err) {
      console.error('Failed to load KPIs:', err);
      toast.error('Failed to load KPIs');
    }
  };

  const loadLeads = async () => {
    try {
      const params = {
        page: currentPage,
        limit: 20,
        search: searchTerm || undefined,
        status: statusFilter !== 'all' ? statusFilter : undefined,
        approval_status: approvalStatusFilter !== 'all' ? approvalStatusFilter : undefined,
        tender_type: tenderTypeFilter !== 'all' ? tenderTypeFilter : undefined,
        sort_field: sortField || undefined,
        sort_direction: sortDirection || undefined,
      };

      const response = await axios.get(`${API}/leads`, { params });
      setLeads(response.data.leads || []);
      setTotalPages(Math.ceil((response.data.total || 0) / 20));
    } catch (err) {
      console.error('Failed to load leads:', err);
      setError('Failed to load leads');
      toast.error('Failed to load leads');
    }
  };

  const loadMasterData = async () => {
    try {
      const [companiesRes, productServicesRes, subTenderRes] = await Promise.all([
        axios.get(`${API}/companies`),
        axios.get(`${API}/product-services`),
        axios.get(`${API}/sub-tender-types`),
      ]);
      
      setCompanies(companiesRes.data || []);
      setProductServices(productServicesRes.data || []);
      setSubTenderTypes(subTenderRes.data || []);
    } catch (err) {
      console.error('Failed to load master data:', err);
    }
  };

  const handleStatusChange = (lead) => {
    setStatusChangeModal({
      isOpen: true,
      leadId: lead.id,
      lead: lead
    });
  };

  const handleStatusChangeSuccess = (updatedLead) => {
    // Refresh the leads list and KPIs
    loadData();
    
    // Close the modal
    setStatusChangeModal({
      isOpen: false,
      leadId: null,
      lead: null
    });
  };

  const handleStatusChangeClose = () => {
    setStatusChangeModal({
      isOpen: false,
      leadId: null,
      lead: null
    });
  };

  const handleDelete = async (lead) => {
    if (window.confirm(`Are you sure you want to delete lead "${lead.project_title}"?`)) {
      try {
        await axios.delete(`${API}/leads/${lead.id}`);
        toast.success('Lead deleted successfully');
        loadData(); // Reload both leads and KPIs
      } catch (err) {
        const errorMsg = err.response?.data?.detail || 'Failed to delete lead';
        toast.error(errorMsg);
      }
    }
  };

  const handleSort = (field) => {
    const newDirection = sortField === field && sortDirection === 'asc' ? 'desc' : 'asc';
    setSortField(field);
    setSortDirection(newDirection);
  };

  const handleNurture = async (lead) => {
    try {
      await axios.post(`${API}/leads/${lead.id}/nurture`);
      toast.success('Lead moved to nurturing status');
      loadData(); // Reload to update status and KPIs
    } catch (err) {
      const errorMsg = err.response?.data?.detail || 'Failed to nurture lead';
      toast.error(errorMsg);
    }
  };

  const handleConvert = async (lead) => {
    try {
      await axios.post(`${API}/leads/${lead.id}/convert`, {
        opportunity_date: new Date().toISOString()
      });
      toast.success('Lead converted to opportunity');
      loadData(); // Reload to update status and KPIs
    } catch (err) {
      const errorMsg = err.response?.data?.detail || 'Failed to convert lead';
      toast.error(errorMsg);
    }
  };

  const exportToCSV = async () => {
    try {
      const csvContent = convertToCSV(leads);
      downloadCSV(csvContent, 'leads_export.csv');
      toast.success('Leads exported successfully');
    } catch (err) {
      toast.error('Failed to export leads');
    }
  };

  const convertToCSV = (data) => {
    if (!data.length) return '';
    
    const headers = ['Lead ID', 'Project Title', 'Company', 'Tender Type', 'Status', 'Approval Status', 'Expected ORC', 'Revenue', 'Lead Owner', 'Created Date'];
    const rows = data.map(lead => [
      lead.lead_id || '',
      lead.project_title || '',
      getCompanyName(lead.company_id) || '',
      lead.tender_type || '',
      lead.status || '',
      lead.approval_status || '',
      lead.expected_orc || '',
      lead.revenue || '',
      lead.lead_owner || '',
      new Date(lead.created_at).toLocaleDateString()
    ]);
    
    return [headers, ...rows].map(row => row.join(',')).join('\n');
  };

  const downloadCSV = (content, filename) => {
    const blob = new Blob([content], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    const url = URL.createObjectURL(blob);
    link.setAttribute('href', url);
    link.setAttribute('download', filename);
    link.style.visibility = 'hidden';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const getCompanyName = (companyId) => {
    const company = companies.find(c => c.id === companyId);
    return company ? company.name : 'Unknown Company';
  };

  const getProductServiceName = (serviceId) => {
    const service = productServices.find(s => s.id === serviceId);
    return service ? service.name : 'Not specified';
  };

  const getSubTenderTypeName = (typeId) => {
    const type = subTenderTypes.find(t => t.id === typeId);
    return type ? type.name : 'Not specified';
  };

  const getStatusBadgeColor = (status) => {
    switch (status?.toLowerCase()) {
      case 'new': return 'bg-blue-100 text-blue-800';
      case 'nurturing': return 'bg-yellow-100 text-yellow-800';
      case 'converted': return 'bg-green-100 text-green-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const getApprovalStatusBadgeColor = (status) => {
    switch (status?.toLowerCase()) {
      case 'pending': return 'bg-yellow-100 text-yellow-800';
      case 'approved': return 'bg-green-100 text-green-800';
      case 'rejected': return 'bg-red-100 text-red-800';
      case 'escalated': return 'bg-orange-100 text-orange-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const columns = [
    { 
      key: 'lead_id', 
      label: 'Lead ID', 
      sortable: true,
      render: (lead) => (
        <div className="flex items-center space-x-2">
          <Target className="h-4 w-4 text-blue-600" />
          <div>
            <p className="font-medium font-mono text-sm">{lead.lead_id}</p>
            <p className="text-xs text-gray-500">{lead.tender_type}</p>
          </div>
        </div>
      )
    },
    { 
      key: 'project_title', 
      label: 'Project Title', 
      sortable: true,
      render: (lead) => (
        <div className="max-w-xs">
          <p className="font-medium truncate">{lead.project_title}</p>
          <p className="text-sm text-gray-500 truncate">
            {getCompanyName(lead.company_id)}
          </p>
        </div>
      )
    },
    { 
      key: 'status', 
      label: 'Status', 
      sortable: true,
      render: (lead) => (
        <Badge className={getStatusBadgeColor(lead.status)}>
          {lead.status || 'New'}
        </Badge>
      )
    },
    { 
      key: 'approval_status', 
      label: 'Approval', 
      sortable: true,
      render: (lead) => (
        <Badge className={getApprovalStatusBadgeColor(lead.approval_status)}>
          {lead.approval_status || 'Pending'}
        </Badge>
      )
    },
    { 
      key: 'expected_orc', 
      label: 'Expected ORC', 
      sortable: true,
      render: (lead) => (
        <div className="text-right">
          {lead.expected_orc ? (
            <p className="font-medium">₹{Number(lead.expected_orc).toLocaleString('en-IN')}</p>
          ) : (
            <p className="text-gray-400">Not specified</p>
          )}
        </div>
      )
    },
    { 
      key: 'revenue', 
      label: 'Revenue', 
      sortable: true,
      render: (lead) => (
        <div className="text-right">
          {lead.revenue ? (
            <p className="font-medium">₹{Number(lead.revenue).toLocaleString('en-IN')}</p>
          ) : (
            <p className="text-gray-400">Not specified</p>
          )}
        </div>
      )
    },
    { 
      key: 'state', 
      label: 'Location', 
      render: (lead) => (
        <div className="text-sm">
          <p>{lead.state}</p>
        </div>
      )
    },
    { 
      key: 'created_at', 
      label: 'Created', 
      sortable: true,
      render: (lead) => (
        <div className="text-sm text-gray-600">
          {new Date(lead.created_at).toLocaleDateString()}
        </div>
      )
    }
  ];

  const KPICard = ({ title, value, icon: Icon, color, description }) => (
    <Card>
      <CardContent className="p-6">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm font-medium text-gray-600">{title}</p>
            <p className={`text-2xl font-bold ${color}`}>{value}</p>
            {description && (
              <p className="text-xs text-gray-500 mt-1">{description}</p>
            )}
          </div>
          <div className={`p-3 rounded-full ${color.replace('text-', 'bg-').replace('-600', '-100')}`}>
            <Icon className={`h-6 w-6 ${color}`} />
          </div>
        </div>
      </CardContent>
    </Card>
  );

  return (
    <div className="space-y-6">
      {error && (
        <Alert className="border-red-200 bg-red-50">
          <AlertCircle className="h-4 w-4 text-red-600" />
          <AlertDescription className="text-red-800">{error}</AlertDescription>
        </Alert>
      )}

      {/* KPI Dashboard */}
      <div className="space-y-4">
        <div>
          <h2 className="text-xl font-semibold text-gray-900">Lead Management Dashboard</h2>
          <p className="text-gray-600">Overview of lead performance and status</p>
        </div>
        
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <KPICard
            title="Total Leads"
            value={kpis.total}
            icon={Target}
            color="text-blue-600"
            description="All leads in system"
          />
          <KPICard
            title="Pending Approval"
            value={kpis.pending}
            icon={Clock}
            color="text-yellow-600"
            description="Awaiting approval"
          />
          <KPICard
            title="Approved"
            value={kpis.approved}
            icon={CheckCircle2}
            color="text-green-600"
            description="Approved leads"
          />
          <KPICard
            title="Escalated"
            value={kpis.escalated}
            icon={AlertTriangle}
            color="text-orange-600"
            description="Requires attention"
          />
        </div>
      </div>

      <Separator />

      {/* Filters */}
      <div className="space-y-4">
        <h3 className="text-lg font-medium">Filters & Search</h3>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div>
            <Label>Status</Label>
            <Select value={statusFilter} onValueChange={setStatusFilter}>
              <SelectTrigger>
                <SelectValue placeholder="All statuses" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Statuses</SelectItem>
                <SelectItem value="New">New</SelectItem>
                <SelectItem value="Nurturing">Nurturing</SelectItem>
                <SelectItem value="Converted">Converted</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <div>
            <Label>Approval Status</Label>
            <Select value={approvalStatusFilter} onValueChange={setApprovalStatusFilter}>
              <SelectTrigger>
                <SelectValue placeholder="All approval statuses" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Approval Statuses</SelectItem>
                <SelectItem value="Pending">Pending</SelectItem>
                <SelectItem value="Approved">Approved</SelectItem>
                <SelectItem value="Rejected">Rejected</SelectItem>
                <SelectItem value="Escalated">Escalated</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <div>
            <Label>Tender Type</Label>
            <Select value={tenderTypeFilter} onValueChange={setTenderTypeFilter}>
              <SelectTrigger>
                <SelectValue placeholder="All tender types" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Tender Types</SelectItem>
                <SelectItem value="Tender">Tender</SelectItem>
                <SelectItem value="Pre-Tender">Pre-Tender</SelectItem>
                <SelectItem value="Non-Tender">Non-Tender</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <div>
            <Label>Search</Label>
            <div className="relative">
              <Search className="absolute left-3 top-3 h-4 w-4 text-gray-400" />
              <Input
                placeholder="Search leads..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pl-10"
              />
            </div>
          </div>
        </div>
      </div>

      {/* Data Table */}
      <PermissionDataTable
        data={leads}
        columns={columns}
        loading={loading}
        error={error}
        searchTerm={searchTerm}
        setSearchTerm={setSearchTerm}
        sortField={sortField}
        sortDirection={sortDirection}
        currentPage={currentPage}
        setCurrentPage={setCurrentPage}
        totalPages={totalPages}
        onSort={handleSort}
        onExport={exportToCSV}
        onView={(lead) => setViewingLead(lead)}
        onEdit={(lead) => navigate(`/leads/edit/${lead.id}`)}
        onDelete={handleDelete}
        onAdd={() => navigate('/leads/add')}
        title="Leads"
        description="Manage lead pipeline and track conversions"
        modulePath="/leads"
        entityName="leads"
        customActions={(lead) => (
          <div className="flex space-x-2">
            {lead.status === 'New' && (
              <Button
                size="sm"
                variant="outline"
                onClick={() => handleNurture(lead)}
                className="text-yellow-600 hover:text-yellow-700"
              >
                <TrendingUp className="h-4 w-4 mr-1" />
                Nurture
              </Button>
            )}
            {(lead.status === 'New' || lead.status === 'Nurturing') && lead.approval_status === 'Approved' && (
              <Button
                size="sm"
                variant="outline"
                onClick={() => handleConvert(lead)}
                className="text-green-600 hover:text-green-700"
              >
                <CheckCircle2 className="h-4 w-4 mr-1" />
                Convert
              </Button>
            )}
          </div>
        )}
      />

      {/* View Dialog */}
      <Dialog open={!!viewingLead} onOpenChange={() => setViewingLead(null)}>
        <DialogContent className="max-w-4xl max-h-[80vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="flex items-center space-x-2">
              <Target className="h-5 w-5" />
              <span>Lead Details</span>
            </DialogTitle>
          </DialogHeader>
          
          {viewingLead && (
            <div className="space-y-6">
              {/* Basic Info */}
              <div className="bg-blue-50 p-4 rounded-lg">
                <h4 className="font-semibold text-lg border-b pb-2">Lead Information</h4>
                <div className="grid grid-cols-2 gap-4 mt-4">
                  <div>
                    <Label className="font-medium">Lead ID:</Label>
                    <p className="text-gray-700 font-mono">{viewingLead.lead_id}</p>
                  </div>
                  <div>
                    <Label className="font-medium">Project Title:</Label>
                    <p className="text-gray-700">{viewingLead.project_title}</p>
                  </div>
                  <div>
                    <Label className="font-medium">Tender Type:</Label>
                    <Badge className="bg-blue-100 text-blue-800">{viewingLead.tender_type}</Badge>
                  </div>
                  <div>
                    <Label className="font-medium">Sub-Tender Type:</Label>
                    <p className="text-gray-700">{getSubTenderTypeName(viewingLead.sub_tender_type_id)}</p>
                  </div>
                </div>
              </div>

              {/* Company & Location */}
              <div className="grid grid-cols-2 gap-6">
                <div>
                  <h4 className="font-semibold text-lg border-b pb-2">Company & Location</h4>
                  <div className="space-y-2 mt-4">
                    <div>
                      <Label className="font-medium">Company:</Label>
                      <p className="text-gray-700">{getCompanyName(viewingLead.company_id)}</p>
                    </div>
                    <div>
                      <Label className="font-medium">State:</Label>
                      <p className="text-gray-700">{viewingLead.state}</p>
                    </div>
                  </div>
                </div>

                <div>
                  <h4 className="font-semibold text-lg border-b pb-2">Lead Details</h4>
                  <div className="space-y-2 mt-4">
                    <div>
                      <Label className="font-medium">Lead Subtype:</Label>
                      <p className="text-gray-700">{viewingLead.lead_subtype}</p>
                    </div>
                    <div>
                      <Label className="font-medium">Source:</Label>
                      <p className="text-gray-700">{viewingLead.source || 'Not specified'}</p>
                    </div>
                    <div>
                      <Label className="font-medium">Product/Service:</Label>
                      <p className="text-gray-700">{getProductServiceName(viewingLead.product_service_id)}</p>
                    </div>
                  </div>
                </div>
              </div>

              {/* Financial Info */}
              <div>
                <h4 className="font-semibold text-lg border-b pb-2">Financial Information</h4>
                <div className="grid grid-cols-3 gap-4 mt-4">
                  <div>
                    <Label className="font-medium">Expected ORC:</Label>
                    <p className="text-gray-700">
                      {viewingLead.expected_orc ? `₹${Number(viewingLead.expected_orc).toLocaleString('en-IN')}` : 'Not specified'}
                    </p>
                  </div>
                  <div>
                    <Label className="font-medium">Expected Revenue:</Label>
                    <p className="text-gray-700">
                      {viewingLead.revenue ? `₹${Number(viewingLead.revenue).toLocaleString('en-IN')}` : 'Not specified'}
                    </p>
                  </div>
                  <div>
                    <Label className="font-medium">Lead Owner:</Label>
                    <p className="text-gray-700">{viewingLead.lead_owner}</p>
                  </div>
                </div>
              </div>

              {/* Status & Additional Info */}
              <div className="grid grid-cols-2 gap-6">
                <div>
                  <h4 className="font-semibold text-lg border-b pb-2">Status Information</h4>
                  <div className="space-y-2 mt-4">
                    <div>
                      <Label className="font-medium">Status:</Label>
                      <Badge className={getStatusBadgeColor(viewingLead.status)}>
                        {viewingLead.status || 'New'}
                      </Badge>
                    </div>
                    <div>
                      <Label className="font-medium">Approval Status:</Label>
                      <Badge className={getApprovalStatusBadgeColor(viewingLead.approval_status)}>
                        {viewingLead.approval_status || 'Pending'}
                      </Badge>
                    </div>
                    <div>
                      <Label className="font-medium">Checklist Completed:</Label>
                      <Badge className={viewingLead.checklist_completed ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}>
                        {viewingLead.checklist_completed ? 'Yes' : 'No'}
                      </Badge>
                    </div>
                  </div>
                </div>

                <div>
                  <h4 className="font-semibold text-lg border-b pb-2">Additional Information</h4>
                  <div className="space-y-2 mt-4">
                    <div>
                      <Label className="font-medium">Competitors:</Label>
                      <p className="text-gray-700">{viewingLead.competitors || 'Not specified'}</p>
                    </div>
                    {viewingLead.converted_to_opportunity && (
                      <div>
                        <Label className="font-medium">Opportunity Date:</Label>
                        <p className="text-gray-700">
                          {viewingLead.opportunity_date ? 
                            new Date(viewingLead.opportunity_date).toLocaleDateString() : 
                            'Not specified'
                          }
                        </p>
                      </div>
                    )}
                  </div>
                </div>
              </div>

              {/* System Information */}
              <div className="border-t pt-4">
                <h4 className="font-semibold text-lg border-b pb-2">System Information</h4>
                <div className="grid grid-cols-3 gap-4 mt-4">
                  <div>
                    <Label className="font-medium">Created:</Label>
                    <p className="text-gray-600 text-sm">
                      {new Date(viewingLead.created_at).toLocaleString()}
                    </p>
                  </div>
                  <div>
                    <Label className="font-medium">Last Updated:</Label>
                    <p className="text-gray-600 text-sm">
                      {new Date(viewingLead.updated_at).toLocaleString()}
                    </p>
                  </div>
                  <div>
                    <Label className="font-medium">Lead ID:</Label>
                    <p className="text-xs text-gray-500 font-mono">{viewingLead.id}</p>
                  </div>
                </div>
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default LeadList;