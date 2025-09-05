import React, { useState, useEffect } from 'react';
import { useForm, Controller } from 'react-hook-form';
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
import { Progress } from './ui/progress';
import { Alert, AlertDescription } from './ui/alert';
import { AlertCircle, CheckCircle, Users, Phone, MapPin } from 'lucide-react';
import { toast } from 'sonner';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Contact form schema
const contactSchema = z.object({
  // Step 1: General Info
  company_id: z.string().min(1, 'Company is required'),
  salutation: z.enum(['Mr.', 'Ms.', 'Mrs.', 'Dr.', 'Prof.'], {invalid_type_error: 'Salutation is required'}),
  first_name: z.string().min(1, 'First name is required').max(50, 'First name must be less than 50 characters'),
  middle_name: z.string().max(50, 'Middle name must be less than 50 characters').optional(),
  last_name: z.string().max(50, 'Last name must be less than 50 characters').optional(),
  
  // Step 2: Contact Details
  email: z.string().email('Invalid email address'),
  primary_phone: z.string().min(10, 'Phone number must be at least 10 digits').max(15, 'Phone number must be less than 15 digits').regex(/^\+?[\d\s\-\(\)]{10,15}$/, 'Invalid phone number format'),
  designation_id: z.string().optional(),
  decision_maker: z.boolean().default(false),
  spoc: z.boolean().default(false),
  
  // Step 3: Additional Info
  address: z.string().max(500, 'Address must be less than 500 characters').optional(),
  country_id: z.string().optional(),
  city_id: z.string().optional(),
  comments: z.string().max(500, 'Comments must be less than 500 characters').optional(),
  option: z.string().max(100, 'Option must be less than 100 characters').optional()
});

const ContactForm = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const isEditing = !!id;
  
  const [currentStep, setCurrentStep] = useState(1);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState(false);
  const [spocWarning, setSpocWarning] = useState(null);
  
  // Master data
  const [masterData, setMasterData] = useState({});
  const [filteredCities, setFilteredCities] = useState([]);
  
  const form = useForm({
    resolver: zodResolver(contactSchema),
    defaultValues: {
      salutation: 'Mr.',
      decision_maker: false,
      spoc: false
    },
    mode: 'onChange'
  });

  // Load existing contact data or initialize form
  useEffect(() => {
    if (isEditing) {
      loadExistingContact();
    }
    fetchMasterData();
  }, [id]);

  const loadExistingContact = async () => {
    try {
      setIsLoading(true);
      const response = await axios.get(`${API}/contacts/${id}`);
      const contact = response.data;
      
      // Map contact data to form format
      const formData = {
        company_id: contact.company_id,
        salutation: contact.salutation,
        first_name: contact.first_name,
        middle_name: contact.middle_name || '',
        last_name: contact.last_name || '',
        email: contact.email,
        primary_phone: contact.primary_phone,
        designation_id: contact.designation_id || '',
        decision_maker: contact.decision_maker || false,
        spoc: contact.spoc || false,
        address: contact.address || '',
        country_id: contact.country_id || '',
        city_id: contact.city_id || '',
        comments: contact.comments || '',
        option: contact.option || ''
      };
      
      form.reset(formData);
      
    } catch (error) {
      toast.error('Failed to load contact data');
      navigate('/contacts');
    } finally {
      setIsLoading(false);
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
      toast.error('Failed to load master data');
      console.error('Master data fetch error:', error);
    }
  };

  // Watch for country changes to filter cities
  const watchCountry = form.watch('country_id');
  
  useEffect(() => {
    if (watchCountry && masterData.cities) {
      const filtered = masterData.cities.filter(city => city.country_id === watchCountry);
      setFilteredCities(filtered);
      form.setValue('city_id', ''); // Reset city selection
    }
  }, [watchCountry, masterData.cities]);

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
    
    setError('');
    return true;
  };

  const getStepFields = (step) => {
    switch (step) {
      case 1:
        return ['company_id', 'salutation', 'first_name'];
      case 2:
        return ['email', 'primary_phone', 'decision_maker', 'spoc'];
      case 3:
        return [];
      default:
        return [];
    }
  };

  const nextStep = async () => {
    if (await validateStep(currentStep)) {
      setCurrentStep(prev => Math.min(prev + 1, 3));
    }
  };

  const prevStep = () => {
    setCurrentStep(prev => Math.max(prev - 1, 1));
  };

  const handleSpocConfirmation = async (confirmUpdate = false) => {
    if (spocWarning && confirmUpdate) {
      // Proceed with SPOC update
      await submitContact(true);
      setSpocWarning(null);
    }
  };

  const submitContact = async (forceSPOCUpdate = false) => {
    setIsLoading(true);
    setError('');

    try {
      const formData = form.getValues();
      
      let response;
      if (isEditing) {
        const url = forceSPOCUpdate ? `${API}/contacts/${id}?force_spoc_update=true` : `${API}/contacts/${id}`;
        response = await axios.put(url, formData);
        toast.success('Contact updated successfully!');
      } else {
        response = await axios.post(`${API}/contacts`, formData);
        toast.success('Contact created successfully!');
      }
      
      setSuccess(true);
      
    } catch (error) {
      console.error('Contact submission error:', error);
      
      if (error.response?.status === 409 && error.response?.data?.requires_confirmation) {
        // SPOC conflict - show warning
        setSpocWarning({
          message: error.response.data.message,
          existingSpoc: error.response.data.existing_spoc
        });
      } else if (error.response?.status === 400 && error.response?.data?.detail?.includes('duplicate')) {
        setError('Possible duplicate contact detected. Review and confirm.');
      } else {
        const errorMsg = error.response?.data?.detail || `Failed to ${isEditing ? 'update' : 'create'} contact`;
        setError(errorMsg);
        toast.error(errorMsg);
      }
    } finally {
      setIsLoading(false);
    }
  };

  const onSubmit = async (data) => {
    if (!(await validateStep(currentStep))) return;
    await submitContact();
  };

  const getProgressPercentage = () => (currentStep / 3) * 100;

  const getCompanyName = (companyId) => {
    const company = masterData.companies?.find(c => c.id === companyId);
    return company?.name || 'Unknown Company';
  };

  const getDesignationName = (designationId) => {
    const designation = masterData.designations?.find(d => d.id === designationId);
    return designation?.name || 'Not specified';
  };

  if (success) {
    return (
      <div className="max-w-2xl mx-auto p-6">
        <Card>
          <CardContent className="pt-6 text-center">
            <CheckCircle className="h-16 w-16 text-green-500 mx-auto mb-4" />
            <h2 className="text-2xl font-bold text-green-700 mb-2">
              {isEditing ? 'Contact Updated!' : 'Contact Created!'}
            </h2>
            <p className="text-gray-600 mb-4">
              Contact has been {isEditing ? 'updated' : 'created'} successfully.
            </p>
            <div className="space-x-4">
              <Button onClick={() => navigate('/contacts')}>
                View Contacts
              </Button>
              {!isEditing && (
                <Button variant="outline" onClick={() => window.location.reload()}>
                  Add Another Contact
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
          <CardTitle className="flex items-center space-x-2">
            <Users className="h-5 w-5" />
            <span>{isEditing ? 'Edit Contact' : 'Add Contact'}</span>
          </CardTitle>
          <CardDescription>
            {isEditing ? 'Update contact information' : 'Add a new contact to the system'}
          </CardDescription>
          
          {/* Progress Bar */}
          <div className="mt-4">
            <div className="flex justify-between text-sm text-gray-600 mb-2">
              <span>Step {currentStep} of 3</span>
              <span>{Math.round(getProgressPercentage())}% Complete</span>
            </div>
            <Progress value={getProgressPercentage()} className="w-full" />
          </div>
          
          {/* Step Labels */}
          <div className="flex justify-between text-xs text-gray-500 mt-2">
            <span className={currentStep >= 1 ? 'text-blue-600 font-medium' : ''}>General Info</span>
            <span className={currentStep >= 2 ? 'text-blue-600 font-medium' : ''}>Contact Details</span>
            <span className={currentStep >= 3 ? 'text-blue-600 font-medium' : ''}>Additional Info</span>
          </div>
        </CardHeader>

        <CardContent>
          {error && (
            <Alert className="mb-6 border-red-200 bg-red-50">
              <AlertCircle className="h-4 w-4 text-red-600" />
              <AlertDescription className="text-red-800">{error}</AlertDescription>
            </Alert>
          )}

          {/* SPOC Warning Dialog */}
          {spocWarning && (
            <Alert className="mb-6 border-yellow-200 bg-yellow-50">
              <AlertCircle className="h-4 w-4 text-yellow-600" />
              <AlertDescription className="text-yellow-800">
                <div className="space-y-3">
                  <p className="font-semibold">{spocWarning.message}</p>
                  <p>
                    Current SPOC: {spocWarning.existingSpoc?.first_name} {spocWarning.existingSpoc?.last_name} 
                    ({spocWarning.existingSpoc?.email})
                  </p>
                  <div className="flex space-x-2">
                    <Button 
                      size="sm" 
                      onClick={() => handleSpocConfirmation(true)}
                      className="bg-yellow-600 hover:bg-yellow-700"
                    >
                      Confirm & Update
                    </Button>
                    <Button 
                      size="sm" 
                      variant="outline" 
                      onClick={() => setSpocWarning(null)}
                    >
                      Cancel
                    </Button>
                  </div>
                </div>
              </AlertDescription>
            </Alert>
          )}

          <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-6">
            {/* Step 1: General Info */}
            {currentStep === 1 && (
              <div className="space-y-4">
                <div className="flex items-center space-x-2 mb-4">
                  <Users className="h-5 w-5 text-blue-600" />
                  <h3 className="text-lg font-semibold">General Information</h3>
                </div>
                
                <div>
                  <Label htmlFor="company_id">Company *</Label>
                  <Controller
                    name="company_id"
                    control={form.control}
                    render={({ field }) => (
                      <Select onValueChange={field.onChange} value={field.value}>
                        <SelectTrigger>
                          <SelectValue placeholder="Select company" />
                        </SelectTrigger>
                        <SelectContent>
                          {masterData.companies?.map((company) => (
                            <SelectItem key={company.id} value={company.id}>
                              {company.name}
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    )}
                  />
                  {form.formState.errors.company_id && (
                    <p className="text-red-500 text-sm mt-1">{form.formState.errors.company_id.message}</p>
                  )}
                </div>

                <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                  <div>
                    <Label htmlFor="salutation">Salutation *</Label>
                    <Controller
                      name="salutation"
                      control={form.control}
                      render={({ field }) => (
                        <Select onValueChange={field.onChange} value={field.value}>
                          <SelectTrigger>
                            <SelectValue placeholder="Select salutation" />
                          </SelectTrigger>
                          <SelectContent>
                            <SelectItem value="Mr.">Mr.</SelectItem>
                            <SelectItem value="Ms.">Ms.</SelectItem>
                            <SelectItem value="Mrs.">Mrs.</SelectItem>
                            <SelectItem value="Dr.">Dr.</SelectItem>
                            <SelectItem value="Prof.">Prof.</SelectItem>
                          </SelectContent>
                        </Select>
                      )}
                    />
                    {form.formState.errors.salutation && (
                      <p className="text-red-500 text-sm mt-1">{form.formState.errors.salutation.message}</p>
                    )}
                  </div>

                  <div>
                    <Label htmlFor="first_name">First Name *</Label>
                    <Input
                      {...form.register('first_name')}
                      id="first_name"
                      placeholder="Enter first name"
                    />
                    {form.formState.errors.first_name && (
                      <p className="text-red-500 text-sm mt-1">{form.formState.errors.first_name.message}</p>
                    )}
                  </div>

                  <div>
                    <Label htmlFor="middle_name">Middle Name</Label>
                    <Input
                      {...form.register('middle_name')}
                      id="middle_name"
                      placeholder="Enter middle name"
                    />
                    {form.formState.errors.middle_name && (
                      <p className="text-red-500 text-sm mt-1">{form.formState.errors.middle_name.message}</p>
                    )}
                  </div>

                  <div>
                    <Label htmlFor="last_name">Last Name</Label>
                    <Input
                      {...form.register('last_name')}
                      id="last_name"
                      placeholder="Enter last name"
                    />
                    {form.formState.errors.last_name && (
                      <p className="text-red-500 text-sm mt-1">{form.formState.errors.last_name.message}</p>
                    )}
                  </div>
                </div>
              </div>
            )}

            {/* Step 2: Contact Details */}
            {currentStep === 2 && (
              <div className="space-y-4">
                <div className="flex items-center space-x-2 mb-4">
                  <Phone className="h-5 w-5 text-blue-600" />
                  <h3 className="text-lg font-semibold">Contact Details</h3>
                </div>
                
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <Label htmlFor="email">Email *</Label>
                    <Input
                      {...form.register('email')}
                      id="email"
                      type="email"
                      placeholder="Enter email address"
                    />
                    {form.formState.errors.email && (
                      <p className="text-red-500 text-sm mt-1">{form.formState.errors.email.message}</p>
                    )}
                  </div>

                  <div>
                    <Label htmlFor="primary_phone">Primary Phone *</Label>
                    <Input
                      {...form.register('primary_phone')}
                      id="primary_phone"
                      placeholder="Enter phone number"
                    />
                    {form.formState.errors.primary_phone && (
                      <p className="text-red-500 text-sm mt-1">{form.formState.errors.primary_phone.message}</p>
                    )}
                  </div>
                </div>

                <div>
                  <Label htmlFor="designation_id">Designation</Label>
                  <Controller
                    name="designation_id"
                    control={form.control}
                    render={({ field }) => (
                      <Select onValueChange={field.onChange} value={field.value}>
                        <SelectTrigger>
                          <SelectValue placeholder="Select designation" />
                        </SelectTrigger>
                        <SelectContent>
                          {masterData.designations?.map((designation) => (
                            <SelectItem key={designation.id} value={designation.id}>
                              {designation.name}
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    )}
                  />
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div className="flex items-center space-x-2">
                    <Controller
                      name="decision_maker"
                      control={form.control}
                      render={({ field }) => (
                        <Checkbox
                          id="decision_maker"
                          checked={field.value}
                          onCheckedChange={field.onChange}
                        />
                      )}
                    />
                    <Label htmlFor="decision_maker" className="text-sm font-medium">
                      Decision Maker
                    </Label>
                  </div>

                  <div className="flex items-center space-x-2">
                    <Controller
                      name="spoc"
                      control={form.control}
                      render={({ field }) => (
                        <Checkbox
                          id="spoc"
                          checked={field.value}
                          onCheckedChange={field.onChange}
                        />
                      )}
                    />
                    <Label htmlFor="spoc" className="text-sm font-medium">
                      Single Point of Contact (SPOC)
                    </Label>
                  </div>
                </div>
              </div>
            )}

            {/* Step 3: Additional Info */}
            {currentStep === 3 && (
              <div className="space-y-4">
                <div className="flex items-center space-x-2 mb-4">
                  <MapPin className="h-5 w-5 text-blue-600" />
                  <h3 className="text-lg font-semibold">Additional Information</h3>
                </div>
                
                <div>
                  <Label htmlFor="address">Address</Label>
                  <Textarea
                    {...form.register('address')}
                    id="address"
                    placeholder="Enter address"
                    rows={3}
                  />
                  {form.formState.errors.address && (
                    <p className="text-red-500 text-sm mt-1">{form.formState.errors.address.message}</p>
                  )}
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <Label htmlFor="country_id">Country</Label>
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
                  </div>

                  <div>
                    <Label htmlFor="city_id">City</Label>
                    <Controller
                      name="city_id"
                      control={form.control}
                      render={({ field }) => (
                        <Select onValueChange={field.onChange} value={field.value}>
                          <SelectTrigger>
                            <SelectValue placeholder="Select city" />
                          </SelectTrigger>
                          <SelectContent>
                            {filteredCities?.map((city) => (
                              <SelectItem key={city.id} value={city.id}>
                                {city.name}
                              </SelectItem>
                            ))}
                          </SelectContent>
                        </Select>
                      )}
                    />
                  </div>
                </div>

                <div>
                  <Label htmlFor="comments">Comments</Label>
                  <Textarea
                    {...form.register('comments')}
                    id="comments"
                    placeholder="Additional comments or notes"
                    rows={3}
                  />
                  {form.formState.errors.comments && (
                    <p className="text-red-500 text-sm mt-1">{form.formState.errors.comments.message}</p>
                  )}
                </div>

                <div>
                  <Label htmlFor="option">Preferred Contact Method</Label>
                  <Controller
                    name="option"
                    control={form.control}
                    render={({ field }) => (
                      <Select onValueChange={field.onChange} value={field.value}>
                        <SelectTrigger>
                          <SelectValue placeholder="Select preferred contact method" />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="email">Email</SelectItem>
                          <SelectItem value="phone">Phone</SelectItem>
                          <SelectItem value="whatsapp">WhatsApp</SelectItem>
                          <SelectItem value="linkedin">LinkedIn</SelectItem>
                          <SelectItem value="any">Any method</SelectItem>
                        </SelectContent>
                      </Select>
                    )}
                  />
                </div>

                {/* Summary */}
                <div className="mt-6 p-4 bg-blue-50 rounded-lg">
                  <h4 className="font-medium mb-2">Contact Summary</h4>
                  <div className="text-sm space-y-1">
                    <p><span className="font-medium">Name:</span> {form.watch('salutation')} {form.watch('first_name')} {form.watch('last_name')}</p>
                    <p><span className="font-medium">Company:</span> {getCompanyName(form.watch('company_id'))}</p>
                    <p><span className="font-medium">Email:</span> {form.watch('email')}</p>
                    <p><span className="font-medium">Phone:</span> {form.watch('primary_phone')}</p>
                    <p><span className="font-medium">Designation:</span> {getDesignationName(form.watch('designation_id'))}</p>
                    {form.watch('decision_maker') && <p className="text-green-600">✓ Decision Maker</p>}
                    {form.watch('spoc') && <p className="text-blue-600">✓ Single Point of Contact</p>}
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

              {currentStep < 3 ? (
                <Button type="button" onClick={nextStep}>
                  Next
                </Button>
              ) : (
                <Button type="submit" disabled={isLoading}>
                  {isLoading ? (isEditing ? 'Updating...' : 'Creating...') : (isEditing ? 'Update Contact' : 'Create Contact')}
                </Button>
              )}
            </div>
          </form>
        </CardContent>
      </Card>
    </div>
  );
};

export default ContactForm;