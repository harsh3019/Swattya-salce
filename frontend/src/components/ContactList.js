import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { Badge } from './ui/badge';
import { Label } from './ui/label';
import { Input } from './ui/input';
import { Button } from './ui/button';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './ui/select';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from './ui/dialog';
import { Alert, AlertDescription } from './ui/alert';
import { Checkbox } from './ui/checkbox';
import { AlertCircle, Plus, Users, Eye, Edit, Trash2, FileDown, Phone, Mail, MapPin, Building, UserCheck, Crown } from 'lucide-react';
import { toast } from 'sonner';
import PermissionDataTable from './PermissionDataTable';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export const ContactList = () => {
  const navigate = useNavigate();
  const [contacts, setContacts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [searchTerm, setSearchTerm] = useState('');
  const [sortField, setSortField] = useState('created_at');
  const [sortDirection, setSortDirection] = useState('desc');
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [viewingContact, setViewingContact] = useState(null);
  
  // Filters
  const [filters, setFilters] = useState({
    company_id: '',
    designation_id: '',
    spoc: null,
    decision_maker: null,
    is_active: null
  });
  
  // Bulk operations
  const [selectedContacts, setSelectedContacts] = useState([]);
  const [bulkLoading, setBulkLoading] = useState(false);
  
  // Master data for display and filtering
  const [masterData, setMasterData] = useState({});

  useEffect(() => {
    fetchContacts();
    fetchMasterData();
  }, [currentPage, searchTerm, sortField, sortDirection, filters]);

  const fetchContacts = async () => {
    try {
      setLoading(true);
      setError('');
      
      const params = new URLSearchParams({
        page: currentPage.toString(),
        limit: '50',
        sort_by: sortField,
        sort_order: sortDirection
      });
      
      if (searchTerm) params.append('search', searchTerm);
      if (filters.company_id) params.append('company_id', filters.company_id);
      if (filters.designation_id) params.append('designation_id', filters.designation_id);
      if (filters.spoc !== null) params.append('spoc', filters.spoc.toString());
      if (filters.decision_maker !== null) params.append('decision_maker', filters.decision_maker.toString());
      if (filters.is_active !== null) params.append('is_active', filters.is_active.toString());
      
      const response = await axios.get(`${API}/contacts?${params}`);
      const data = response.data;
      
      setContacts(data.contacts || []);
      setTotalPages(data.total_pages || 1);
      
    } catch (err) {
      const errorMsg = err.response?.data?.detail || 'Failed to fetch contacts';
      setError(errorMsg);
      toast.error(errorMsg);
    } finally {
      setLoading(false);
    }
  };

  const fetchMasterData = async () => {
    try {
      const endpoints = ['companies', 'designations', 'countries', 'cities'];
      
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

  const handleDelete = async (contact) => {
    if (window.confirm(`Are you sure you want to delete contact "${contact.first_name} ${contact.last_name || ''}"?`)) {
      try {
        await axios.delete(`${API}/contacts/${contact.id}`);
        toast.success('Contact deleted successfully');
        fetchContacts();
      } catch (err) {
        const errorMsg = err.response?.data?.detail || 'Failed to delete contact';
        toast.error(errorMsg);
      }
    }
  };

  const handleBulkUpdate = async (action) => {
    if (selectedContacts.length === 0) {
      toast.error('Please select contacts to update');
      return;
    }

    if (window.confirm(`Are you sure you want to ${action} ${selectedContacts.length} selected contact(s)?`)) {
      setBulkLoading(true);
      try {
        await axios.post(`${API}/contacts/bulk`, {
          contact_ids: selectedContacts,
          action: action
        });
        
        toast.success(`Successfully ${action}d ${selectedContacts.length} contact(s)`);
        setSelectedContacts([]);
        fetchContacts();
      } catch (err) {
        const errorMsg = err.response?.data?.detail || `Failed to ${action} contacts`;
        toast.error(errorMsg);
      } finally {
        setBulkLoading(false);
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
      const params = new URLSearchParams();
      if (filters.company_id) params.append('company_id', filters.company_id);
      if (filters.designation_id) params.append('designation_id', filters.designation_id);
      if (filters.spoc !== null) params.append('spoc', filters.spoc.toString());
      if (filters.decision_maker !== null) params.append('decision_maker', filters.decision_maker.toString());
      if (filters.is_active !== null) params.append('is_active', filters.is_active.toString());
      
      const response = await axios.get(`${API}/contacts/export?${params}`);
      const csvContent = convertToCSV(response.data);
      downloadCSV(csvContent, 'contacts_export.csv');
      toast.success('Contacts exported successfully');
    } catch (err) {
      const errorMsg = err.response?.data?.detail || 'Failed to export contacts';
      toast.error(errorMsg);
    }
  };

  const convertToCSV = (data) => {
    if (!data.length) return '';
    
    const headers = ['Sr No', 'Name', 'Company', 'Email', 'Phone', 'Designation', 'Decision Maker', 'SPOC', 'Address', 'Country', 'City', 'Created At'];
    const rows = data.map((contact, index) => [
      index + 1,
      `${contact.salutation || ''} ${contact.first_name} ${contact.last_name || ''}`.trim(),
      getCompanyName(contact.company_id),
      contact.email || '',
      contact.primary_phone || '',
      getDesignationName(contact.designation_id),
      contact.decision_maker ? 'Yes' : 'No',
      contact.spoc ? 'Yes' : 'No',
      contact.address || '',
      getCountryName(contact.country_id),
      getCityName(contact.city_id),
      new Date(contact.created_at).toLocaleDateString()
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
  const getCompanyName = (companyId) => {
    const company = masterData.companies?.find(c => c.id === companyId);
    return company?.name || 'Unknown';
  };

  const getDesignationName = (designationId) => {
    if (!designationId) return 'Not specified';
    const designation = masterData.designations?.find(d => d.id === designationId);
    return designation?.name || 'Unknown';
  };

  const getCountryName = (countryId) => {
    if (!countryId) return '';
    const country = masterData.countries?.find(c => c.id === countryId);
    return country?.name || '';
  };

  const getCityName = (cityId) => {
    if (!cityId) return '';
    const city = masterData.cities?.find(c => c.id === cityId);
    return city?.name || '';
  };

  const handleSelectAll = (checked) => {
    if (checked) {
      setSelectedContacts(contacts.map(c => c.id));
    } else {
      setSelectedContacts([]);
    }
  };

  const handleSelectContact = (contactId, checked) => {
    if (checked) {
      setSelectedContacts(prev => [...prev, contactId]);
    } else {
      setSelectedContacts(prev => prev.filter(id => id !== contactId));
    }
  };

  const columns = [
    {
      key: 'select',
      label: (
        <Checkbox
          checked={selectedContacts.length === contacts.length && contacts.length > 0}
          onCheckedChange={handleSelectAll}
        />
      ),
      render: (contact) => (
        <Checkbox
          checked={selectedContacts.includes(contact.id)}
          onCheckedChange={(checked) => handleSelectContact(contact.id, checked)}
        />
      )
    },
    { 
      key: 'name', 
      label: 'Name', 
      sortable: true,
      render: (contact) => (
        <div className="flex items-center space-x-2">
          <Users className="h-4 w-4 text-blue-600" />
          <div>
            <p className="font-medium">
              {contact.salutation} {contact.first_name} {contact.last_name || ''}
            </p>
            <div className="flex items-center space-x-2 text-xs text-gray-500">
              {contact.decision_maker && (
                <Badge variant="outline" className="bg-green-50 text-green-700 border-green-200">
                  <UserCheck className="h-3 w-3 mr-1" />
                  Decision Maker
                </Badge>
              )}
              {contact.spoc && (
                <Badge variant="outline" className="bg-blue-50 text-blue-700 border-blue-200">
                  <Crown className="h-3 w-3 mr-1" />
                  SPOC
                </Badge>
              )}
            </div>
          </div>
        </div>
      )
    },
    { 
      key: 'company', 
      label: 'Company', 
      sortable: false,
      render: (contact) => (
        <div className="flex items-center space-x-2">
          <Building className="h-4 w-4 text-gray-400" />
          <span>{getCompanyName(contact.company_id)}</span>
        </div>
      )
    },
    { 
      key: 'email', 
      label: 'Email', 
      sortable: true,
      render: (contact) => (
        <div className="flex items-center space-x-2">
          <Mail className="h-4 w-4 text-gray-400" />
          <a href={`mailto:${contact.email}`} className="text-blue-600 hover:text-blue-800">
            {contact.email}
          </a>
        </div>
      )
    },
    { 
      key: 'primary_phone', 
      label: 'Phone', 
      sortable: true,
      render: (contact) => (
        <div className="flex items-center space-x-2">
          <Phone className="h-4 w-4 text-gray-400" />
          <a href={`tel:${contact.primary_phone}`} className="text-blue-600 hover:text-blue-800">
            {contact.primary_phone}
          </a>
        </div>
      )
    },
    { 
      key: 'designation', 
      label: 'Designation', 
      sortable: false,
      render: (contact) => (
        <span className="text-sm">{getDesignationName(contact.designation_id)}</span>
      )
    },
    { 
      key: 'location', 
      label: 'Location', 
      sortable: false,
      render: (contact) => (
        <div className="flex items-center space-x-2 text-sm">
          <MapPin className="h-4 w-4 text-gray-400" />
          <div>
            {getCityName(contact.city_id) && <p>{getCityName(contact.city_id)}</p>}
            {getCountryName(contact.country_id) && <p className="text-gray-500">{getCountryName(contact.country_id)}</p>}
          </div>
        </div>
      )
    },
    { 
      key: 'is_active', 
      label: 'Status', 
      sortable: true,
      render: (contact) => (
        <Badge variant={contact.is_active ? 'default' : 'secondary'}>
          {contact.is_active ? 'Active' : 'Inactive'}
        </Badge>
      )
    },
    { 
      key: 'created_at', 
      label: 'Created', 
      sortable: true,
      render: (contact) => (
        <div className="text-sm">
          <p>{new Date(contact.created_at).toLocaleDateString()}</p>
          <p className="text-gray-500">{new Date(contact.created_at).toLocaleTimeString()}</p>
        </div>
      )
    }
  ];

  const filteredContacts = contacts; // Filtering is done server-side

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold">Contacts</h1>
          <p className="text-gray-600">Manage contact information and relationships</p>
        </div>
        <Button onClick={() => navigate('/contacts/add')} className="bg-blue-600 hover:bg-blue-700">
          <Plus className="h-4 w-4 mr-2" />
          Add Contact
        </Button>
      </div>

      {/* Filters and Bulk Actions */}
      <div className="bg-white p-4 rounded-lg border space-y-4">
        <div className="flex items-center justify-between">
          <h3 className="font-medium">Filters & Actions</h3>
          {selectedContacts.length > 0 && (
            <div className="flex items-center space-x-2">
              <span className="text-sm text-gray-600">{selectedContacts.length} selected</span>
              <Button 
                size="sm" 
                onClick={() => handleBulkUpdate('activate')}
                disabled={bulkLoading}
                className="bg-green-600 hover:bg-green-700"
              >
                Activate
              </Button>
              <Button 
                size="sm" 
                onClick={() => handleBulkUpdate('deactivate')}
                disabled={bulkLoading}
                variant="outline"
              >
                Deactivate
              </Button>
            </div>
          )}
        </div>
        
        <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
          <div>
            <Label>Company</Label>
            <Select 
              value={filters.company_id} 
              onValueChange={(value) => setFilters(prev => ({...prev, company_id: value}))}
            >
              <SelectTrigger>
                <SelectValue placeholder="All Companies" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Companies</SelectItem>
                {masterData.companies?.map((company) => (
                  <SelectItem key={company.id} value={company.id}>
                    {company.name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <div>
            <Label>Designation</Label>
            <Select 
              value={filters.designation_id} 
              onValueChange={(value) => setFilters(prev => ({...prev, designation_id: value}))}
            >
              <SelectTrigger>
                <SelectValue placeholder="All Designations" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Designations</SelectItem>
                {masterData.designations?.map((designation) => (
                  <SelectItem key={designation.id} value={designation.id}>
                    {designation.name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <div>
            <Label>SPOC</Label>
            <Select 
              value={filters.spoc === null ? '' : filters.spoc.toString()} 
              onValueChange={(value) => setFilters(prev => ({...prev, spoc: value === '' ? null : value === 'true'}))}
            >
              <SelectTrigger>
                <SelectValue placeholder="All" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="">All</SelectItem>
                <SelectItem value="true">SPOC Only</SelectItem>
                <SelectItem value="false">Non-SPOC</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <div>
            <Label>Decision Maker</Label>
            <Select 
              value={filters.decision_maker === null ? '' : filters.decision_maker.toString()} 
              onValueChange={(value) => setFilters(prev => ({...prev, decision_maker: value === '' ? null : value === 'true'}))}
            >
              <SelectTrigger>
                <SelectValue placeholder="All" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="">All</SelectItem>
                <SelectItem value="true">Decision Makers</SelectItem>
                <SelectItem value="false">Non-Decision Makers</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <div>
            <Label>Status</Label>
            <Select 
              value={filters.is_active === null ? '' : filters.is_active.toString()} 
              onValueChange={(value) => setFilters(prev => ({...prev, is_active: value === '' ? null : value === 'true'}))}
            >
              <SelectTrigger>
                <SelectValue placeholder="All" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="">All</SelectItem>
                <SelectItem value="true">Active</SelectItem>
                <SelectItem value="false">Inactive</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </div>
      </div>

      {error && (
        <Alert className="border-red-200 bg-red-50">
          <AlertCircle className="h-4 w-4 text-red-600" />
          <AlertDescription className="text-red-800">{error}</AlertDescription>
        </Alert>
      )}

      {/* Data Table */}
      <PermissionDataTable
        data={filteredContacts}
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
        onView={(contact) => setViewingContact(contact)}
        onEdit={(contact) => navigate(`/contacts/edit/${contact.id}`)}
        onDelete={handleDelete}
        onAdd={() => navigate('/contacts/add')}
        title="Contacts"
        modulePath="/contacts"
        entityName="contacts"
      />

      {/* View Contact Dialog */}
      <Dialog open={!!viewingContact} onOpenChange={() => setViewingContact(null)}>
        <DialogContent className="max-w-3xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="flex items-center space-x-2">
              <Users className="h-5 w-5" />
              <span>Contact Details</span>
            </DialogTitle>
          </DialogHeader>
          
          {viewingContact && (
            <div className="space-y-6">
              {/* Header Info */}
              <div className="bg-blue-50 p-4 rounded-lg">
                <div className="flex justify-between items-start">
                  <div>
                    <h3 className="text-xl font-bold text-blue-900">
                      {viewingContact.salutation} {viewingContact.first_name} {viewingContact.last_name || ''}
                    </h3>
                    <p className="text-blue-700">{getCompanyName(viewingContact.company_id)}</p>
                    <p className="text-blue-600">{getDesignationName(viewingContact.designation_id)}</p>
                  </div>
                  <div className="text-right space-y-1">
                    <Badge variant={viewingContact.is_active ? 'default' : 'secondary'}>
                      {viewingContact.is_active ? 'Active' : 'Inactive'}
                    </Badge>
                    {viewingContact.decision_maker && (
                      <Badge variant="outline" className="bg-green-50 text-green-700 border-green-200 block">
                        <UserCheck className="h-3 w-3 mr-1" />
                        Decision Maker
                      </Badge>
                    )}
                    {viewingContact.spoc && (
                      <Badge variant="outline" className="bg-blue-50 text-blue-700 border-blue-200 block">
                        <Crown className="h-3 w-3 mr-1" />
                        SPOC
                      </Badge>
                    )}
                  </div>
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {/* Contact Information */}
                <div className="space-y-4">
                  <h4 className="font-semibold text-lg border-b pb-2">Contact Information</h4>
                  
                  <div className="space-y-3">
                    <div className="flex items-center space-x-2">
                      <Mail className="h-4 w-4 text-gray-500" />
                      <div>
                        <Label className="font-medium">Email:</Label>
                        <p className="text-gray-600">
                          <a href={`mailto:${viewingContact.email}`} className="text-blue-600 hover:text-blue-800">
                            {viewingContact.email}
                          </a>
                        </p>
                      </div>
                    </div>
                    
                    <div className="flex items-center space-x-2">
                      <Phone className="h-4 w-4 text-gray-500" />
                      <div>
                        <Label className="font-medium">Phone:</Label>
                        <p className="text-gray-600">
                          <a href={`tel:${viewingContact.primary_phone}`} className="text-blue-600 hover:text-blue-800">
                            {viewingContact.primary_phone}
                          </a>
                        </p>
                      </div>
                    </div>

                    {viewingContact.option && (
                      <div>
                        <Label className="font-medium">Preferred Contact:</Label>
                        <p className="text-gray-600 capitalize">{viewingContact.option}</p>
                      </div>
                    )}
                  </div>
                </div>

                {/* Location Information */}
                <div className="space-y-4">
                  <h4 className="font-semibold text-lg border-b pb-2">Location Information</h4>
                  
                  <div className="space-y-3">
                    {viewingContact.address && (
                      <div>
                        <Label className="font-medium">Address:</Label>
                        <p className="text-gray-600">{viewingContact.address}</p>
                      </div>
                    )}
                    
                    <div className="flex items-center space-x-2">
                      <MapPin className="h-4 w-4 text-gray-500" />
                      <div>
                        <Label className="font-medium">Location:</Label>
                        <p className="text-gray-600">
                          {getCityName(viewingContact.city_id) && `${getCityName(viewingContact.city_id)}, `}
                          {getCountryName(viewingContact.country_id)}
                        </p>
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              {/* Comments */}
              {viewingContact.comments && (
                <div className="space-y-4">
                  <h4 className="font-semibold text-lg border-b pb-2">Comments</h4>
                  <p className="text-gray-600 leading-relaxed">{viewingContact.comments}</p>
                </div>
              )}

              {/* System Information */}
              <div className="bg-gray-50 p-4 rounded-lg">
                <h4 className="font-semibold text-lg mb-3">System Information</h4>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
                  <div>
                    <Label className="font-medium">Created:</Label>
                    <p className="text-gray-600">
                      {new Date(viewingContact.created_at).toLocaleString()}
                    </p>
                  </div>
                  <div>
                    <Label className="font-medium">Last Updated:</Label>
                    <p className="text-gray-600">
                      {new Date(viewingContact.updated_at).toLocaleString()}
                    </p>
                  </div>
                  <div>
                    <Label className="font-medium">Contact ID:</Label>
                    <p className="text-xs text-gray-500 font-mono">{viewingContact.id}</p>
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