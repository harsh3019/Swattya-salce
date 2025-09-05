import React, { useState, useEffect } from 'react';
import { useForm, Controller, useFieldArray } from 'react-hook-form';
import { useParams, useNavigate } from 'react-router-dom';
import { zodResolver } from '@hookform/resolvers/zod';
import axios from 'axios';
import * as z from 'zod';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Label } from './ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './ui/select';
import { Textarea } from './ui/textarea';
import { Checkbox } from './ui/checkbox';
import { Switch } from './ui/switch';
import { Progress } from './ui/progress';
import { Alert, AlertDescription } from './ui/alert';
import { AlertCircle, Upload, Plus, Trash2, CheckCircle } from 'lucide-react';
import { toast } from 'sonner';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Multi-step form schema
const companySchema = z.object({
  // Step 1: General Info
  company_name: z.string().min(3, 'Company name must be at least 3 characters').max(100, 'Company name must be less than 100 characters'),
  domestic_international: z.enum(['Domestic', 'International']),
  gst_number: z.string().optional(),
  pan_number: z.string().optional(), 
  vat_number: z.string().optional(),
  company_type_id: z.string().min(1, 'Company type is required'),
  account_type_id: z.string().min(1, 'Account type is required'),
  region_id: z.string().min(1, 'Region is required'),
  business_type_id: z.string().min(1, 'Business type is required'),
  industry_id: z.string().min(1, 'Industry is required'),
  sub_industry_id: z.string().min(1, 'Sub-industry is required'),
  website: z.string().url('Must be a valid URL').optional().or(z.literal('')),
  is_child: z.boolean().default(false),
  parent_company_id: z.string().optional(),
  employee_count: z.number().min(1, 'Employee count must be at least 1'),
  
  // Step 2: Location
  address: z.string().min(10, 'Address must be at least 10 characters').max(500, 'Address must be less than 500 characters'),
  country_id: z.string().min(1, 'Country is required'),
  state_id: z.string().min(1, 'State is required'),
  city_id: z.string().min(1, 'City is required'),
  
  // Step 3: Financials
  turnover: z.array(z.object({
    year: z.number().min(2000).max(2030),
    revenue: z.number().min(0),
    currency: z.string().min(3).max(3)
  })).default([]),
  profit: z.array(z.object({
    year: z.number().min(2000).max(2030),
    profit: z.number(),
    currency: z.string().min(3).max(3)
  })).default([]),
  annual_revenue: z.number().min(0, 'Annual revenue must be non-negative'),
  revenue_currency: z.string().min(3, 'Currency is required').max(3),
  
  // Step 4: Profile
  company_profile: z.string().optional(),
  
  // Step 5: Checklist
  valid_gst: z.boolean().default(false),
  active_status: z.boolean().default(true),
  parent_linkage_valid: z.boolean().default(true)
});

const CompanyRegistration = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const isEditing = !!id;
  
  const [currentStep, setCurrentStep] = useState(1);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState(false);
  
  // Master data
  const [masterData, setMasterData] = useState({});
  const [filteredData, setFilteredData] = useState({
    subIndustries: [],
    states: [],
    cities: [],
    parentCompanies: []
  });
  
  // File uploads
  const [uploadedDocuments, setUploadedDocuments] = useState([]);
  
  const form = useForm({
    resolver: zodResolver(companySchema),
    defaultValues: {
      domestic_international: 'Domestic',
      is_child: false,
      employee_count: 1,
      annual_revenue: 0,
      revenue_currency: 'INR',
      turnover: [],
      profit: [],
      valid_gst: false,
      active_status: true,
      parent_linkage_valid: true
    },
    mode: 'onChange'
  });

  const { fields: turnoverFields, append: appendTurnover, remove: removeTurnover } = useFieldArray({
    control: form.control,
    name: 'turnover'
  });

  const { fields: profitFields, append: appendProfit, remove: removeProfit } = useFieldArray({
    control: form.control,
    name: 'profit'
  });

  // Load from localStorage on mount or load existing company for editing
  useEffect(() => {
    if (isEditing) {
      loadExistingCompany();
    } else {
      const savedData = localStorage.getItem('companyRegistrationDraft');
      if (savedData) {
        const parsed = JSON.parse(savedData);
        form.reset(parsed.formData);
        setCurrentStep(parsed.currentStep);
        setUploadedDocuments(parsed.documents || []);
      }
    }
    fetchMasterData();
  }, [id]);

  const loadExistingCompany = async () => {
    try {
      setIsLoading(true);
      const response = await axios.get(`${API}/companies/${id}`);
      const company = response.data;
      
      // Map company data to form format
      const formData = {
        company_name: company.name,
        domestic_international: company.domestic_international,
        gst_number: company.gst_number || '',
        pan_number: company.pan_number || '',
        vat_number: company.vat_number || '',
        company_type_id: company.company_type_id,
        account_type_id: company.account_type_id,
        region_id: company.region_id,
        business_type_id: company.business_type_id,
        industry_id: company.industry_id,
        sub_industry_id: company.sub_industry_id,
        website: company.website || '',
        is_child: company.is_child || false,
        parent_company_id: company.parent_company_id || '',
        employee_count: company.employee_count,
        address: company.address,
        country_id: company.country_id,
        state_id: company.state_id,
        city_id: company.city_id,
        turnover: company.turnover || [],
        profit: company.profit || [],
        annual_revenue: company.annual_revenue,
        revenue_currency: company.revenue_currency,
        company_profile: company.company_profile || '',
        valid_gst: company.valid_gst || false,
        active_status: company.active_status !== undefined ? company.active_status : true,
        parent_linkage_valid: company.parent_linkage_valid !== undefined ? company.parent_linkage_valid : true
      };
      
      form.reset(formData);
      setUploadedDocuments(company.documents || []);
      
    } catch (error) {
      toast.error('Failed to load company data');
      navigate('/companies');
    } finally {
      setIsLoading(false);
    }
  };

  // Auto-save to localStorage (only for new companies, not editing)
  useEffect(() => {
    if (!isEditing) {
      const subscription = form.watch((data) => {
        const draftData = {
          formData: data,
          currentStep,
          documents: uploadedDocuments,
          lastSaved: new Date().toISOString()
        };
        localStorage.setItem('companyRegistrationDraft', JSON.stringify(draftData));
      });
      return () => subscription.unsubscribe();
    }
  }, [currentStep, uploadedDocuments, form, isEditing]);

  const fetchMasterData = async () => {
    try {
      const endpoints = [
        'company-types', 'account-types', 'regions', 'business-types',
        'industries', 'sub-industries', 'countries', 'states', 'cities', 'currencies'
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
      toast.error('Failed to load master data');
      console.error('Master data fetch error:', error);
    }
  };

  // Watch for changes to trigger cascading dropdowns
  const watchIndustry = form.watch('industry_id');
  const watchCountry = form.watch('country_id');
  const watchState = form.watch('state_id');
  const watchDomesticIntl = form.watch('domestic_international');
  const watchIsChild = form.watch('is_child');

  // Update sub-industries when industry changes
  useEffect(() => {
    if (watchIndustry && masterData['sub-industries']) {
      const filtered = masterData['sub-industries'].filter(si => si.industry_id === watchIndustry);
      setFilteredData(prev => ({ ...prev, subIndustries: filtered }));
    }
  }, [watchIndustry, masterData]);

  // Update states when country changes
  useEffect(() => {
    if (watchCountry && masterData.states) {
      const filtered = masterData.states.filter(s => s.country_id === watchCountry);
      setFilteredData(prev => ({ ...prev, states: filtered }));
      form.setValue('state_id', ''); // Reset state selection
      form.setValue('city_id', ''); // Reset city selection
    }
  }, [watchCountry, masterData]);

  // Update cities when state changes
  useEffect(() => {
    if (watchState && masterData.cities) {
      const filtered = masterData.cities.filter(c => c.state_id === watchState);
      setFilteredData(prev => ({ ...prev, cities: filtered }));
      form.setValue('city_id', ''); // Reset city selection
    }
  }, [watchState, masterData]);

  const validateStep = async (step) => {
    const fieldsToValidate = getStepFields(step);
    const isValid = await form.trigger(fieldsToValidate);
    
    if (!isValid) {
      const errors = form.formState.errors;
      const errorMessages = fieldsToValidate
        .filter(field => errors[field])
        .map(field => errors[field]?.message)
        .join(', ');
      setError(`Please fix the following errors: ${errorMessages}`);
      return false;
    }
    
    // Additional validation for specific steps
    if (step === 1 && watchDomesticIntl === 'Domestic') {
      const gst = form.getValues('gst_number');
      const pan = form.getValues('pan_number');
      if (!gst && !pan) {
        setError('GST or PAN number is required for domestic companies');
        return false;
      }
    }
    
    if (step === 5) {
      const validGst = form.getValues('valid_gst');
      const activeStatus = form.getValues('active_status');
      const parentLinkage = form.getValues('parent_linkage_valid');
      
      if (!validGst || !activeStatus || !parentLinkage) {
        setError('All checklist items must be checked before submission');
        return false;
      }
    }
    
    setError('');
    return true;
  };

  const getStepFields = (step) => {
    switch (step) {
      case 1:
        return ['company_name', 'domestic_international', 'company_type_id', 'account_type_id', 
                'region_id', 'business_type_id', 'industry_id', 'sub_industry_id', 'employee_count'];
      case 2:
        return ['address', 'country_id', 'state_id', 'city_id'];
      case 3:
        return ['annual_revenue', 'revenue_currency'];
      case 4:
        return [];
      case 5:
        return ['valid_gst', 'active_status', 'parent_linkage_valid'];
      default:
        return [];
    }
  };

  const nextStep = async () => {
    if (await validateStep(currentStep)) {
      setCurrentStep(prev => Math.min(prev + 1, 5));
    }
  };

  const prevStep = () => {
    setCurrentStep(prev => Math.max(prev - 1, 1));
  };

  const handleFileUpload = async (event) => {
    const file = event.target.files[0];
    if (!file) return;

    // Validate file
    if (file.size > 10 * 1024 * 1024) {
      toast.error('File size must be less than 10MB');
      return;
    }

    const allowedTypes = ['application/pdf', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document', 
                         'image/png', 'image/jpeg'];
    if (!allowedTypes.includes(file.type)) {
      toast.error('Only PDF, DOCX, PNG, and JPG files are allowed');
      return;
    }

    try {
      const formData = new FormData();
      formData.append('file', file);

      const response = await axios.post(`${API}/companies/upload-document`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });

      setUploadedDocuments(prev => [...prev, response.data]);
      toast.success('File uploaded successfully');
    } catch (error) {
      toast.error('Failed to upload file');
      console.error('Upload error:', error);
    }
  };

  const removeDocument = (index) => {
    setUploadedDocuments(prev => prev.filter((_, i) => i !== index));
  };

  const onSubmit = async (data) => {
    if (!(await validateStep(5))) return;

    setIsLoading(true);
    setError('');

    try {
      const companyData = {
        ...data,
        documents: uploadedDocuments
      };

      let response;
      if (isEditing) {
        response = await axios.put(`${API}/companies/${id}`, companyData);
        toast.success('Company updated successfully!');
      } else {
        response = await axios.post(`${API}/companies`, companyData);
        toast.success('Company registered successfully!');
        // Clear localStorage draft only for new companies
        localStorage.removeItem('companyRegistrationDraft');
      }
      
      setSuccess(true);
      
    } catch (error) {
      const errorMsg = error.response?.data?.detail || `Failed to ${isEditing ? 'update' : 'register'} company`;
      setError(errorMsg);
      toast.error(errorMsg);
    } finally {
      setIsLoading(false);
    }
  };

  const getProgressPercentage = () => (currentStep / 5) * 100;

  if (success) {
    return (
      <div className="max-w-2xl mx-auto p-6">
        <Card>
          <CardContent className="pt-6 text-center">
            <CheckCircle className="h-16 w-16 text-green-500 mx-auto mb-4" />
            <h2 className="text-2xl font-bold text-green-700 mb-2">
              {isEditing ? 'Update Successful!' : 'Registration Successful!'}
            </h2>
            <p className="text-gray-600 mb-4">
              Company has been {isEditing ? 'updated' : 'registered'} successfully.
            </p>
            <div className="space-x-4">
              <Button onClick={() => navigate('/companies')}>
                View Companies
              </Button>
              {!isEditing && (
                <Button variant="outline" onClick={() => window.location.reload()}>
                  Register Another Company
                </Button>
              )}
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto p-6">
      <Card>
        <CardHeader>
          <CardTitle>Company Registration</CardTitle>
          <CardDescription>Register a new company in the system</CardDescription>
          
          {/* Progress Bar */}
          <div className="mt-4">
            <div className="flex justify-between text-sm text-gray-600 mb-2">
              <span>Step {currentStep} of 5</span>
              <span>{Math.round(getProgressPercentage())}% Complete</span>
            </div>
            <Progress value={getProgressPercentage()} className="w-full" />
          </div>
          
          {/* Step Labels */}
          <div className="flex justify-between text-xs text-gray-500 mt-2">
            <span className={currentStep >= 1 ? 'text-blue-600 font-medium' : ''}>General Info</span>
            <span className={currentStep >= 2 ? 'text-blue-600 font-medium' : ''}>Location</span>
            <span className={currentStep >= 3 ? 'text-blue-600 font-medium' : ''}>Financials</span>
            <span className={currentStep >= 4 ? 'text-blue-600 font-medium' : ''}>Documents</span>
            <span className={currentStep >= 5 ? 'text-blue-600 font-medium' : ''}>Review</span>
          </div>
        </CardHeader>

        <CardContent>
          {error && (
            <Alert className="mb-6 border-red-200 bg-red-50">
              <AlertCircle className="h-4 w-4 text-red-600" />
              <AlertDescription className="text-red-800">{error}</AlertDescription>
            </Alert>
          )}

          <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-6">
            {/* Step 1: General Info */}
            {currentStep === 1 && (
              <div className="space-y-4">
                <h3 className="text-lg font-semibold">General Information</h3>
                
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <Label htmlFor="company_name">Company Name *</Label>
                    <Input
                      {...form.register('company_name')}
                      id="company_name"
                      placeholder="Enter company name"
                    />
                    {form.formState.errors.company_name && (
                      <p className="text-red-500 text-sm mt-1">{form.formState.errors.company_name.message}</p>
                    )}
                  </div>

                  <div>
                    <Label htmlFor="domestic_international">Business Type *</Label>
                    <Controller
                      name="domestic_international"
                      control={form.control}
                      render={({ field }) => (
                        <Select onValueChange={field.onChange} value={field.value}>
                          <SelectTrigger>
                            <SelectValue placeholder="Select business type" />
                          </SelectTrigger>
                          <SelectContent>
                            <SelectItem value="Domestic">Domestic</SelectItem>
                            <SelectItem value="International">International</SelectItem>
                          </SelectContent>
                        </Select>
                      )}
                    />
                  </div>
                </div>

                {/* Conditional GST/PAN/VAT fields */}
                {watchDomesticIntl === 'Domestic' && (
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4 p-4 bg-blue-50 rounded-lg">
                    <div>
                      <Label htmlFor="gst_number">GST Number</Label>
                      <Input
                        {...form.register('gst_number')}
                        id="gst_number"
                        placeholder="Enter GST Number"
                        maxLength="15"
                      />
                    </div>
                    <div>
                      <Label htmlFor="pan_number">PAN Number</Label>
                      <Input
                        {...form.register('pan_number')}
                        id="pan_number"
                        placeholder="Enter PAN Number"
                        maxLength="10"
                      />
                    </div>
                  </div>
                )}

                {watchDomesticIntl === 'International' && (
                  <div className="p-4 bg-green-50 rounded-lg">
                    <div>
                      <Label htmlFor="vat_number">VAT Number</Label>
                      <Input
                        {...form.register('vat_number')}
                        id="vat_number"
                        placeholder="Enter VAT Number"
                        maxLength="20"
                      />
                    </div>
                  </div>
                )}

                {/* Master Data Dropdowns */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <Label htmlFor="company_type_id">Company Type *</Label>
                    <Controller
                      name="company_type_id"
                      control={form.control}
                      render={({ field }) => (
                        <Select onValueChange={field.onChange} value={field.value}>
                          <SelectTrigger>
                            <SelectValue placeholder="Select company type" />
                          </SelectTrigger>
                          <SelectContent>
                            {masterData['company-types']?.map((type) => (
                              <SelectItem key={type.id} value={type.id}>
                                {type.name}
                              </SelectItem>
                            ))}
                          </SelectContent>
                        </Select>
                      )}
                    />
                    {form.formState.errors.company_type_id && (
                      <p className="text-red-500 text-sm mt-1">{form.formState.errors.company_type_id.message}</p>
                    )}
                  </div>

                  <div>
                    <Label htmlFor="account_type_id">Account Type *</Label>
                    <Controller
                      name="account_type_id"
                      control={form.control}
                      render={({ field }) => (
                        <Select onValueChange={field.onChange} value={field.value}>
                          <SelectTrigger>
                            <SelectValue placeholder="Select account type" />
                          </SelectTrigger>
                          <SelectContent>
                            {masterData['account-types']?.map((type) => (
                              <SelectItem key={type.id} value={type.id}>
                                {type.name}
                              </SelectItem>
                            ))}
                          </SelectContent>
                        </Select>
                      )}
                    />
                    {form.formState.errors.account_type_id && (
                      <p className="text-red-500 text-sm mt-1">{form.formState.errors.account_type_id.message}</p>
                    )}
                  </div>

                  <div>
                    <Label htmlFor="region_id">Region *</Label>
                    <Controller
                      name="region_id"
                      control={form.control}
                      render={({ field }) => (
                        <Select onValueChange={field.onChange} value={field.value}>
                          <SelectTrigger>
                            <SelectValue placeholder="Select region" />
                          </SelectTrigger>
                          <SelectContent>
                            {masterData.regions?.map((region) => (
                              <SelectItem key={region.id} value={region.id}>
                                {region.name}
                              </SelectItem>
                            ))}
                          </SelectContent>
                        </Select>
                      )}
                    />
                    {form.formState.errors.region_id && (
                      <p className="text-red-500 text-sm mt-1">{form.formState.errors.region_id.message}</p>
                    )}
                  </div>

                  <div>
                    <Label htmlFor="business_type_id">Business Type *</Label>
                    <Controller
                      name="business_type_id"
                      control={form.control}
                      render={({ field }) => (
                        <Select onValueChange={field.onChange} value={field.value}>
                          <SelectTrigger>
                            <SelectValue placeholder="Select business type" />
                          </SelectTrigger>
                          <SelectContent>
                            {masterData['business-types']?.map((type) => (
                              <SelectItem key={type.id} value={type.id}>
                                {type.name}
                              </SelectItem>
                            ))}
                          </SelectContent>
                        </Select>
                      )}
                    />
                    {form.formState.errors.business_type_id && (
                      <p className="text-red-500 text-sm mt-1">{form.formState.errors.business_type_id.message}</p>
                    )}
                  </div>

                  <div>
                    <Label htmlFor="industry_id">Industry *</Label>
                    <Controller
                      name="industry_id"
                      control={form.control}
                      render={({ field }) => (
                        <Select onValueChange={field.onChange} value={field.value}>
                          <SelectTrigger>
                            <SelectValue placeholder="Select industry" />
                          </SelectTrigger>
                          <SelectContent>
                            {masterData.industries?.map((industry) => (
                              <SelectItem key={industry.id} value={industry.id}>
                                {industry.name}
                              </SelectItem>
                            ))}
                          </SelectContent>
                        </Select>
                      )}
                    />
                    {form.formState.errors.industry_id && (
                      <p className="text-red-500 text-sm mt-1">{form.formState.errors.industry_id.message}</p>
                    )}
                  </div>

                  <div>
                    <Label htmlFor="sub_industry_id">Sub-Industry *</Label>
                    <Controller
                      name="sub_industry_id"
                      control={form.control}
                      render={({ field }) => (
                        <Select onValueChange={field.onChange} value={field.value}>
                          <SelectTrigger>
                            <SelectValue placeholder="Select sub-industry" />
                          </SelectTrigger>
                          <SelectContent>
                            {filteredData.subIndustries?.map((subIndustry) => (
                              <SelectItem key={subIndustry.id} value={subIndustry.id}>
                                {subIndustry.name}
                              </SelectItem>
                            ))}
                          </SelectContent>
                        </Select>
                      )}
                    />
                    {form.formState.errors.sub_industry_id && (
                      <p className="text-red-500 text-sm mt-1">{form.formState.errors.sub_industry_id.message}</p>
                    )}
                  </div>
                </div>

                {/* Website and other fields */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <Label htmlFor="website">Website</Label>
                    <Input
                      {...form.register('website')}
                      id="website"
                      type="url"
                      placeholder="https://example.com"
                    />
                    {form.formState.errors.website && (
                      <p className="text-red-500 text-sm mt-1">{form.formState.errors.website.message}</p>
                    )}
                  </div>

                  <div>
                    <Label htmlFor="employee_count">Employee Count *</Label>
                    <Input
                      {...form.register('employee_count', { valueAsNumber: true })}
                      id="employee_count"
                      type="number"
                      min="1"
                      placeholder="Enter employee count"
                    />
                    {form.formState.errors.employee_count && (
                      <p className="text-red-500 text-sm mt-1">{form.formState.errors.employee_count.message}</p>
                    )}
                  </div>
                </div>

                {/* Parent Company */}
                <div className="space-y-4">
                  <div className="flex items-center space-x-2">
                    <Controller
                      name="is_child"
                      control={form.control}
                      render={({ field }) => (
                        <Checkbox
                          id="is_child"
                          checked={field.value}
                          onCheckedChange={field.onChange}
                        />
                      )}
                    />
                    <Label htmlFor="is_child">Is this a child company?</Label>
                  </div>

                  {watchIsChild && (
                    <div>
                      <Label htmlFor="parent_company_id">Parent Company</Label>
                      <Controller
                        name="parent_company_id"
                        control={form.control}
                        render={({ field }) => (
                          <Select onValueChange={field.onChange} value={field.value}>
                            <SelectTrigger>
                              <SelectValue placeholder="Select parent company" />
                            </SelectTrigger>
                            <SelectContent>
                              {filteredData.parentCompanies?.map((company) => (
                                <SelectItem key={company.id} value={company.id}>
                                  {company.name}
                                </SelectItem>
                              ))}
                            </SelectContent>
                          </Select>
                        )}
                      />
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* Step 2: Location */}
            {currentStep === 2 && (
              <div className="space-y-4">
                <h3 className="text-lg font-semibold">Location Information</h3>
                
                <div>
                  <Label htmlFor="address">Address *</Label>
                  <Textarea
                    {...form.register('address')}
                    id="address"
                    placeholder="Enter complete address"
                    rows={3}
                    maxLength="500"
                  />
                  {form.formState.errors.address && (
                    <p className="text-red-500 text-sm mt-1">{form.formState.errors.address.message}</p>
                  )}
                </div>

                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div>
                    <Label htmlFor="country_id">Country *</Label>
                    <Controller
                      name="country_id"
                      control={form.control}
                      render={({ field }) => (
                        <Select onValueChange={field.onChange} value={field.value}>
                          <SelectTrigger>
                            <SelectValue placeholder="Select country" />
                          </SelectTrigger>
                          <SelectContent>
                            {masterData.countries?.map((country) => (
                              <SelectItem key={country.id} value={country.id}>
                                {country.name}
                              </SelectItem>
                            ))}
                          </SelectContent>
                        </Select>
                      )}
                    />
                    {form.formState.errors.country_id && (
                      <p className="text-red-500 text-sm mt-1">{form.formState.errors.country_id.message}</p>
                    )}
                  </div>

                  <div>
                    <Label htmlFor="state_id">State *</Label>
                    <Controller
                      name="state_id"
                      control={form.control}
                      render={({ field }) => (
                        <Select onValueChange={field.onChange} value={field.value}>
                          <SelectTrigger>
                            <SelectValue placeholder="Select state" />
                          </SelectTrigger>
                          <SelectContent>
                            {filteredData.states?.map((state) => (
                              <SelectItem key={state.id} value={state.id}>
                                {state.name}
                              </SelectItem>
                            ))}
                          </SelectContent>
                        </Select>
                      )}
                    />
                    {form.formState.errors.state_id && (
                      <p className="text-red-500 text-sm mt-1">{form.formState.errors.state_id.message}</p>
                    )}
                  </div>

                  <div>
                    <Label htmlFor="city_id">City *</Label>
                    <Controller
                      name="city_id"
                      control={form.control}
                      render={({ field }) => (
                        <Select onValueChange={field.onChange} value={field.value}>
                          <SelectTrigger>
                            <SelectValue placeholder="Select city" />
                          </SelectTrigger>
                          <SelectContent>
                            {filteredData.cities?.map((city) => (
                              <SelectItem key={city.id} value={city.id}>
                                {city.name}
                              </SelectItem>
                            ))}
                          </SelectContent>
                        </Select>
                      )}
                    />
                    {form.formState.errors.city_id && (
                      <p className="text-red-500 text-sm mt-1">{form.formState.errors.city_id.message}</p>
                    )}
                  </div>
                </div>
              </div>
            )}

            {/* Step 3: Financials */}
            {currentStep === 3 && (
              <div className="space-y-6">
                <h3 className="text-lg font-semibold">Financial Information</h3>
                
                {/* Annual Revenue */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <Label htmlFor="annual_revenue">Annual Revenue *</Label>
                    <Input
                      {...form.register('annual_revenue', { valueAsNumber: true })}
                      id="annual_revenue"
                      type="number"
                      min="0"
                      step="0.01"
                      placeholder="Enter annual revenue"
                    />
                    {form.formState.errors.annual_revenue && (
                      <p className="text-red-500 text-sm mt-1">{form.formState.errors.annual_revenue.message}</p>
                    )}
                  </div>

                  <div>
                    <Label htmlFor="revenue_currency">Currency *</Label>
                    <Controller
                      name="revenue_currency"
                      control={form.control}
                      render={({ field }) => (
                        <Select onValueChange={field.onChange} value={field.value}>
                          <SelectTrigger>
                            <SelectValue placeholder="Select currency" />
                          </SelectTrigger>
                          <SelectContent>
                            {masterData.currencies?.map((currency) => (
                              <SelectItem key={currency.id} value={currency.code}>
                                {currency.code} - {currency.name}
                              </SelectItem>
                            ))}
                          </SelectContent>
                        </Select>
                      )}
                    />
                    {form.formState.errors.revenue_currency && (
                      <p className="text-red-500 text-sm mt-1">{form.formState.errors.revenue_currency.message}</p>
                    )}
                  </div>
                </div>

                {/* Turnover */}
                <div>
                  <div className="flex justify-between items-center mb-4">
                    <Label>Turnover (Multi-year)</Label>
                    <Button
                      type="button"
                      variant="outline"
                      size="sm"
                      onClick={() => appendTurnover({ year: new Date().getFullYear(), revenue: 0, currency: 'INR' })}
                    >
                      <Plus className="h-4 w-4 mr-2" />
                      Add Turnover
                    </Button>
                  </div>

                  {turnoverFields.map((field, index) => (
                    <div key={field.id} className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-4 p-4 border rounded">
                      <div>
                        <Label>Year</Label>
                        <Input
                          {...form.register(`turnover.${index}.year`, { valueAsNumber: true })}
                          type="number"
                          min="2000"
                          max="2030"
                        />
                      </div>
                      <div>
                        <Label>Revenue</Label>
                        <Input
                          {...form.register(`turnover.${index}.revenue`, { valueAsNumber: true })}
                          type="number"
                          min="0"
                          step="0.01"
                        />
                      </div>
                      <div>
                        <Label>Currency</Label>
                        <Controller
                          name={`turnover.${index}.currency`}
                          control={form.control}
                          render={({ field }) => (
                            <Select onValueChange={field.onChange} value={field.value}>
                              <SelectTrigger>
                                <SelectValue placeholder="Currency" />
                              </SelectTrigger>
                              <SelectContent>
                                {masterData.currencies?.map((currency) => (
                                  <SelectItem key={currency.id} value={currency.code}>
                                    {currency.code}
                                  </SelectItem>
                                ))}
                              </SelectContent>
                            </Select>
                          )}
                        />
                      </div>
                      <div className="flex items-end">
                        <Button
                          type="button"
                          variant="outline"
                          size="sm"
                          onClick={() => removeTurnover(index)}
                        >
                          <Trash2 className="h-4 w-4" />
                        </Button>
                      </div>
                    </div>
                  ))}
                </div>

                {/* Profit */}
                <div>
                  <div className="flex justify-between items-center mb-4">
                    <Label>Profit (Multi-year)</Label>
                    <Button
                      type="button"
                      variant="outline"
                      size="sm"
                      onClick={() => appendProfit({ year: new Date().getFullYear(), profit: 0, currency: 'INR' })}
                    >
                      <Plus className="h-4 w-4 mr-2" />
                      Add Profit
                    </Button>
                  </div>

                  {profitFields.map((field, index) => (
                    <div key={field.id} className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-4 p-4 border rounded">
                      <div>
                        <Label>Year</Label>
                        <Input
                          {...form.register(`profit.${index}.year`, { valueAsNumber: true })}
                          type="number"
                          min="2000"
                          max="2030"
                        />
                      </div>
                      <div>
                        <Label>Profit</Label>
                        <Input
                          {...form.register(`profit.${index}.profit`, { valueAsNumber: true })}
                          type="number"
                          step="0.01"
                        />
                      </div>
                      <div>
                        <Label>Currency</Label>
                        <Controller
                          name={`profit.${index}.currency`}
                          control={form.control}
                          render={({ field }) => (
                            <Select onValueChange={field.onChange} value={field.value}>
                              <SelectTrigger>
                                <SelectValue placeholder="Currency" />
                              </SelectTrigger>
                              <SelectContent>
                                {masterData.currencies?.map((currency) => (
                                  <SelectItem key={currency.id} value={currency.code}>
                                    {currency.code}
                                  </SelectItem>
                                ))}
                              </SelectContent>
                            </Select>
                          )}
                        />
                      </div>
                      <div className="flex items-end">
                        <Button
                          type="button"
                          variant="outline"
                          size="sm"
                          onClick={() => removeProfit(index)}
                        >
                          <Trash2 className="h-4 w-4" />
                        </Button>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Step 4: Documents & Profile */}
            {currentStep === 4 && (
              <div className="space-y-6">
                <h3 className="text-lg font-semibold">Documents & Company Profile</h3>
                
                {/* Company Profile */}
                <div>
                  <Label htmlFor="company_profile">Company Profile</Label>
                  <Textarea
                    {...form.register('company_profile')}
                    id="company_profile"
                    placeholder="Enter company profile and description"
                    rows={6}
                  />
                </div>

                {/* Document Upload */}
                <div>
                  <Label>Upload Documents</Label>
                  <div className="mt-2">
                    <div className="flex items-center justify-center w-full">
                      <label htmlFor="document-upload" className="flex flex-col items-center justify-center w-full h-32 border-2 border-gray-300 border-dashed rounded-lg cursor-pointer bg-gray-50 hover:bg-gray-100">
                        <div className="flex flex-col items-center justify-center pt-5 pb-6">
                          <Upload className="w-10 h-10 mb-3 text-gray-400" />
                          <p className="mb-2 text-sm text-gray-500">
                            <span className="font-semibold">Click to upload</span> documents
                          </p>
                          <p className="text-xs text-gray-500">PDF, DOCX, PNG, JPG (Max 10MB)</p>
                        </div>
                        <input
                          id="document-upload"
                          type="file"
                          className="hidden"
                          onChange={handleFileUpload}
                          accept=".pdf,.docx,.png,.jpg,.jpeg"
                        />
                      </label>
                    </div>
                  </div>

                  {/* Uploaded Documents */}
                  {uploadedDocuments.length > 0 && (
                    <div className="mt-4">
                      <h4 className="font-medium mb-2">Uploaded Documents:</h4>
                      <div className="space-y-2">
                        {uploadedDocuments.map((doc, index) => (
                          <div key={index} className="flex items-center justify-between p-3 bg-gray-50 rounded">
                            <div className="flex items-center">
                              <div className="mr-3">
                                {doc.mime_type?.includes('pdf') && '📄'}
                                {doc.mime_type?.includes('image') && '🖼️'}
                                {doc.mime_type?.includes('document') && '📝'}
                              </div>
                              <div>
                                <p className="font-medium">{doc.original_filename}</p>
                                <p className="text-sm text-gray-500">
                                  {(doc.file_size / 1024 / 1024).toFixed(2)} MB
                                </p>
                              </div>
                            </div>
                            <Button
                              type="button"
                              variant="outline"
                              size="sm"
                              onClick={() => removeDocument(index)}
                            >
                              <Trash2 className="h-4 w-4" />
                            </Button>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* Step 5: Checklist & Submit */}
            {currentStep === 5 && (
              <div className="space-y-6">
                <h3 className="text-lg font-semibold">Review & Submit</h3>
                
                {/* Checklist */}
                <div className="space-y-4 p-4 bg-gray-50 rounded-lg">
                  <h4 className="font-medium">Pre-submission Checklist</h4>
                  
                  <div className="space-y-3">
                    <div className="flex items-center space-x-2">
                      <Controller
                        name="valid_gst"
                        control={form.control}
                        render={({ field }) => (
                          <Checkbox
                            id="valid_gst"
                            checked={field.value}
                            onCheckedChange={field.onChange}
                          />
                        )}
                      />
                      <Label htmlFor="valid_gst">Valid GST number verified</Label>
                    </div>

                    <div className="flex items-center space-x-2">
                      <Controller
                        name="active_status"
                        control={form.control}
                        render={({ field }) => (
                          <Checkbox
                            id="active_status"
                            checked={field.value}
                            onCheckedChange={field.onChange}
                          />
                        )}
                      />
                      <Label htmlFor="active_status">Company is active and operational</Label>
                    </div>

                    {watchIsChild && (
                      <div className="flex items-center space-x-2">
                        <Controller
                          name="parent_linkage_valid"
                          control={form.control}
                          render={({ field }) => (
                            <Checkbox
                              id="parent_linkage_valid"
                              checked={field.value}
                              onCheckedChange={field.onChange}
                            />
                          )}
                        />
                        <Label htmlFor="parent_linkage_valid">Parent company linkage verified</Label>
                      </div>
                    )}
                  </div>
                </div>

                {/* Summary */}
                <div className="p-4 bg-blue-50 rounded-lg">
                  <h4 className="font-medium mb-2">Registration Summary</h4>
                  <div className="text-sm space-y-1">
                    <p><span className="font-medium">Company:</span> {form.watch('company_name')}</p>
                    <p><span className="font-medium">Type:</span> {form.watch('domestic_international')}</p>
                    <p><span className="font-medium">Employee Count:</span> {form.watch('employee_count')}</p>
                    <p><span className="font-medium">Annual Revenue:</span> {form.watch('annual_revenue')} {form.watch('revenue_currency')}</p>
                    <p><span className="font-medium">Documents:</span> {uploadedDocuments.length} uploaded</p>
                  </div>
                </div>
              </div>
            )}

            {/* Navigation Buttons */}
            <div className="flex justify-between pt-6">
              <Button
                type="button"
                variant="outline"
                onClick={prevStep}
                disabled={currentStep === 1}
              >
                Previous
              </Button>

              {currentStep < 5 ? (
                <Button type="button" onClick={nextStep}>
                  Next
                </Button>
              ) : (
                <Button type="submit" disabled={isLoading}>
                  {isLoading ? 'Submitting...' : 'Submit Registration'}
                </Button>
              )}
            </div>
          </form>
        </CardContent>
      </Card>
    </div>
  );
};

export default CompanyRegistration;