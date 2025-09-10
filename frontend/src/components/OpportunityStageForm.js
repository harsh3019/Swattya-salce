import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Separator } from '@/components/ui/separator';
import { 
  ArrowLeft, 
  ArrowRight,
  Save, 
  FileText, 
  Target,
  CheckCircle,
  AlertCircle,
  Clock,
  Users,
  Building,
  DollarSign,
  Calendar,
  Upload,
  Download,
  Lock,
  Plus
} from 'lucide-react';
import { usePermissions } from '../contexts/PermissionContext';
import axios from 'axios';

const STAGES = [
  { number: 1, code: 'L1', name: 'Prospect', color: 'bg-slate-100 text-slate-800 border-slate-200' },
  { number: 2, code: 'L2', name: 'Qualification', color: 'bg-blue-100 text-blue-800 border-blue-200' },
  { number: 3, code: 'L3', name: 'Proposal', color: 'bg-indigo-100 text-indigo-800 border-indigo-200' },
  { number: 4, code: 'L4', name: 'Technical Qualification', color: 'bg-purple-100 text-purple-800 border-purple-200' },
  { number: 5, code: 'L5', name: 'Commercial Negotiation', color: 'bg-pink-100 text-pink-800 border-pink-200' },
  { number: 6, code: 'L6', name: 'Won', color: 'bg-green-100 text-green-800 border-green-200' },
  { number: 7, code: 'L7', name: 'Lost', color: 'bg-red-100 text-red-800 border-red-200' },
  { number: 8, code: 'L8', name: 'Dropped', color: 'bg-orange-100 text-orange-800 border-orange-200' }
];

const OpportunityStageForm = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const { permissions } = usePermissions();
  
  const [opportunity, setOpportunity] = useState(null);
  const [currentStage, setCurrentStage] = useState(1);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState(null);
  const [validationErrors, setValidationErrors] = useState([]);

  // Master data
  const [regions, setRegions] = useState([]);
  const [users, setUsers] = useState([]);
  const [quotations, setQuotations] = useState([]);
  const [competitors, setCompetitors] = useState([]);
  
  // File upload state
  const [uploadedDocuments, setUploadedDocuments] = useState([]);
  const [uploading, setUploading] = useState(false);

  // Form data for each stage
  const [stageData, setStageData] = useState({
    // L1 - Prospect
    region_id: '',
    product_interest: '',
    assigned_representatives: [],
    lead_owner_id: '',
    
    // L2 - Qualification
    scorecard: '',
    budget: '',
    authority: '',
    need: '',
    timeline: '',
    qualification_status: '',
    
    // L3 - Proposal/Bid
    proposal_documents: [],
    submission_date: '',
    internal_stakeholder_id: '',
    client_response: '',
    
    // L4 - Technical Qualification
    selected_quotation_id: '',
    
    // L5 - Commercial Negotiation
    updated_price: '',
    margin: '',
    cpc_overhead: '',
    po_number: '',
    po_date: '',
    po_file: '',
    
    // L6 - Won
    final_value: '',
    client_poc: '',
    delivery_team: [],
    kickoff_task: '',
    
    // L7 - Lost
    lost_reason: '',
    competitor_id: '',
    followup_reminder: '',
    internal_learning: '',
    
    // L8 - Dropped
    drop_reason: '',
    reminder_date: ''
  });

  const baseURL = process.env.REACT_APP_BACKEND_URL;

  useEffect(() => {
    if (id) {
      fetchOpportunity();
      fetchMasterData();
    }
  }, [id]);

  const fetchOpportunity = async () => {
    try {
      setLoading(true);
      const token = localStorage.getItem('token');
      const response = await axios.get(`${baseURL}/api/opportunities/${id}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      const oppData = response.data;
      setOpportunity(oppData);
      setCurrentStage(oppData.current_stage || 1);
      
      // Populate form data from opportunity
      setStageData(prevData => ({
        ...prevData,
        ...oppData
      }));
      
    } catch (error) {
      console.error('Error fetching opportunity:', error);
      setError('Failed to load opportunity data');
    } finally {
      setLoading(false);
    }
  };

  const fetchMasterData = async () => {
    try {
      const token = localStorage.getItem('token');
      const headers = { Authorization: `Bearer ${token}` };

      const [regionsRes, usersRes, quotationsRes, competitorsRes, documentsRes] = await Promise.all([
        axios.get(`${baseURL}/api/mst/regions`, { headers }),
        axios.get(`${baseURL}/api/users`, { headers }),
        axios.get(`${baseURL}/api/opportunities/${id}/quotations`, { headers }),
        axios.get(`${baseURL}/api/mst/competitors`, { headers }),
        axios.get(`${baseURL}/api/opportunities/${id}/documents`, { headers }).catch(() => ({ data: [] }))
      ]);

      setRegions(regionsRes.data || []);
      setUsers(usersRes.data || []);
      setQuotations(quotationsRes.data || []);
      setCompetitors(competitorsRes.data || []);
      setUploadedDocuments(documentsRes.data || []);
    } catch (error) {
      console.error('Error fetching master data:', error);
    }
  };

  const handleInputChange = (field, value) => {
    setStageData(prev => ({
      ...prev,
      [field]: value
    }));
    
    // Clear validation errors for this field
    setValidationErrors(prev => prev.filter(error => !error.includes(field)));
  };

  const handleFileUpload = async (files) => {
    if (!files || files.length === 0) return;
    
    setUploading(true);
    const token = localStorage.getItem('token');
    
    try {
      const uploadPromises = Array.from(files).map(async (file) => {
        const formData = new FormData();
        formData.append('file', file);
        formData.append('document_type', 'proposal');
        formData.append('description', 'Proposal document uploaded for L3 stage');
        
        const response = await axios.post(
          `${baseURL}/api/opportunities/${id}/upload-document`,
          formData,
          {
            headers: {
              'Authorization': `Bearer ${token}`,
              'Content-Type': 'multipart/form-data'
            }
          }
        );
        
        return response.data;
      });
      
      const uploadedFiles = await Promise.all(uploadPromises);
      setUploadedDocuments(prev => [...prev, ...uploadedFiles]);
      
      // Update proposal_documents in stageData
      const documentIds = uploadedFiles.map(doc => doc.id);
      handleInputChange('proposal_documents', [...(stageData.proposal_documents || []), ...documentIds]);
      
      alert(`Successfully uploaded ${uploadedFiles.length} document(s)!`);
    } catch (error) {
      console.error('Error uploading files:', error);
      alert('Error uploading files. Please try again.');
    } finally {
      setUploading(false);
    }
  };

  const handleDeleteDocument = async (documentId) => {
    if (!confirm('Are you sure you want to delete this document?')) return;
    
    try {
      const token = localStorage.getItem('token');
      await axios.delete(
        `${baseURL}/api/opportunities/${id}/documents/${documentId}`,
        { headers: { Authorization: `Bearer ${token}` } }
      );
      
      setUploadedDocuments(prev => prev.filter(doc => doc.id !== documentId));
      handleInputChange('proposal_documents', 
        (stageData.proposal_documents || []).filter(docId => docId !== documentId)
      );
      
      alert('Document deleted successfully!');
    } catch (error) {
      console.error('Error deleting document:', error);
      alert('Error deleting document. Please try again.');
    }
  };

  const validateCurrentStage = () => {
    const errors = [];
    
    switch (currentStage) {
      case 1: // L1 - Prospect
        if (!stageData.region_id) errors.push('Region is required');
        if (!stageData.product_interest) errors.push('Product Interest is required');
        if (!stageData.assigned_representatives.length) errors.push('At least one Assigned Representative is required');
        if (!stageData.lead_owner_id) errors.push('Lead Owner is required');
        break;
      
      case 2: // L2 - Qualification
        if (!stageData.scorecard) errors.push('Scorecard is required');
        if (!stageData.budget) errors.push('Budget is required');
        if (!stageData.authority) errors.push('Authority is required');
        if (!stageData.need) errors.push('Need is required');
        if (!stageData.timeline) errors.push('Timeline is required');
        if (!stageData.qualification_status) errors.push('Status is required');
        break;
      
      case 3: // L3 - Proposal/Bid
        if (!uploadedDocuments.length && !stageData.proposal_documents?.length) errors.push('Proposal Documents are required');
        if (!stageData.submission_date) errors.push('Submission Date is required');
        if (!stageData.internal_stakeholder_id) errors.push('Internal Stakeholder is required');
        break;
      
      case 4: // L4 - Technical Qualification
        if (!stageData.selected_quotation_id) errors.push('Selected Quotation is required');
        break;
      
      case 5: // L5 - Commercial Negotiation
        if (!stageData.updated_price) errors.push('Updated Price is required');
        if (!stageData.po_number) errors.push('PO Number is required');
        if (!stageData.po_date) errors.push('PO Date is required');
        break;
      
      case 6: // L6 - Won
        if (!stageData.final_value) errors.push('Final Value is required');
        if (!stageData.client_poc) errors.push('Client POC is required');
        if (!stageData.delivery_team.length) errors.push('Delivery Team is required');
        break;
      
      case 7: // L7 - Lost
        if (!stageData.lost_reason) errors.push('Lost Reason is required');
        break;
      
      case 8: // L8 - Dropped
        if (!stageData.drop_reason) errors.push('Drop Reason is required');
        break;
    }
    
    setValidationErrors(errors);
    return errors.length === 0;
  };

  const handleSaveDraft = async () => {
    try {
      setSaving(true);
      const token = localStorage.getItem('token');
      
      // Save current stage data without validation
      await axios.post(`${baseURL}/api/opportunities/${id}/change-stage`, {
        target_stage: currentStage,
        stage_data: stageData,
        notes: 'Draft save'
      }, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      alert('Draft saved successfully!');
    } catch (error) {
      console.error('Error saving draft:', error);
      alert('Error saving draft. Please try again.');
    } finally {
      setSaving(false);
    }
  };

  const handleSaveAndNext = async () => {
    if (!validateCurrentStage()) {
      return;
    }
    
    try {
      setSaving(true);
      const token = localStorage.getItem('token');
      
      const nextStage = currentStage + 1;
      
      await axios.post(`${baseURL}/api/opportunities/${id}/change-stage`, {
        target_stage: nextStage,
        stage_data: stageData,
        notes: `Advanced from ${STAGES[currentStage - 1].name} to ${STAGES[nextStage - 1].name}`
      }, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      setCurrentStage(nextStage);
      alert(`Successfully moved to ${STAGES[nextStage - 1].name}!`);
    } catch (error) {
      console.error('Error advancing stage:', error);
      if (error.response?.data?.validation_errors) {
        setValidationErrors(error.response.data.validation_errors);
      } else {
        alert('Error advancing stage. Please try again.');
      }
    } finally {
      setSaving(false);
    }
  };

  const handleBack = () => {
    if (currentStage > 1) {
      setCurrentStage(currentStage - 1);
    }
  };

  const isStageCompleted = (stageNumber) => {
    return opportunity?.current_stage > stageNumber;
  };

  const isStageActive = (stageNumber) => {
    return currentStage === stageNumber;
  };

  const isStageAccessible = (stageNumber) => {
    return stageNumber <= (opportunity?.current_stage || 1);
  };

  const isOpportunityLocked = () => {
    return opportunity?.is_locked || ['Won', 'Lost', 'Dropped'].includes(opportunity?.status);
  };

  const isStageNumberLocked = (stageNumber) => {
    return opportunity?.locked_stages?.includes(stageNumber) || isOpportunityLocked();
  };

  const formatCurrency = (amount) => {
    return `₹${Number(amount).toLocaleString('en-IN')}`;
  };

  const renderStageForm = () => {
    if (isStageNumberLocked(currentStage)) {
      return (
        <Card className="border-yellow-200 bg-yellow-50">
          <CardContent className="flex items-center justify-center p-12">
            <div className="text-center">
              <Lock className="w-12 h-12 text-yellow-600 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-yellow-900 mb-2">Stage Locked</h3>
              <p className="text-yellow-700">This stage is locked and cannot be modified.</p>
            </div>
          </CardContent>
        </Card>
      );
    }

    switch (currentStage) {
      case 1:
        return renderL1ProspectForm();
      case 2:
        return renderL2QualificationForm();
      case 3:
        return renderL3ProposalForm();
      case 4:
        return renderL4TechnicalForm();
      case 5:
        return renderL5NegotiationForm();
      case 6:
        return renderL6WonForm();
      case 7:
        return renderL7LostForm();
      case 8:
        return renderL8DroppedForm();
      default:
        return null;
    }
  };

  const renderL1ProspectForm = () => (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Target className="w-5 h-5" />
          L1 - Prospect
        </CardTitle>
        <CardDescription>Initial prospect identification and qualification</CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <Label htmlFor="region_id">Region *</Label>
            <Select value={stageData.region_id} onValueChange={(value) => handleInputChange('region_id', value)}>
              <SelectTrigger>
                <SelectValue placeholder="Select region" />
              </SelectTrigger>
              <SelectContent>
                {regions.map((region) => (
                  <SelectItem key={region.id} value={region.id}>
                    {region.region_name} ({region.region_code})
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <div>
            <Label htmlFor="lead_owner_id">Lead Owner *</Label>
            <Select value={stageData.lead_owner_id} onValueChange={(value) => handleInputChange('lead_owner_id', value)}>
              <SelectTrigger>
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
          </div>
        </div>

        <div>
          <Label htmlFor="product_interest">Product Interest *</Label>
          <Textarea
            id="product_interest"
            value={stageData.product_interest}
            onChange={(e) => handleInputChange('product_interest', e.target.value)}
            placeholder="Describe the customer's product interest..."
            rows={3}
          />
        </div>

        <div>
          <Label htmlFor="assigned_representatives">Assigned Representatives *</Label>
          <Select value="" onValueChange={(value) => {
            if (value && !stageData.assigned_representatives.includes(value)) {
              handleInputChange('assigned_representatives', [...stageData.assigned_representatives, value]);
            }
          }}>
            <SelectTrigger>
              <SelectValue placeholder="Add representatives" />
            </SelectTrigger>
            <SelectContent>
              {users.filter(user => !stageData.assigned_representatives.includes(user.id)).map((user) => (
                <SelectItem key={user.id} value={user.id}>
                  {user.username}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          
          <div className="flex flex-wrap gap-2 mt-2">
            {stageData.assigned_representatives.map((userId) => {
              const user = users.find(u => u.id === userId);
              return (
                <Badge key={userId} variant="secondary" className="cursor-pointer">
                  {user?.username}
                  <button
                    onClick={() => handleInputChange('assigned_representatives', 
                      stageData.assigned_representatives.filter(id => id !== userId)
                    )}
                    className="ml-2 text-red-600 hover:text-red-800"
                  >
                    ×
                  </button>
                </Badge>
              );
            })}
          </div>
        </div>
      </CardContent>
    </Card>
  );

  const renderL2QualificationForm = () => (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <CheckCircle className="w-5 h-5" />
          L2 - Qualification
        </CardTitle>
        <CardDescription>Detailed qualification using BANT/CHAMP methodology</CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <Label htmlFor="scorecard">Scorecard *</Label>
            <Select value={stageData.scorecard} onValueChange={(value) => handleInputChange('scorecard', value)}>
              <SelectTrigger>
                <SelectValue placeholder="Select scorecard" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="BANT">BANT</SelectItem>
                <SelectItem value="CHAMP">CHAMP</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <div>
            <Label htmlFor="qualification_status">Status *</Label>
            <Select value={stageData.qualification_status} onValueChange={(value) => handleInputChange('qualification_status', value)}>
              <SelectTrigger>
                <SelectValue placeholder="Select status" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="Qualified">Qualified</SelectItem>
                <SelectItem value="Not Now">Not Now</SelectItem>
                <SelectItem value="Disqualified">Disqualified</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <div>
            <Label htmlFor="budget">Budget *</Label>
            <Input
              id="budget"
              value={stageData.budget}
              onChange={(e) => handleInputChange('budget', e.target.value)}
              placeholder="Enter budget information"
            />
          </div>

          <div>
            <Label htmlFor="authority">Authority *</Label>
            <Input
              id="authority"
              value={stageData.authority}
              onChange={(e) => handleInputChange('authority', e.target.value)}
              placeholder="Decision maker details"
            />
          </div>

          <div>
            <Label htmlFor="need">Need *</Label>
            <Input
              id="need"
              value={stageData.need}
              onChange={(e) => handleInputChange('need', e.target.value)}
              placeholder="Customer need/pain point"
            />
          </div>

          <div>
            <Label htmlFor="timeline">Timeline *</Label>
            <Input
              id="timeline"
              value={stageData.timeline}
              onChange={(e) => handleInputChange('timeline', e.target.value)}
              placeholder="Expected timeline"
            />
          </div>
        </div>
      </CardContent>
    </Card>
  );

  const renderL3ProposalForm = () => (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <FileText className="w-5 h-5" />
          L3 - Proposal/Bid
        </CardTitle>
        <CardDescription>Proposal creation and submission</CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <Label htmlFor="submission_date">Submission Date *</Label>
            <Input
              id="submission_date"
              type="date"
              value={stageData.submission_date}
              onChange={(e) => handleInputChange('submission_date', e.target.value)}
            />
          </div>

          <div>
            <Label htmlFor="internal_stakeholder_id">Internal Stakeholder *</Label>
            <Select value={stageData.internal_stakeholder_id} onValueChange={(value) => handleInputChange('internal_stakeholder_id', value)}>
              <SelectTrigger>
                <SelectValue placeholder="Select stakeholder" />
              </SelectTrigger>
              <SelectContent>
                {users.map((user) => (
                  <SelectItem key={user.id} value={user.id}>
                    {user.username}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </div>

        <div>
          <Label htmlFor="proposal_documents">Proposal Documents *</Label>
          <div className="space-y-4">
            {/* File Upload Area */}
            <div className="border-2 border-dashed border-gray-300 rounded-lg p-6 text-center">
              <Upload className="w-8 h-8 text-gray-400 mx-auto mb-2" />
              <p className="text-gray-600">Upload proposal documents (PDF/DOC/DOCX/PNG/JPG)</p>
              <p className="text-sm text-gray-500 mb-2">Maximum file size: 10MB</p>
              <input
                type="file"
                id="document-upload"
                multiple
                accept=".pdf,.doc,.docx,.png,.jpg,.jpeg,.txt"
                onChange={(e) => handleFileUpload(e.target.files)}
                className="hidden"
                disabled={uploading}
              />
              <Button 
                variant="outline" 
                className="mt-2"
                onClick={() => document.getElementById('document-upload').click()}
                disabled={uploading}
              >
                {uploading ? 'Uploading...' : 'Choose Files'}
              </Button>
            </div>
            
            {/* Uploaded Documents List */}
            {uploadedDocuments.length > 0 && (
              <div>
                <Label className="text-sm font-medium text-gray-700">Uploaded Documents</Label>
                <div className="space-y-2 mt-2">
                  {uploadedDocuments.map((doc) => (
                    <div key={doc.id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                      <div className="flex items-center gap-3">
                        <FileText className="w-4 h-4 text-blue-600" />
                        <div>
                          <p className="text-sm font-medium text-gray-900">{doc.original_filename}</p>
                          <p className="text-xs text-gray-500">
                            {(doc.file_size / 1024).toFixed(1)} KB • {new Date(doc.uploaded_at).toLocaleDateString()}
                          </p>
                        </div>
                      </div>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => handleDeleteDocument(doc.id)}
                        className="text-red-600 hover:text-red-800"
                      >
                        ×
                      </Button>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>

        <div>
          <Label htmlFor="client_response">Client Response</Label>
          <Textarea
            id="client_response"
            value={stageData.client_response}
            onChange={(e) => handleInputChange('client_response', e.target.value)}
            placeholder="Client feedback or response (optional)"
            rows={3}
          />
        </div>
      </CardContent>
    </Card>
  );

  const renderL4TechnicalForm = () => (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <DollarSign className="w-5 h-5" />
          L4 - Technical Qualification
        </CardTitle>
        <CardDescription>Technical evaluation and quotation selection</CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div>
          <Label htmlFor="selected_quotation_id">Select Quotation *</Label>
          <Select value={stageData.selected_quotation_id} onValueChange={(value) => handleInputChange('selected_quotation_id', value)}>
            <SelectTrigger>
              <SelectValue placeholder="Choose quotation to proceed" />
            </SelectTrigger>
            <SelectContent>
              {quotations.map((quotation) => (
                <SelectItem key={quotation.id} value={quotation.id}>
                  {quotation.quotation_name} - {formatCurrency(quotation.grand_total)}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        {quotations.length > 0 && (
          <div>
            <Label>Available Quotations</Label>
            <div className="space-y-2 mt-2">
              {quotations.map((quotation) => (
                <div key={quotation.id} className="border rounded p-3 flex justify-between items-center">
                  <div>
                    <p className="font-medium">{quotation.quotation_name}</p>
                    <p className="text-sm text-gray-600">ID: {quotation.quotation_id}</p>
                  </div>
                  <div className="text-right">
                    <p className="font-semibold">{formatCurrency(quotation.grand_total)}</p>
                    <p className="text-sm text-green-600">{quotation.profitability_percent.toFixed(1)}% profit</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {quotations.length === 0 && (
          <div className="text-center py-6 text-gray-500">
            <FileText className="w-12 h-12 mx-auto mb-2 text-gray-400" />
            <p>No quotations created yet</p>
            <p className="text-sm mb-4">Create quotations to proceed with this stage</p>
            <Button 
              onClick={() => navigate(`/opportunities/${id}/quotations/create`)}
              className="bg-blue-600 hover:bg-blue-700"
            >
              <Plus className="w-4 h-4 mr-2" />
              Create Quotation
            </Button>
          </div>
        )}

        {quotations.length > 0 && (
          <div className="flex justify-center mt-4">
            <Button 
              variant="outline"
              onClick={() => navigate(`/opportunities/${id}/quotations/create`)}
              className="border-blue-200 text-blue-700 hover:bg-blue-50"
            >
              <Plus className="w-4 h-4 mr-2" />
              Add Another Quotation
            </Button>
          </div>
        )}
      </CardContent>
    </Card>
  );

  const renderL5NegotiationForm = () => (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <DollarSign className="w-5 h-5" />
          L5 - Commercial Negotiation
        </CardTitle>
        <CardDescription>Price negotiation and commercial terms</CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <Label htmlFor="updated_price">Updated Price *</Label>
            <Input
              id="updated_price"
              type="number"
              value={stageData.updated_price}
              onChange={(e) => handleInputChange('updated_price', e.target.value)}
              placeholder="Final negotiated price"
            />
          </div>

          <div>
            <Label htmlFor="margin">Margin (Auto-calculated)</Label>
            <Input
              id="margin"
              value={stageData.margin}
              disabled
              className="bg-gray-100"
            />
          </div>

          <div>
            <Label htmlFor="po_number">PO Number *</Label>
            <Input
              id="po_number"
              value={stageData.po_number}
              onChange={(e) => handleInputChange('po_number', e.target.value)}
              placeholder="Purchase Order number"
            />
          </div>

          <div>
            <Label htmlFor="po_date">PO Date *</Label>
            <Input
              id="po_date"
              type="date"
              value={stageData.po_date}
              onChange={(e) => handleInputChange('po_date', e.target.value)}
            />
          </div>
        </div>

        <div>
          <Label htmlFor="po_file">PO File (Optional)</Label>
          <div className="border-2 border-dashed border-gray-300 rounded-lg p-4 text-center">
            <Upload className="w-6 h-6 text-gray-400 mx-auto mb-2" />
            <p className="text-gray-600 text-sm">Upload Purchase Order document</p>
            <Button variant="outline" size="sm" className="mt-2">
              Choose File
            </Button>
          </div>
        </div>
      </CardContent>
    </Card>
  );

  const renderL6WonForm = () => (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <CheckCircle className="w-5 h-5 text-green-600" />
          L6 - Won
        </CardTitle>
        <CardDescription>Deal won and handover to delivery</CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <Label htmlFor="final_value">Final Value *</Label>
            <Input
              id="final_value"
              type="number"
              value={stageData.final_value}
              onChange={(e) => handleInputChange('final_value', e.target.value)}
              placeholder="Final contract value"
            />
          </div>

          <div>
            <Label htmlFor="client_poc">Client POC *</Label>
            <Input
              id="client_poc"
              value={stageData.client_poc}
              onChange={(e) => handleInputChange('client_poc', e.target.value)}
              placeholder="Client point of contact"
            />
          </div>
        </div>

        <div>
          <Label htmlFor="delivery_team">Delivery Team *</Label>
          <Select value="" onValueChange={(value) => {
            if (value && !stageData.delivery_team.includes(value)) {
              handleInputChange('delivery_team', [...stageData.delivery_team, value]);
            }
          }}>
            <SelectTrigger>
              <SelectValue placeholder="Add team members" />
            </SelectTrigger>
            <SelectContent>
              {users.filter(user => !stageData.delivery_team.includes(user.id)).map((user) => (
                <SelectItem key={user.id} value={user.id}>
                  {user.username}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          
          <div className="flex flex-wrap gap-2 mt-2">
            {stageData.delivery_team.map((userId) => {
              const user = users.find(u => u.id === userId);
              return (
                <Badge key={userId} variant="secondary" className="cursor-pointer">
                  {user?.username}
                  <button
                    onClick={() => handleInputChange('delivery_team', 
                      stageData.delivery_team.filter(id => id !== userId)
                    )}
                    className="ml-2 text-red-600 hover:text-red-800"
                  >
                    ×
                  </button>
                </Badge>
              );
            })}
          </div>
        </div>

        <div>
          <Label htmlFor="kickoff_task">Kickoff Task (Optional)</Label>
          <Textarea
            id="kickoff_task"
            value={stageData.kickoff_task}
            onChange={(e) => handleInputChange('kickoff_task', e.target.value)}
            placeholder="Project kickoff tasks and next steps"
            rows={3}
          />
        </div>
      </CardContent>
    </Card>
  );

  const renderL7LostForm = () => (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <AlertCircle className="w-5 h-5 text-red-600" />
          L7 - Lost
        </CardTitle>
        <CardDescription>Deal lost - capture learning and feedback</CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <Label htmlFor="competitor_id">Competitor (Optional)</Label>
            <Select value={stageData.competitor_id} onValueChange={(value) => handleInputChange('competitor_id', value)}>
              <SelectTrigger>
                <SelectValue placeholder="Select competitor" />
              </SelectTrigger>
              <SelectContent>
                {competitors.map((competitor) => (
                  <SelectItem key={competitor.id} value={competitor.id}>
                    {competitor.competitor_name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <div>
            <Label htmlFor="followup_reminder">Follow-up Reminder (Optional)</Label>
            <Input
              id="followup_reminder"
              type="date"
              value={stageData.followup_reminder}
              onChange={(e) => handleInputChange('followup_reminder', e.target.value)}
            />
          </div>
        </div>

        <div>
          <Label htmlFor="lost_reason">Lost Reason *</Label>
          <Textarea
            id="lost_reason"
            value={stageData.lost_reason}
            onChange={(e) => handleInputChange('lost_reason', e.target.value)}
            placeholder="Explain why the opportunity was lost..."
            rows={3}
          />
        </div>

        <div>
          <Label htmlFor="internal_learning">Internal Learning (Optional)</Label>
          <Textarea
            id="internal_learning"
            value={stageData.internal_learning}
            onChange={(e) => handleInputChange('internal_learning', e.target.value)}
            placeholder="Key learnings and improvements for future opportunities"
            rows={3}
          />
        </div>
      </CardContent>
    </Card>
  );

  const renderL8DroppedForm = () => (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <AlertCircle className="w-5 h-5 text-orange-600" />
          L8 - Dropped
        </CardTitle>
        <CardDescription>Opportunity dropped - no longer active</CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div>
          <Label htmlFor="reminder_date">Reminder Date (Optional)</Label>
          <Input
            id="reminder_date"
            type="date"
            value={stageData.reminder_date}
            onChange={(e) => handleInputChange('reminder_date', e.target.value)}
          />
        </div>

        <div>
          <Label htmlFor="drop_reason">Drop Reason *</Label>
          <Textarea
            id="drop_reason"
            value={stageData.drop_reason}
            onChange={(e) => handleInputChange('drop_reason', e.target.value)}
            placeholder="Explain why the opportunity was dropped..."
            rows={3}
          />
        </div>
      </CardContent>
    </Card>
  );

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
          <h2 className="text-2xl font-bold text-gray-900 mb-2">Error Loading Opportunity</h2>
          <p className="text-gray-600 mb-4">{error || 'Opportunity not found'}</p>
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
      </div>

      {/* Stage Progress Bar */}
      <Card className="border-blue-200 bg-blue-50">
        <CardHeader>
          <CardTitle className="text-lg">Pipeline Progress</CardTitle>
          <CardDescription>L1-L8 Sales Pipeline Stages</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <Progress value={(currentStage / 8) * 100} className="h-3" />
            
            <div className="flex flex-wrap gap-2">
              {STAGES.map((stage) => (
                <Badge
                  key={stage.number}
                  variant={isStageActive(stage.number) ? "default" : "outline"}
                  className={`cursor-pointer ${
                    isStageActive(stage.number)
                      ? 'bg-blue-600 text-white border-blue-600'
                      : isStageCompleted(stage.number)
                        ? 'bg-green-100 text-green-800 border-green-200'
                        : stage.color
                  } ${
                    isStageNumberLocked(stage.number) ? 'opacity-50' : ''
                  }`}
                  onClick={() => {
                    if (isStageAccessible(stage.number) && !isStageNumberLocked(stage.number)) {
                      setCurrentStage(stage.number);
                    }
                  }}
                >
                  {isStageCompleted(stage.number) && <CheckCircle className="w-3 h-3 mr-1" />}
                  {isStageNumberLocked(stage.number) && <Lock className="w-3 h-3 mr-1" />}
                  {stage.code}
                </Badge>
              ))}
            </div>
            
            <div className="text-sm text-gray-600">
              Currently in: <strong>{STAGES[currentStage - 1].name}</strong>
              {isOpportunityLocked() && (
                <span className="ml-2 text-red-600">• Opportunity Locked</span>
              )}
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Validation Errors */}
      {validationErrors.length > 0 && (
        <Card className="border-red-200 bg-red-50">
          <CardContent className="p-4">
            <div className="flex items-center gap-2 text-red-700">
              <AlertCircle className="w-4 h-4" />
              <p className="font-medium">Please fix the following issues:</p>
            </div>
            <ul className="list-disc list-inside mt-2 text-red-600 text-sm">
              {validationErrors.map((error, index) => (
                <li key={index}>{error}</li>
              ))}
            </ul>
          </CardContent>
        </Card>
      )}

      {/* Stage Form */}
      {renderStageForm()}

      {/* Action Buttons */}
      {!isStageNumberLocked(currentStage) && (
        <div className="flex justify-between">
          <Button
            variant="outline"
            onClick={handleBack}
            disabled={currentStage === 1}
          >
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back
          </Button>
          
          <div className="flex gap-2">
            <Button
              variant="outline"
              onClick={handleSaveDraft}
              disabled={saving}
            >
              <Save className="w-4 h-4 mr-2" />
              Save Draft
            </Button>
            
            {currentStage < 8 && (
              <Button
                onClick={handleSaveAndNext}
                disabled={saving}
                className="bg-blue-600 hover:bg-blue-700"
              >
                {saving ? 'Saving...' : 'Save & Next'}
                <ArrowRight className="w-4 h-4 ml-2" />
              </Button>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default OpportunityStageForm;