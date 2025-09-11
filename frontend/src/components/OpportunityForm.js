import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Badge } from '@/components/ui/badge';
import { ArrowLeft, Save, Target, Building, User, DollarSign } from 'lucide-react';
import { usePermissions } from '../contexts/PermissionContext';
import axios from 'axios';

// Form validation schema
const opportunitySchema = z.object({
  project_title: z.string().min(1, 'Project title is required'),
  company_id: z.string().min(1, 'Company is required'),
  stage_id: z.string().min(1, 'Stage is required'),
  status: z.enum(['Open', 'Won', 'Lost', 'On Hold']),
  expected_revenue: z.number().min(0, 'Expected revenue must be positive'),
  currency_id: z.string().min(1, 'Currency is required'),
  win_probability: z.number().min(0).max(100, 'Win probability must be between 0-100'),
  lead_owner_id: z.string().min(1, 'Lead owner is required'),
  product_interest: z.string().optional(),
  close_date: z.string().optional(),
  lead_id: z.string().optional()
});

const OpportunityForm = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const { permissions } = usePermissions();
  const isEdit = Boolean(id);
  
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState(null);

  // Master data
  const [companies, setCompanies] = useState([]);
  const [stages, setStages] = useState([]);
  const [currencies, setCurrencies] = useState([]);
  const [users, setUsers] = useState([]);

  const baseURL = process.env.REACT_APP_BACKEND_URL;

  const {
    register,
    handleSubmit,
    setValue,
    watch,
    formState: { errors },
    reset
  } = useForm({
    resolver: zodResolver(opportunitySchema),
    defaultValues: {
      project_title: '',
      company_id: '',
      stage_id: '',
      status: 'Open',
      expected_revenue: 0,
      currency_id: '',
      win_probability: 50,
      lead_owner_id: '',
      product_interest: '',
      close_date: '',
      lead_id: ''
    }
  });

  const watchedFields = watch(['expected_revenue', 'win_probability']);

  useEffect(() => {
    fetchMasterData();
    if (isEdit) {
      fetchOpportunity();
    } else {
      setLoading(false);
    }
  }, [id]);

  const fetchMasterData = async () => {
    try {
      const token = localStorage.getItem('token');
      const headers = { Authorization: `Bearer ${token}` };

      const [companiesRes, stagesRes, currenciesRes, usersRes] = await Promise.all([
        axios.get(`${baseURL}/api/companies`, { headers }),
        axios.get(`${baseURL}/api/mst/stages`, { headers }),
        axios.get(`${baseURL}/api/mst/currencies`, { headers }),
        axios.get(`${baseURL}/api/users`, { headers })
      ]);

      setCompanies(companiesRes.data || []);
      setStages(stagesRes.data || []);
      setCurrencies(currenciesRes.data || []);
      setUsers(usersRes.data || []);
    } catch (error) {
      console.error('Error fetching master data:', error);
      setError('Failed to load form data');
    }
  };

  const fetchOpportunity = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(`${baseURL}/api/opportunities/${id}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      const opportunityData = response.data;
      
      // Convert close_date to proper format for date input
      if (opportunityData.close_date) {
        opportunityData.close_date = new Date(opportunityData.close_date).toISOString().split('T')[0];
      }
      
      reset(opportunityData);
    } catch (error) {
      console.error('Error fetching opportunity:', error);
      setError('Failed to load opportunity data');
    } finally {
      setLoading(false);
    }
  };

  const onSubmit = async (data) => {
    try {
      setSaving(true);
      const token = localStorage.getItem('token');
      
      // Calculate weighted revenue
      const weightedRevenue = (data.expected_revenue * data.win_probability) / 100;
      
      const submitData = {
        ...data,
        weighted_revenue: weightedRevenue,
        expected_revenue: Number(data.expected_revenue),
        win_probability: Number(data.win_probability)
      };

      let response;
      if (isEdit) {
        response = await axios.put(`${baseURL}/api/opportunities/${id}`, submitData, {
          headers: { Authorization: `Bearer ${token}` }
        });
      } else {
        response = await axios.post(`${baseURL}/api/opportunities`, submitData, {
          headers: { Authorization: `Bearer ${token}` }
        });
      }

      console.log('Opportunity saved:', response.data);
      navigate('/opportunities');
    } catch (error) {
      console.error('Error saving opportunity:', error);
      setError(error.response?.data?.detail || `Failed to ${isEdit ? 'update' : 'create'} opportunity`);
    } finally {
      setSaving(false);
    }
  };

  const getCompanyName = (companyId) => {
    const company = companies.find(c => c.id === companyId);
    return company ? company.name : 'Unknown Company';
  };

  const getStageName = (stageId) => {
    const stage = stages.find(s => s.id === stageId);
    return stage ? `${stage.stage_code} - ${stage.stage_name}` : 'Unknown Stage';
  };

  const getCurrencySymbol = (currencyId) => {
    const currency = currencies.find(c => c.id === currencyId);
    return currency ? currency.symbol : '₹';
  };

  const getUserName = (userId) => {
    const user = users.find(u => u.id === userId);
    return user ? user.username : 'Unknown User';
  };

  const calculateWeightedRevenue = () => {
    const revenue = Number(watchedFields[0]) || 0;
    const probability = Number(watchedFields[1]) || 0;
    return (revenue * probability) / 100;
  };

  const formatCurrency = (amount, currencyId) => {
    const symbol = getCurrencySymbol(currencyId);
    return `${symbol}${Number(amount).toLocaleString('en-IN')}`;
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
          <h2 className="text-2xl font-bold text-gray-900 mb-2">Error Loading Form</h2>
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
            <h1 className="text-3xl font-bold text-gray-900">
              {isEdit ? 'Edit Opportunity' : 'Create Opportunity'}
            </h1>
            <p className="text-gray-600 mt-1">
              {isEdit ? 'Update opportunity details' : 'Create a new sales opportunity'}
            </p>
          </div>
        </div>
      </div>

      <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Main Form */}
          <div className="lg:col-span-2">
            {/* Basic Information */}
            <Card className="mb-6">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Target className="w-5 h-5" />
                  Basic Information
                </CardTitle>
                <CardDescription>
                  Enter the basic details for this opportunity
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <Label htmlFor="project_title">Project Title *</Label>
                    <Input
                      id="project_title"
                      {...register('project_title')}
                      placeholder="Enter project title"
                      className={errors.project_title ? 'border-red-500' : ''}
                    />
                    {errors.project_title && (
                      <p className="text-sm text-red-600 mt-1">{errors.project_title.message}</p>
                    )}
                  </div>

                  <div>
                    <Label htmlFor="company_id">Company *</Label>
                    <Select value={watch('company_id')} onValueChange={(value) => setValue('company_id', value)}>
                      <SelectTrigger className={errors.company_id ? 'border-red-500' : ''}>
                        <SelectValue placeholder="Select company" />
                      </SelectTrigger>
                      <SelectContent>
                        {companies.map((company) => (
                          <SelectItem key={company.id} value={company.id}>
                            {company.name}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                    {errors.company_id && (
                      <p className="text-sm text-red-600 mt-1">{errors.company_id.message}</p>
                    )}
                  </div>

                  <div>
                    <Label htmlFor="stage_id">Stage *</Label>
                    <Select value={watch('stage_id')} onValueChange={(value) => setValue('stage_id', value)}>
                      <SelectTrigger className={errors.stage_id ? 'border-red-500' : ''}>
                        <SelectValue placeholder="Select stage" />
                      </SelectTrigger>
                      <SelectContent>
                        {stages.map((stage) => (
                          <SelectItem key={stage.id} value={stage.id}>
                            {stage.stage_code} - {stage.stage_name}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                    {errors.stage_id && (
                      <p className="text-sm text-red-600 mt-1">{errors.stage_id.message}</p>
                    )}
                  </div>

                  <div>
                    <Label htmlFor="status">Status *</Label>
                    <Select value={watch('status')} onValueChange={(value) => setValue('status', value)}>
                      <SelectTrigger className={errors.status ? 'border-red-500' : ''}>
                        <SelectValue placeholder="Select status" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="Open">Open</SelectItem>
                        <SelectItem value="Won">Won</SelectItem>
                        <SelectItem value="Lost">Lost</SelectItem>
                        <SelectItem value="On Hold">On Hold</SelectItem>
                      </SelectContent>
                    </Select>
                    {errors.status && (
                      <p className="text-sm text-red-600 mt-1">{errors.status.message}</p>
                    )}
                  </div>

                  <div>
                    <Label htmlFor="lead_owner_id">Lead Owner *</Label>
                    <Select value={watch('lead_owner_id')} onValueChange={(value) => setValue('lead_owner_id', value)}>
                      <SelectTrigger className={errors.lead_owner_id ? 'border-red-500' : ''}>
                        <SelectValue placeholder="Select lead owner" />
                      </SelectTrigger>
                      <SelectContent>
                        {users.map((user) => (
                          <SelectItem key={user.id} value={user.id}>
                            {user.username}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                    {errors.lead_owner_id && (
                      <p className="text-sm text-red-600 mt-1">{errors.lead_owner_id.message}</p>
                    )}
                  </div>

                  <div>
                    <Label htmlFor="close_date">Expected Close Date</Label>
                    <Input
                      id="close_date"
                      type="date"
                      {...register('close_date')}
                      className={errors.close_date ? 'border-red-500' : ''}
                    />
                    {errors.close_date && (
                      <p className="text-sm text-red-600 mt-1">{errors.close_date.message}</p>
                    )}
                  </div>
                </div>

                <div>
                  <Label htmlFor="product_interest">Product Interest</Label>
                  <Textarea
                    id="product_interest"
                    {...register('product_interest')}
                    placeholder="Describe the customer's product interest..."
                    rows={3}
                  />
                </div>

                {watch('lead_id') && (
                  <div>
                    <Label>Converted from Lead</Label>
                    <div className="flex items-center gap-2 mt-1">
                      <Badge variant="outline" className="bg-blue-50 text-blue-700 border-blue-200">
                        {watch('lead_id')}
                      </Badge>
                      <span className="text-sm text-gray-600">This opportunity was converted from a lead</span>
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
                  Financial Information
                </CardTitle>
                <CardDescription>
                  Set the financial parameters for this opportunity
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div>
                    <Label htmlFor="expected_revenue">Expected Revenue *</Label>
                    <Input
                      id="expected_revenue"
                      type="number"
                      step="0.01"
                      {...register('expected_revenue', { valueAsNumber: true })}
                      placeholder="0.00"
                      className={errors.expected_revenue ? 'border-red-500' : ''}
                    />
                    {errors.expected_revenue && (
                      <p className="text-sm text-red-600 mt-1">{errors.expected_revenue.message}</p>
                    )}
                  </div>

                  <div>
                    <Label htmlFor="currency_id">Currency *</Label>
                    <Select value={watch('currency_id')} onValueChange={(value) => setValue('currency_id', value)}>
                      <SelectTrigger className={errors.currency_id ? 'border-red-500' : ''}>
                        <SelectValue placeholder="Select currency" />
                      </SelectTrigger>
                      <SelectContent>
                        {currencies.map((currency) => (
                          <SelectItem key={currency.id} value={currency.id}>
                            {currency.symbol} - {currency.name}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                    {errors.currency_id && (
                      <p className="text-sm text-red-600 mt-1">{errors.currency_id.message}</p>
                    )}
                  </div>

                  <div>
                    <Label htmlFor="win_probability">Win Probability (%) *</Label>
                    <Input
                      id="win_probability"
                      type="number"
                      min="0"
                      max="100"
                      {...register('win_probability', { valueAsNumber: true })}
                      placeholder="50"
                      className={errors.win_probability ? 'border-red-500' : ''}
                    />
                    {errors.win_probability && (
                      <p className="text-sm text-red-600 mt-1">{errors.win_probability.message}</p>
                    )}
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Sidebar - Summary */}
          <div className="lg:col-span-1">
            <Card className="sticky top-6">
              <CardHeader>
                <CardTitle className="text-lg">Opportunity Summary</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                {watch('project_title') && (
                  <div>
                    <Label className="text-sm text-gray-600">Project Title</Label>
                    <p className="font-medium">{watch('project_title')}</p>
                  </div>
                )}

                {watch('company_id') && (
                  <div>
                    <Label className="text-sm text-gray-600">Company</Label>
                    <p className="font-medium">{getCompanyName(watch('company_id'))}</p>
                  </div>
                )}

                {watch('stage_id') && (
                  <div>
                    <Label className="text-sm text-gray-600">Stage</Label>
                    <Badge variant="outline" className="mt-1">
                      {getStageName(watch('stage_id'))}
                    </Badge>
                  </div>
                )}

                {watch('lead_owner_id') && (
                  <div>
                    <Label className="text-sm text-gray-600">Lead Owner</Label>
                    <p className="font-medium">{getUserName(watch('lead_owner_id'))}</p>
                  </div>
                )}

                {watch('expected_revenue') > 0 && (
                  <div>
                    <Label className="text-sm text-gray-600">Expected Revenue</Label>
                    <p className="text-lg font-semibold text-green-600">
                      {formatCurrency(watch('expected_revenue'), watch('currency_id'))}
                    </p>
                  </div>
                )}

                {watch('win_probability') > 0 && (
                  <div>
                    <Label className="text-sm text-gray-600">Win Probability</Label>
                    <div className="flex items-center gap-2">
                      <div className="w-full bg-gray-200 rounded-full h-2">
                        <div 
                          className="bg-gradient-to-r from-red-500 via-yellow-500 to-green-500 h-2 rounded-full"
                          style={{ width: `${watch('win_probability')}%` }}
                        ></div>
                      </div>
                      <span className="font-medium">{watch('win_probability')}%</span>
                    </div>
                  </div>
                )}

                {watch('expected_revenue') > 0 && watch('win_probability') > 0 && (
                  <div>
                    <Label className="text-sm text-gray-600">Weighted Revenue</Label>
                    <p className="text-lg font-semibold text-purple-600">
                      {formatCurrency(calculateWeightedRevenue(), watch('currency_id'))}
                    </p>
                  </div>
                )}

                <div className="pt-4 space-y-2">
                  <Button 
                    type="submit" 
                    className="w-full bg-blue-600 hover:bg-blue-700"
                    disabled={saving}
                  >
                    <Save className="w-4 h-4 mr-2" />
                    {saving ? 'Saving...' : (isEdit ? 'Update Opportunity' : 'Create Opportunity')}
                  </Button>
                  
                  <Button 
                    type="button" 
                    variant="outline" 
                    className="w-full"
                    onClick={() => navigate('/opportunities')}
                  >
                    Cancel
                  </Button>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      </form>
    </div>
  );
};

export default OpportunityForm;