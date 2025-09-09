import React, { useState, useEffect } from 'react';
import { useForm, Controller } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import * as z from 'zod';
import axios from 'axios';
import { useNavigate, useParams } from 'react-router-dom';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Label } from './ui/label';
import { Textarea } from './ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './ui/select';
import { Badge } from './ui/badge';
import { Alert, AlertCircle, AlertDescription } from './ui/alert';
import { Checkbox } from './ui/checkbox';
import { Progress } from './ui/progress';
import { Separator } from './ui/separator';
import { toast } from 'sonner';
import { 
  ArrowLeft, 
  ArrowRight, 
  Upload, 
  FileText, 
  CheckCircle2, 
  AlertTriangle,
  User,
  Building,
  Target,
  FileCheck
} from 'lucide-react';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Validation schemas for each step
const step1Schema = z.object({
  tender_type: z.enum(['Tender', 'Pre-Tender', 'Non-Tender'], {
    required_error: 'Tender type is required'
  }),
  billing_type: z.string().optional(),
  project_title: z.string()
    .min(2, 'Project title must be at least 2 characters')
    .max(200, 'Project title must be less than 200 characters'),
  company_id: z.string().min(1, 'Company selection is required'),
  state: z.string().min(1, 'State is required').max(100, 'State must be less than 100 characters'),
  sub_tender_type_id: z.string().optional(),
  partner_id: z.string().optional(),
}).refine((data) => {
  // If tender_type is Tender or Pre-Tender, billing_type is required
  if (data.tender_type === 'Tender' || data.tender_type === 'Pre-Tender') {
    return data.billing_type && data.billing_type.trim() !== '';
  }
  return true;
}, {
  message: 'Billing type is required for Tender and Pre-Tender types',
  path: ['billing_type'],
});

const step2Schema = z.object({
  lead_subtype: z.enum(['Direct', 'Referral'], {
    required_error: 'Lead subtype is required'
  }),
  source: z.string().optional(),
  product_service_id: z.string().optional(),
  expected_orc: z.coerce.number().min(0, 'Expected ORC must be non-negative').optional(),
  revenue: z.coerce.number().min(0, 'Revenue must be non-negative').optional(),
  competitors: z.string().optional(),
  lead_owner: z.string().min(1, 'Lead owner is required'),
});

const step3Schema = z.object({
  checklist_completed: z.boolean().refine((val) => val === true, {
    message: 'All checklist items must be completed'
  }),
});

const STEPS = [
  { id: 1, title: 'General Info', description: 'Basic lead information', icon: Building },
  { id: 2, title: 'Lead Details', description: 'Detailed lead data', icon: Target },
  { id: 3, title: 'Proofs & Checklist', description: 'Documentation and validation', icon: FileCheck },
];

export const LeadForm = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const isEdit = Boolean(id);
  
  // Form state
  const [currentStep, setCurrentStep] = useState(1);
  const [formData, setFormData] = useState({
    // Step 1 defaults
    tender_type: '',
    billing_type: '',
    project_title: '',
    company_id: '',
    state: '',
    sub_tender_type_id: 'none',
    partner_id: 'none',
    // Step 2 defaults
    lead_subtype: '',
    source: '',
    product_service_id: 'none',
    expected_orc: '',
    revenue: '',
    competitors: '',
    lead_owner: '',
  });
  const [loading, setLoading] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  
  // Master data
  const [companies, setCompanies] = useState([]);
  const [subTenderTypes, setSubTenderTypes] = useState([]);
  const [partners, setPartners] = useState([]);
  const [productServices, setProductServices] = useState([]);
  const [users, setUsers] = useState([]);
  
  // File uploads
  const [uploadedFiles, setUploadedFiles] = useState([]);
  const [uploadingFile, setUploadingFile] = useState(false);
  
  // Checklist items
  const [checklistItems, setChecklistItems] = useState([
    { id: 'project_feasibility', label: 'Project feasibility assessed', checked: false },
    { id: 'budget_approval', label: 'Budget approval obtained', checked: false },
    { id: 'stakeholder_alignment', label: 'Stakeholder alignment confirmed', checked: false },
    { id: 'technical_requirements', label: 'Technical requirements documented', checked: false },
    { id: 'legal_compliance', label: 'Legal compliance verified', checked: false },
  ]);

  // Form setup for current step
  const getCurrentSchema = () => {
    switch (currentStep) {
      case 1: return step1Schema;
      case 2: return step2Schema;
      case 3: return step3Schema;
      default: return step1Schema;
    }
  };

  const form = useForm({
    resolver: zodResolver(getCurrentSchema()),
    defaultValues: formData,
    mode: 'onChange'
  });

  const { control, handleSubmit, formState: { errors }, watch, setValue, reset } = form;
  const watchedValues = watch();

  // Load master data
  useEffect(() => {
    loadMasterData();
    if (isEdit) {
      loadLeadData();
    }
  }, [id, isEdit]);

  // Update form when step changes
  useEffect(() => {
    const newSchema = getCurrentSchema();
    form.resolver = zodResolver(newSchema);
    
    // Use proper default values for the form
    const defaultValues = {
      ...formData,
      billing_type: formData.billing_type || '',
      sub_tender_type_id: formData.sub_tender_type_id || 'none',
      partner_id: formData.partner_id || 'none',
      product_service_id: formData.product_service_id || 'none',
    };
    
    reset(defaultValues);
  }, [currentStep]);

  // Auto-save functionality
  useEffect(() => {
    const timer = setTimeout(() => {
      const currentData = { ...formData, ...watchedValues };
      localStorage.setItem('leadFormData', JSON.stringify(currentData));
      setFormData(currentData);
    }, 1000);

    return () => clearTimeout(timer);
  }, [watchedValues]);

  const loadMasterData = async () => {
    try {
      setLoading(true);
      const [companiesRes, subTenderRes, partnersRes, productServicesRes, usersRes] = await Promise.all([
        axios.get(`${API}/companies`),
        axios.get(`${API}/sub-tender-types`),
        axios.get(`${API}/partners`),
        axios.get(`${API}/product-services`),
        axios.get(`${API}/users`),
      ]);
      
      setCompanies(companiesRes.data || []);
      setSubTenderTypes(subTenderRes.data || []);
      setPartners(partnersRes.data || []);
      setProductServices(productServicesRes.data || []);
      setUsers(usersRes.data || []);
    } catch (err) {
      console.error('Failed to load master data:', err);
      toast.error('Failed to load form data');
    } finally {
      setLoading(false);
    }
  };

  const loadLeadData = async () => {
    try {
      const response = await axios.get(`${API}/leads/${id}`);
      const leadData = response.data;
      setFormData(leadData);
      reset(leadData);
      
      // Load uploaded files if any
      if (leadData.proofs) {
        setUploadedFiles(leadData.proofs);
      }
    } catch (err) {
      console.error('Failed to load lead data:', err);
      toast.error('Failed to load lead data');
      navigate('/leads');
    }
  };

  const generateLeadId = () => {
    const chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789';
    let result = 'LEAD-';
    for (let i = 0; i < 7; i++) {
      result += chars.charAt(Math.floor(Math.random() * chars.length));
    }
    return result;
  };

  const handleNext = async (data) => {
    console.log('Form step data:', data);
    console.log('Current step:', currentStep);
    console.log('Form errors:', errors);
    
    const updatedData = { ...formData, ...data };
    setFormData(updatedData);
    
    if (currentStep < 3) {
      setCurrentStep(currentStep + 1);
    } else {
      console.log('Attempting final submission with data:', updatedData);
      console.log('Checklist completed:', checklistItems.every(item => item.checked));
      console.log('Checklist items:', checklistItems);
      await handleFinalSubmit(updatedData);
    }
  };

  const handlePrevious = () => {
    if (currentStep > 1) {
      setCurrentStep(currentStep - 1);
    }
  };

  const handleFinalSubmit = async (finalData) => {
    try {
      console.log('Starting final submission...');
      setSubmitting(true);
      
      const submitData = {
        ...finalData,
        checklist_completed: checklistItems.every(item => item.checked),
      };
      
      console.log('Submit data before processing:', submitData);
      
      // Convert "none" values to null/undefined for optional fields
      if (submitData.sub_tender_type_id === "none") {
        submitData.sub_tender_type_id = null;
      }
      if (submitData.partner_id === "none") {
        submitData.partner_id = null;
      }
      if (submitData.product_service_id === "none") {
        submitData.product_service_id = null;
      }
      
      if (!isEdit) {
        submitData.lead_id = generateLeadId();
      }
      
      console.log('Final submit data:', submitData);
      
      const url = isEdit ? `${API}/leads/${id}` : `${API}/leads`;
      const method = isEdit ? 'put' : 'post';
      
      console.log(`Making ${method.toUpperCase()} request to:`, url);
      
      const token = localStorage.getItem('token');
      const response = await axios[method](url, submitData, {
        headers: { Authorization: `Bearer ${token}` }
      });
      console.log('API response:', response.data);
      
      // Clear localStorage
      localStorage.removeItem('leadFormData');
      
      toast.success(`Lead ${isEdit ? 'updated' : 'created'} successfully`);
      navigate('/leads');
      
    } catch (err) {
      console.error('Submit error details:', err);
      console.error('Error response:', err.response?.data);
      const errorMsg = err.response?.data?.detail || `Failed to ${isEdit ? 'update' : 'create'} lead`;
      toast.error(errorMsg);
    } finally {
      setSubmitting(false);
    }
  };

  const handleFileUpload = async (event) => {
    const files = Array.from(event.target.files);
    if (!files.length) return;

    setUploadingFile(true);
    
    try {
      for (const file of files) {
        const formData = new FormData();
        formData.append('file', file);
        
        const response = await axios.post(`${API}/leads/upload-proof`, formData, {
          headers: { 'Content-Type': 'multipart/form-data' }
        });
        
        setUploadedFiles(prev => [...prev, response.data]);
      }
      
      toast.success('Files uploaded successfully');
    } catch (err) {
      toast.error('Failed to upload files');
      console.error('Upload error:', err);
    } finally {
      setUploadingFile(false);
    }
  };

  const handleChecklistChange = (itemId, checked) => {
    setChecklistItems(prev => 
      prev.map(item => 
        item.id === itemId ? { ...item, checked } : item
      )
    );
  };

  const renderStep1 = () => (
    <div className="space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="space-y-2">
          <Label htmlFor="tender_type">Tender Type *</Label>
          <Controller
            name="tender_type"
            control={control}
            render={({ field }) => (
              <Select onValueChange={field.onChange} value={field.value}>
                <SelectTrigger className={errors.tender_type ? 'border-red-500' : ''}>
                  <SelectValue placeholder="Select tender type" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="Tender">Tender</SelectItem>
                  <SelectItem value="Pre-Tender">Pre-Tender</SelectItem>
                  <SelectItem value="Non-Tender">Non-Tender</SelectItem>
                </SelectContent>
              </Select>
            )}
          />
          {errors.tender_type && (
            <p className="text-sm text-red-600">{errors.tender_type.message}</p>
          )}
        </div>

        {/* Conditional Billing Type - only show for Tender or Pre-Tender */}
        {(watchedValues.tender_type === 'Tender' || watchedValues.tender_type === 'Pre-Tender') && (
          <div className="space-y-2">
            <Label htmlFor="billing_type">Billing Type *</Label>
            <Controller
              name="billing_type"
              control={control}
              render={({ field }) => (
                <Select onValueChange={field.onChange} value={field.value || ''}>
                  <SelectTrigger className={errors.billing_type ? 'border-red-500' : ''}>
                    <SelectValue placeholder="Select billing type" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="prepaid">Prepaid</SelectItem>
                    <SelectItem value="postpaid">Postpaid</SelectItem>
                  </SelectContent>
                </Select>
              )}
            />
            {errors.billing_type && (
              <p className="text-sm text-red-600">{errors.billing_type.message}</p>
            )}
          </div>
        )}

        <div className="space-y-2">
          <Label htmlFor="sub_tender_type_id">Sub-Tender Type</Label>
          <Controller
            name="sub_tender_type_id"
            control={control}
            render={({ field }) => (
              <Select onValueChange={field.onChange} value={field.value || 'none'}>
                <SelectTrigger>
                  <SelectValue placeholder="Select sub-tender type (optional)" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="none">None</SelectItem>
                  {subTenderTypes.map(type => (
                    <SelectItem key={type.id} value={type.id}>{type.name}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            )}
          />
        </div>
      </div>

      <div className="space-y-2">
        <Label htmlFor="project_title">Project Title *</Label>
        <Controller
          name="project_title"
          control={control}
          render={({ field }) => (
            <Input
              {...field}
              placeholder="Enter project title"
              className={errors.project_title ? 'border-red-500' : ''}
            />
          )}
        />
        {errors.project_title && (
          <p className="text-sm text-red-600">{errors.project_title.message}</p>
        )}
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="space-y-2">
          <Label htmlFor="company_id">Company *</Label>
          <Controller
            name="company_id"
            control={control}
            render={({ field }) => (
              <Select onValueChange={field.onChange} value={field.value}>
                <SelectTrigger className={errors.company_id ? 'border-red-500' : ''}>
                  <SelectValue placeholder="Select company" />
                </SelectTrigger>
                <SelectContent>
                  {companies.map(company => (
                    <SelectItem key={company.id} value={company.id}>{company.name}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            )}
          />
          {errors.company_id && (
            <p className="text-sm text-red-600">{errors.company_id.message}</p>
          )}
        </div>

        <div className="space-y-2">
          <Label htmlFor="state">State *</Label>
          <Controller
            name="state"
            control={control}
            render={({ field }) => (
              <Input
                {...field}
                placeholder="Enter state"
                className={errors.state ? 'border-red-500' : ''}
              />
            )}
          />
          {errors.state && (
            <p className="text-sm text-red-600">{errors.state.message}</p>
          )}
        </div>
      </div>

      <div className="space-y-2">
        <Label htmlFor="partner_id">Partner</Label>
        <Controller
          name="partner_id"
          control={control}
          render={({ field }) => (
            <Select onValueChange={field.onChange} value={field.value || 'none'}>
              <SelectTrigger>
                <SelectValue placeholder="Select partner (optional)" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="none">None</SelectItem>
                {partners.map(partner => (
                  <SelectItem key={partner.id} value={partner.id}>{partner.name}</SelectItem>
                ))}
              </SelectContent>
            </Select>
          )}
        />
      </div>
    </div>
  );

  const renderStep2 = () => (
    <div className="space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="space-y-2">
          <Label htmlFor="lead_subtype">Lead Subtype *</Label>
          <Controller
            name="lead_subtype"
            control={control}
            render={({ field }) => (
              <Select onValueChange={field.onChange} value={field.value}>
                <SelectTrigger className={errors.lead_subtype ? 'border-red-500' : ''}>
                  <SelectValue placeholder="Select lead subtype" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="Direct">Direct</SelectItem>
                  <SelectItem value="Referral">Referral</SelectItem>
                </SelectContent>
              </Select>
            )}
          />
          {errors.lead_subtype && (
            <p className="text-sm text-red-600">{errors.lead_subtype.message}</p>
          )}
        </div>

        <div className="space-y-2">
          <Label htmlFor="source">Source</Label>
          <Controller
            name="source"
            control={control}
            render={({ field }) => (
              <Input
                {...field}
                placeholder="Enter lead source (optional)"
                className={errors.source ? 'border-red-500' : ''}
              />
            )}
          />
          {errors.source && (
            <p className="text-sm text-red-600">{errors.source.message}</p>
          )}
        </div>
      </div>

      <div className="space-y-2">
        <Label htmlFor="product_service_id">Product/Service</Label>
        <Controller
          name="product_service_id"
          control={control}
          render={({ field }) => (
            <Select onValueChange={field.onChange} value={field.value || 'none'}>
              <SelectTrigger>
                <SelectValue placeholder="Select product/service (optional)" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="none">None</SelectItem>
                {productServices.map(service => (
                  <SelectItem key={service.id} value={service.id}>{service.name}</SelectItem>
                ))}
              </SelectContent>
            </Select>
          )}
        />
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="space-y-2">
          <Label htmlFor="expected_orc">Expected ORC</Label>
          <Controller
            name="expected_orc"
            control={control}
            render={({ field }) => (
              <Input
                {...field}
                type="number"
                min="0"
                step="0.01"
                placeholder="Enter expected ORC (optional)"
                className={errors.expected_orc ? 'border-red-500' : ''}
              />
            )}
          />
          {errors.expected_orc && (
            <p className="text-sm text-red-600">{errors.expected_orc.message}</p>
          )}
        </div>

        <div className="space-y-2">
          <Label htmlFor="revenue">Expected Revenue</Label>
          <Controller
            name="revenue"
            control={control}
            render={({ field }) => (
              <Input
                {...field}
                type="number"
                min="0"
                step="0.01"
                placeholder="Enter expected revenue (optional)"
                className={errors.revenue ? 'border-red-500' : ''}
              />
            )}
          />
          {errors.revenue && (
            <p className="text-sm text-red-600">{errors.revenue.message}</p>
          )}
        </div>
      </div>

      <div className="space-y-2">
        <Label htmlFor="lead_owner">Lead Owner *</Label>
        <Controller
          name="lead_owner"
          control={control}
          render={({ field }) => (
            <Select onValueChange={field.onChange} value={field.value}>
              <SelectTrigger className={errors.lead_owner ? 'border-red-500' : ''}>
                <SelectValue placeholder="Select lead owner" />
              </SelectTrigger>
              <SelectContent>
                {users.map(user => (
                  <SelectItem key={user.id} value={user.id}>
                    {user.username} ({user.email})
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          )}
        />
        {errors.lead_owner && (
          <p className="text-sm text-red-600">{errors.lead_owner.message}</p>
        )}
      </div>

      <div className="space-y-2">
        <Label htmlFor="competitors">Competitors</Label>
        <Controller
          name="competitors"
          control={control}
          render={({ field }) => (
            <Textarea
              {...field}
              placeholder="Enter competitor information (optional)"
              rows={3}
              className={errors.competitors ? 'border-red-500' : ''}
            />
          )}
        />
        {errors.competitors && (
          <p className="text-sm text-red-600">{errors.competitors.message}</p>
        )}
      </div>
    </div>
  );

  const renderStep3 = () => (
    <div className="space-y-6">
      {/* File Upload Section */}
      <div className="space-y-4">
        <div className="flex items-center space-x-2">
          <Upload className="h-5 w-5" />
          <Label className="text-lg font-medium">Upload Proofs & Documents</Label>
        </div>
        
        <div className="border-2 border-dashed border-gray-200 rounded-lg p-6 text-center">
          <input
            type="file"
            multiple
            accept=".pdf,.doc,.docx,.jpg,.jpeg,.png"
            onChange={handleFileUpload}
            className="hidden"
            id="file-upload"
            disabled={uploadingFile}
          />
          <label htmlFor="file-upload" className="cursor-pointer">
            <div className="space-y-2">
              <Upload className="h-8 w-8 mx-auto text-gray-400" />
              <div className="text-sm text-gray-600">
                {uploadingFile ? 'Uploading...' : 'Click to upload files'}
              </div>
              <div className="text-xs text-gray-500">
                PDF, DOC, DOCX, JPG, JPEG, PNG up to 10MB each
              </div>
            </div>
          </label>
        </div>

        {uploadedFiles.length > 0 && (
          <div className="space-y-2">
            <Label className="font-medium">Uploaded Files:</Label>
            <div className="space-y-2">
              {uploadedFiles.map((file, index) => (
                <div key={index} className="flex items-center space-x-2 p-2 bg-gray-50 rounded">
                  <FileText className="h-4 w-4 text-blue-600" />
                  <span className="text-sm flex-1">{file.original_filename}</span>
                  <Badge variant="secondary" className="text-xs">
                    {Math.round(file.file_size / 1024)} KB
                  </Badge>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      <Separator />

      {/* Checklist Section */}
      <div className="space-y-4">
        <div className="flex items-center space-x-2">
          <CheckCircle2 className="h-5 w-5" />
          <Label className="text-lg font-medium">Lead Checklist</Label>
        </div>
        
        <Alert>
          <AlertTriangle className="h-4 w-4" />
          <AlertDescription>
            All checklist items must be completed before submitting the lead.
          </AlertDescription>
        </Alert>

        <div className="space-y-3">
          {checklistItems.map((item) => (
            <div key={item.id} className="flex items-center space-x-3 p-3 border rounded-lg">
              <Checkbox
                id={item.id}
                checked={item.checked}
                onCheckedChange={(checked) => handleChecklistChange(item.id, checked)}
              />
              <Label 
                htmlFor={item.id} 
                className={`flex-1 cursor-pointer ${item.checked ? 'line-through text-gray-500' : ''}`}
              >
                {item.label}
              </Label>
              {item.checked && <CheckCircle2 className="h-4 w-4 text-green-600" />}
            </div>
          ))}
        </div>

        {!checklistItems.every(item => item.checked) && (
          <Alert className="border-amber-200 bg-amber-50">
            <AlertTriangle className="h-4 w-4 text-amber-600" />
            <AlertDescription className="text-amber-800">
              <strong>Action Required:</strong> Please check all {checklistItems.filter(item => !item.checked).length} remaining checklist items to enable form submission.
            </AlertDescription>
          </Alert>
        )}
        
        {checklistItems.every(item => item.checked) && (
          <Alert className="border-green-200 bg-green-50">
            <CheckCircle2 className="h-4 w-4 text-green-600" />
            <AlertDescription className="text-green-800">
              <strong>Ready to Submit:</strong> All checklist items completed. You can now submit the lead.
            </AlertDescription>
          </Alert>
        )}
      </div>
    </div>
  );

  const getStepProgress = () => {
    return (currentStep / STEPS.length) * 100;
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-gray-900 mx-auto"></div>
          <p className="mt-2 text-gray-600">Loading form data...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto p-6 space-y-6">
      {/* Header */}
      <div className="space-y-4">
        <div className="flex items-center space-x-4">
          <Button
            variant="ghost"
            size="sm"
            onClick={() => navigate('/leads')}
            className="text-gray-600 hover:text-gray-800"
          >
            <ArrowLeft className="h-4 w-4 mr-2" />
            Back to Leads
          </Button>
        </div>
        
        <div>
          <h1 className="text-3xl font-bold text-gray-900">
            {isEdit ? 'Edit Lead' : 'Create New Lead'}
          </h1>
          <p className="text-gray-600 mt-1">
            {isEdit ? 'Update lead information' : 'Add a new lead to the system'}
          </p>
        </div>

        {/* Progress */}
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <span className="text-sm font-medium text-gray-700">
              Step {currentStep} of {STEPS.length}
            </span>
            <span className="text-sm text-gray-500">
              {Math.round(getStepProgress())}% Complete
            </span>
          </div>
          <Progress value={getStepProgress()} className="w-full" />
        </div>

        {/* Step Navigation */}
        <div className="flex items-center justify-between">
          {STEPS.map((step) => {
            const StepIcon = step.icon;
            const isActive = currentStep === step.id;
            const isCompleted = currentStep > step.id;
            
            return (
              <div key={step.id} className="flex flex-col items-center flex-1">
                <div className={`
                  w-10 h-10 rounded-full flex items-center justify-center border-2 mb-2
                  ${isActive ? 'border-blue-600 bg-blue-600 text-white' : 
                    isCompleted ? 'border-green-600 bg-green-600 text-white' : 
                    'border-gray-300 bg-white text-gray-400'}
                `}>
                  {isCompleted ? (
                    <CheckCircle2 className="h-5 w-5" />
                  ) : (
                    <StepIcon className="h-5 w-5" />
                  )}
                </div>
                <div className="text-center">
                  <div className={`text-sm font-medium ${
                    isActive ? 'text-blue-600' : isCompleted ? 'text-green-600' : 'text-gray-500'
                  }`}>
                    {step.title}
                  </div>
                  <div className="text-xs text-gray-500">{step.description}</div>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Form */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            {React.createElement(STEPS[currentStep - 1].icon, { className: "h-5 w-5" })}
            <span>{STEPS[currentStep - 1].title}</span>
          </CardTitle>
          <CardDescription>
            {STEPS[currentStep - 1].description}
          </CardDescription>
        </CardHeader>
        
        <CardContent>
          <form onSubmit={handleSubmit(handleNext)} className="space-y-6">
            {currentStep === 1 && renderStep1()}
            {currentStep === 2 && renderStep2()}
            {currentStep === 3 && renderStep3()}

            {/* Form Actions */}
            <Separator />
            <div className="flex justify-between">
              <Button
                type="button"
                variant="outline"
                onClick={handlePrevious}
                disabled={currentStep === 1}
              >
                <ArrowLeft className="h-4 w-4 mr-2" />
                Previous
              </Button>
              
              <Button
                type="submit"
                disabled={submitting || (currentStep === 3 && !checklistItems.every(item => item.checked))}
                className={
                  currentStep === 3 && !checklistItems.every(item => item.checked) 
                    ? 'opacity-50 cursor-not-allowed' 
                    : ''
                }
              >
                {submitting ? (
                  'Processing...'
                ) : currentStep === 3 ? (
                  !checklistItems.every(item => item.checked) 
                    ? 'Complete Checklist to Submit'
                    : `${isEdit ? 'Update' : 'Create'} Lead`
                ) : (
                  <>
                    Next
                    <ArrowRight className="h-4 w-4 ml-2" />
                  </>
                )}
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>
    </div>
  );
};

export default LeadForm;