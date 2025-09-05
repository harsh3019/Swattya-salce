import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { Badge } from './ui/badge';
import { Label } from './ui/label';
import { Input } from './ui/input';
import { Button } from './ui/button';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './ui/select';
import { Textarea } from './ui/textarea';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from './ui/dialog';
import { Alert, AlertDescription } from './ui/alert';
import { AlertCircle, Plus, Building, Eye, Edit, Trash2, FileDown, ExternalLink } from 'lucide-react';
import { toast } from 'sonner';
import PermissionDataTable from './PermissionDataTable';
import { useCRUD } from './UserManagement';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export const CompanyList = () => {
  const navigate = useNavigate();
  const [companies, setCompanies] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [searchTerm, setSearchTerm] = useState('');
  const [sortField, setSortField] = useState('');
  const [sortDirection, setSortDirection] = useState('asc');
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [viewingCompany, setViewingCompany] = useState(null);
  const [editingCompany, setEditingCompany] = useState(null);
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  
  // Master data for display purposes
  const [masterData, setMasterData] = useState({});

  useEffect(() => {
    fetchCompanies();
    fetchMasterData();
  }, []);

  const fetchCompanies = async () => {
    try {
      setLoading(true);
      setError('');
      const response = await axios.get(`${API}/companies`);
      setCompanies(response.data || []);
    } catch (err) {
      const errorMsg = err.response?.data?.detail || 'Failed to fetch companies';
      setError(errorMsg);
      toast.error(errorMsg);
    } finally {
      setLoading(false);
    }
  };

  const fetchMasterData = async () => {
    try {
      const endpoints = [
        'company-types', 'account-types', 'regions', 'business-types',
        'industries', 'sub-industries', 'countries', 'states', 'cities'
      ];
      
      const responses = await Promise.all(
        endpoints.map(endpoint => axios.get(`${API}/${endpoint}`))
      );
      
      const data = {};
      endpoints.forEach((endpoint, index) => {
        data[endpoint] = responses[index].data;
      });
      
      setMasterData(data);
    } catch (error) {
      console.error('Failed to load master data:', error);
    }
  };

  const handleDelete = async (company) => {
    if (window.confirm(`Are you sure you want to delete company "${company.name}"?`)) {
      try {
        await axios.delete(`${API}/companies/${company.id}`);
        toast.success('Company deleted successfully');
        fetchCompanies();
      } catch (err) {
        const errorMsg = err.response?.data?.detail || 'Failed to delete company';
        toast.error(errorMsg);
      }
    }
  };

  const handleSort = (field) => {
    const newDirection = sortField === field && sortDirection === 'asc' ? 'desc' : 'asc';
    setSortField(field);
    setSortDirection(newDirection);
  };

  const exportToCSV = async () => {
    try {
      const response = await axios.get(`${API}/companies/export`);
      const csvContent = convertToCSV(response.data);
      downloadCSV(csvContent, 'companies_export.csv');
      toast.success('Companies exported successfully');
    } catch (err) {
      const errorMsg = err.response?.data?.detail || 'Failed to export companies';
      toast.error(errorMsg);
    }
  };

  const convertToCSV = (data) => {
    if (!data.length) return '';
    
    const headers = ['Name', 'Type', 'GST Number', 'PAN Number', 'Industry', 'Employee Count', 'Annual Revenue', 'Lead Status', 'Score', 'Created Date'];
    const rows = data.map(company => [
      company.name || '',
      company.domestic_international || '',
      company.gst_number || '',
      company.pan_number || '',
      getIndustryName(company.industry_id) || '',
      company.employee_count || '',
      `${company.annual_revenue || 0} ${company.revenue_currency || ''}`,
      company.lead_status || '',
      company.score || 0,
      new Date(company.created_at).toLocaleDateString()
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

  // Helper functions to get master data names
  const getIndustryName = (industryId) => {
    const industry = masterData.industries?.find(i => i.id === industryId);
    return industry?.name || 'Unknown';
  };

  const getSubIndustryName = (subIndustryId) => {
    const subIndustry = masterData['sub-industries']?.find(si => si.id === subIndustryId);
    return subIndustry?.name || 'Unknown';
  };

  const getCompanyTypeName = (companyTypeId) => {
    const companyType = masterData['company-types']?.find(ct => ct.id === companyTypeId);
    return companyType?.name || 'Unknown';
  };

  const getAccountTypeName = (accountTypeId) => {
    const accountType = masterData['account-types']?.find(at => at.id === accountTypeId);
    return accountType?.name || 'Unknown';
  };

  const getRegionName = (regionId) => {
    const region = masterData.regions?.find(r => r.id === regionId);
    return region?.name || 'Unknown';
  };

  const getCountryName = (countryId) => {
    const country = masterData.countries?.find(c => c.id === countryId);
    return country?.name || 'Unknown';
  };

  const getStateName = (stateId) => {
    const state = masterData.states?.find(s => s.id === stateId);
    return state?.name || 'Unknown';
  };

  const getCityName = (cityId) => {
    const city = masterData.cities?.find(c => c.id === cityId);
    return city?.name || 'Unknown';
  };

  const columns = [
    { 
      key: 'name', 
      label: 'Company Name', 
      sortable: true,
      render: (company) => (
        <div className="flex items-center space-x-2">
          <Building className="h-4 w-4 text-blue-600" />
          <div>
            <p className="font-medium">{company.name}</p>
            <p className="text-sm text-gray-500">{company.domestic_international}</p>
          </div>
        </div>
      )
    },
    { 
      key: 'industry', 
      label: 'Industry', 
      sortable: false,
      render: (company) => (
        <div>
          <p className="font-medium">{getIndustryName(company.industry_id)}</p>
          <p className="text-sm text-gray-500">{getSubIndustryName(company.sub_industry_id)}</p>
        </div>
      )
    },
    { 
      key: 'company_type', 
      label: 'Type', 
      sortable: false,
      render: (company) => (
        <Badge variant="outline">
          {getCompanyTypeName(company.company_type_id)}
        </Badge>
      )
    },
    { 
      key: 'employee_count', 
      label: 'Employees', 
      sortable: true,
      render: (company) => (
        <div className="text-center">
          <p className="font-medium">{company.employee_count}</p>
        </div>
      )
    },
    { 
      key: 'annual_revenue', 
      label: 'Revenue', 
      sortable: true,
      render: (company) => (
        <div>
          <p className="font-medium">
            {new Intl.NumberFormat('en-IN').format(company.annual_revenue || 0)}
          </p>
          <p className="text-sm text-gray-500">{company.revenue_currency}</p>
        </div>
      )
    },
    { 
      key: 'lead_status', 
      label: 'Lead Status', 
      sortable: true,
      render: (company) => (
        <div className="flex items-center space-x-2">
          <Badge 
            variant={company.lead_status === 'hot' ? 'default' : 'secondary'}
            className={company.lead_status === 'hot' ? 'bg-red-100 text-red-800' : 'bg-blue-100 text-blue-800'}
          >
            {company.lead_status?.toUpperCase()}
          </Badge>
          <span className="text-sm text-gray-500">({company.score}/100)</span>
        </div>
      )
    },
    { 
      key: 'gst_pan', 
      label: 'GST/PAN', 
      sortable: false,
      render: (company) => (
        <div className="text-sm">
          {company.gst_number && <p><span className="font-medium">GST:</span> {company.gst_number}</p>}
          {company.pan_number && <p><span className="font-medium">PAN:</span> {company.pan_number}</p>}
          {company.vat_number && <p><span className="font-medium">VAT:</span> {company.vat_number}</p>}
        </div>
      )
    },
    { 
      key: 'location', 
      label: 'Location', 
      sortable: false,
      render: (company) => (
        <div className="text-sm">
          <p>{getCityName(company.city_id)}</p>
          <p className="text-gray-500">{getStateName(company.state_id)}, {getCountryName(company.country_id)}</p>
        </div>
      )
    },
    { 
      key: 'created_at', 
      label: 'Created', 
      sortable: true,
      render: (company) => (
        <div className="text-sm">
          <p>{new Date(company.created_at).toLocaleDateString()}</p>
          <p className="text-gray-500">{new Date(company.created_at).toLocaleTimeString()}</p>
        </div>
      )
    }
  ];

  const filteredCompanies = companies.filter(company =>
    company.name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
    company.gst_number?.toLowerCase().includes(searchTerm.toLowerCase()) ||
    company.pan_number?.toLowerCase().includes(searchTerm.toLowerCase()) ||
    getIndustryName(company.industry_id)?.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const sortedCompanies = [...filteredCompanies].sort((a, b) => {
    if (!sortField) return 0;
    
    let aVal = a[sortField];
    let bVal = b[sortField];
    
    if (sortField === 'name') {
      aVal = a.name || '';
      bVal = b.name || '';
    }
    
    if (typeof aVal === 'string') {
      aVal = aVal.toLowerCase();
      bVal = bVal.toLowerCase();
    }
    
    if (sortDirection === 'asc') {
      return aVal < bVal ? -1 : aVal > bVal ? 1 : 0;
    } else {
      return aVal > bVal ? -1 : aVal < bVal ? 1 : 0;
    }
  });

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold">Companies</h1>
          <p className="text-gray-600">Manage company information and records</p>
        </div>
        <Button onClick={() => navigate('/company/add')} className="bg-blue-600 hover:bg-blue-700">
          <Plus className="h-4 w-4 mr-2" />
          Add Company
        </Button>
      </div>

      {error && (
        <Alert className="border-red-200 bg-red-50">
          <AlertCircle className="h-4 w-4 text-red-600" />
          <AlertDescription className="text-red-800">{error}</AlertDescription>
        </Alert>
      )}

      <PermissionDataTable
        data={sortedCompanies}
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
        onView={(company) => setViewingCompany(company)}
        onEdit={(company) => navigate(`/company/edit/${company.id}`)}
        onDelete={handleDelete}
        onAdd={() => navigate('/company/add')}
        title="Companies"
        modulePath="/companies"
        entityName="companies"
      />

      {/* View Company Dialog */}
      <Dialog open={!!viewingCompany} onOpenChange={() => setViewingCompany(null)}>
        <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="flex items-center space-x-2">
              <Building className="h-5 w-5" />
              <span>Company Details</span>
            </DialogTitle>
          </DialogHeader>
          
          {viewingCompany && (
            <div className="space-y-6">
              {/* Header Info */}
              <div className="bg-blue-50 p-4 rounded-lg">
                <div className="flex justify-between items-start">
                  <div>
                    <h3 className="text-xl font-bold text-blue-900">{viewingCompany.name}</h3>
                    <p className="text-blue-700">{viewingCompany.domestic_international} Company</p>
                  </div>
                  <div className="text-right">
                    <Badge 
                      variant={viewingCompany.lead_status === 'hot' ? 'default' : 'secondary'}
                      className={viewingCompany.lead_status === 'hot' ? 'bg-red-100 text-red-800' : 'bg-blue-100 text-blue-800'}
                    >
                      {viewingCompany.lead_status?.toUpperCase()} LEAD
                    </Badge>
                    <p className="text-sm text-blue-600 mt-1">Score: {viewingCompany.score}/100</p>
                  </div>
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {/* Basic Information */}
                <div className="space-y-4">
                  <h4 className="font-semibold text-lg border-b pb-2">Basic Information</h4>
                  
                  <div className="space-y-3">
                    <div>
                      <Label className="font-medium">Company Type:</Label>
                      <p className="text-gray-600">{getCompanyTypeName(viewingCompany.company_type_id)}</p>
                    </div>
                    
                    <div>
                      <Label className="font-medium">Account Type:</Label>
                      <p className="text-gray-600">{getAccountTypeName(viewingCompany.account_type_id)}</p>
                    </div>
                    
                    <div>
                      <Label className="font-medium">Region:</Label>
                      <p className="text-gray-600">{getRegionName(viewingCompany.region_id)}</p>
                    </div>
                    
                    <div>
                      <Label className="font-medium">Industry:</Label>
                      <p className="text-gray-600">
                        {getIndustryName(viewingCompany.industry_id)} - {getSubIndustryName(viewingCompany.sub_industry_id)}
                      </p>
                    </div>
                    
                    <div>
                      <Label className="font-medium">Employee Count:</Label>
                      <p className="text-gray-600">{viewingCompany.employee_count} employees</p>
                    </div>

                    {viewingCompany.website && (
                      <div>
                        <Label className="font-medium">Website:</Label>
                        <a 
                          href={viewingCompany.website} 
                          target="_blank" 
                          rel="noopener noreferrer"
                          className="text-blue-600 hover:text-blue-800 flex items-center space-x-1"
                        >
                          <span>{viewingCompany.website}</span>
                          <ExternalLink className="h-3 w-3" />
                        </a>
                      </div>
                    )}
                  </div>
                </div>

                {/* Legal & Financial Information */}
                <div className="space-y-4">
                  <h4 className="font-semibold text-lg border-b pb-2">Legal & Financial</h4>
                  
                  <div className="space-y-3">
                    {viewingCompany.gst_number && (
                      <div>
                        <Label className="font-medium">GST Number:</Label>
                        <p className="text-gray-600 font-mono">{viewingCompany.gst_number}</p>
                      </div>
                    )}
                    
                    {viewingCompany.pan_number && (
                      <div>
                        <Label className="font-medium">PAN Number:</Label>
                        <p className="text-gray-600 font-mono">{viewingCompany.pan_number}</p>
                      </div>
                    )}
                    
                    {viewingCompany.vat_number && (
                      <div>
                        <Label className="font-medium">VAT Number:</Label>
                        <p className="text-gray-600 font-mono">{viewingCompany.vat_number}</p>
                      </div>
                    )}
                    
                    <div>
                      <Label className="font-medium">Annual Revenue:</Label>
                      <p className="text-gray-600">
                        {new Intl.NumberFormat('en-IN').format(viewingCompany.annual_revenue || 0)} {viewingCompany.revenue_currency}
                      </p>
                    </div>

                    {viewingCompany.turnover && viewingCompany.turnover.length > 0 && (
                      <div>
                        <Label className="font-medium">Turnover History:</Label>
                        <div className="mt-2 space-y-1">
                          {viewingCompany.turnover.map((t, index) => (
                            <p key={index} className="text-sm text-gray-600">
                              {t.year}: {new Intl.NumberFormat('en-IN').format(t.revenue)} {t.currency}
                            </p>
                          ))}
                        </div>
                      </div>
                    )}

                    {viewingCompany.profit && viewingCompany.profit.length > 0 && (
                      <div>
                        <Label className="font-medium">Profit History:</Label>
                        <div className="mt-2 space-y-1">
                          {viewingCompany.profit.map((p, index) => (
                            <p key={index} className="text-sm text-gray-600">
                              {p.year}: {new Intl.NumberFormat('en-IN').format(p.profit)} {p.currency}
                            </p>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              </div>

              {/* Location Information */}
              <div className="space-y-4">
                <h4 className="font-semibold text-lg border-b pb-2">Location Information</h4>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <Label className="font-medium">Address:</Label>
                    <p className="text-gray-600">{viewingCompany.address}</p>
                  </div>
                  <div>
                    <Label className="font-medium">Location:</Label>
                    <p className="text-gray-600">
                      {getCityName(viewingCompany.city_id)}, {getStateName(viewingCompany.state_id)}, {getCountryName(viewingCompany.country_id)}
                    </p>
                  </div>
                </div>
              </div>

              {/* Company Profile */}
              {viewingCompany.company_profile && (
                <div className="space-y-4">
                  <h4 className="font-semibold text-lg border-b pb-2">Company Profile</h4>
                  <p className="text-gray-600 leading-relaxed">{viewingCompany.company_profile}</p>
                </div>
              )}

              {/* Documents */}
              {viewingCompany.documents && viewingCompany.documents.length > 0 && (
                <div className="space-y-4">
                  <h4 className="font-semibold text-lg border-b pb-2">Documents</h4>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {viewingCompany.documents.map((doc, index) => (
                      <div key={index} className="flex items-center space-x-2 p-3 bg-gray-50 rounded">
                        <FileDown className="h-4 w-4 text-gray-500" />
                        <div>
                          <p className="font-medium">{doc.original_filename}</p>
                          <p className="text-sm text-gray-500">
                            {(doc.file_size / 1024 / 1024).toFixed(2)} MB
                          </p>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Parent Company Info */}
              {viewingCompany.is_child && viewingCompany.parent_company_id && (
                <div className="space-y-4">
                  <h4 className="font-semibold text-lg border-b pb-2">Parent Company</h4>
                  <p className="text-gray-600">Parent Company ID: {viewingCompany.parent_company_id}</p>
                </div>
              )}

              {/* System Information */}
              <div className="bg-gray-50 p-4 rounded-lg">
                <h4 className="font-semibold text-lg mb-3">System Information</h4>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
                  <div>
                    <Label className="font-medium">Created:</Label>
                    <p className="text-gray-600">
                      {new Date(viewingCompany.created_at).toLocaleString()}
                    </p>
                  </div>
                  <div>
                    <Label className="font-medium">Last Updated:</Label>
                    <p className="text-gray-600">
                      {new Date(viewingCompany.updated_at).toLocaleString()}
                    </p>
                  </div>
                  <div>
                    <Label className="font-medium">Status:</Label>
                    <Badge variant={viewingCompany.active_status ? 'default' : 'destructive'}>
                      {viewingCompany.active_status ? 'Active' : 'Inactive'}
                    </Badge>
                  </div>
                  <div>
                    <Label className="font-medium">Company ID:</Label>
                    <p className="text-xs text-gray-500 font-mono">{viewingCompany.id}</p>
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