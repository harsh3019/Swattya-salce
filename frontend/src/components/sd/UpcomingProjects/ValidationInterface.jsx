import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import axios from 'axios';
import { Card, CardContent, CardHeader, CardTitle } from '../../ui/card';
import { Badge } from '../../ui/badge';
import { Button } from '../../ui/button';
import { Input } from '../../ui/input';
import { Textarea } from '../../ui/textarea';
import { Separator } from '../../ui/separator';
import { Progress } from '../../ui/progress';
import { Alert, AlertCircle, AlertTriangle, CheckCircle } from 'lucide-react';
import { 
  FileUp, 
  FileCheck, 
  AlertCircle as AlertCircleIcon, 
  CheckCircle as CheckCircleIcon,
  ArrowLeft,
  Upload,
  FileText,
  RefreshCcw,
  ArrowRight,
  X,
  ThumbsUp,
  ThumbsDown
} from 'lucide-react';

const baseURL = process.env.REACT_APP_BACKEND_URL || import.meta.env.REACT_APP_BACKEND_URL;

const ValidationInterface = () => {
  const { projectId } = useParams();
  const navigate = useNavigate();
  
  const [project, setProject] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [validating, setValidating] = useState(false);
  const [converting, setConverting] = useState(false);
  const [rejecting, setRejecting] = useState(false);
  
  // File states
  const [boqFile, setBoqFile] = useState(null);
  const [bomFile, setBomFile] = useState(null);
  const [uploadProgress, setUploadProgress] = useState(0);
  
  // Validation results
  const [validationResult, setValidationResult] = useState(null);
  
  // Rejection state
  const [rejectionReason, setRejectionReason] = useState('');
  const [showRejectionDialog, setShowRejectionDialog] = useState(false);

  useEffect(() => {
    fetchProject();
  }, [projectId]);

  const fetchProject = async () => {
    try {
      setLoading(true);
      const token = localStorage.getItem('token');
      
      const response = await axios.get(`${baseURL}/api/sd/upcoming-projects/${projectId}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      setProject(response.data);
      setError(null);
    } catch (error) {
      console.error('Error fetching project:', error);
      setError('Failed to fetch project details');
    } finally {
      setLoading(false);
    }
  };

  const handleFileUpload = async () => {
    if (!boqFile || !bomFile) {
      alert('Please select both BOQ and BOM files');
      return;
    }

    try {
      setUploading(true);
      setUploadProgress(0);
      const token = localStorage.getItem('token');
      
      const formData = new FormData();
      formData.append('boq_file', boqFile);
      formData.append('bom_file', bomFile);
      
      await axios.post(
        `${baseURL}/api/sd/upcoming-projects/${projectId}/upload-files`,
        formData,
        {
          headers: { 
            Authorization: `Bearer ${token}`,
            'Content-Type': 'multipart/form-data'
          },
          onUploadProgress: (progressEvent) => {
            const progress = Math.round((progressEvent.loaded * 100) / progressEvent.total);
            setUploadProgress(progress);
          }
        }
      );
      
      alert('Files uploaded successfully!');
      await fetchProject(); // Refresh project data
      setBoqFile(null);
      setBomFile(null);
      
    } catch (error) {
      console.error('Error uploading files:', error);
      alert(error.response?.data?.detail || 'Error uploading files');
    } finally {
      setUploading(false);
      setUploadProgress(0);
    }
  };

  const handleValidation = async () => {
    try {
      setValidating(true);
      const token = localStorage.getItem('token');
      
      const response = await axios.post(
        `${baseURL}/api/sd/upcoming-projects/${projectId}/validate`,
        {},
        {
          headers: { Authorization: `Bearer ${token}` }
        }
      );
      
      setValidationResult(response.data);
      await fetchProject(); // Refresh project data
      
    } catch (error) {
      console.error('Error validating files:', error);
      alert(error.response?.data?.detail || 'Error during validation');
    } finally {
      setValidating(false);
    }
  };

  const handleConvertToProject = async () => {
    try {
      setConverting(true);
      const token = localStorage.getItem('token');
      
      const response = await axios.post(
        `${baseURL}/api/sd/upcoming-projects/${projectId}/convert-to-project`,
        {},
        {
          headers: { Authorization: `Bearer ${token}` }
        }
      );
      
      alert(`Project converted successfully! Project ID: ${response.data.project_id}`);
      navigate('/sd/upcoming-projects');
      
    } catch (error) {
      console.error('Error converting project:', error);
      alert(error.response?.data?.detail || 'Error converting project');
    } finally {
      setConverting(false);
    }
  };

  const handleRejectProject = async () => {
    if (!rejectionReason.trim()) {
      alert('Please provide a rejection reason');
      return;
    }

    try {
      setRejecting(true);
      const token = localStorage.getItem('token');
      
      const formData = new FormData();
      formData.append('rejection_reason', rejectionReason);
      
      await axios.put(
        `${baseURL}/api/sd/upcoming-projects/${projectId}/reject`,
        formData,
        {
          headers: { Authorization: `Bearer ${token}` }
        }
      );
      
      alert('Project rejected successfully');
      navigate('/sd/upcoming-projects');
      
    } catch (error) {
      console.error('Error rejecting project:', error);
      alert(error.response?.data?.detail || 'Error rejecting project');
    } finally {
      setRejecting(false);
      setShowRejectionDialog(false);
      setRejectionReason('');
    }
  };

  const getStatusBadge = (status) => {
    const statusConfig = {
      'Pending': { color: 'bg-yellow-100 text-yellow-800', icon: AlertCircleIcon },
      'Converted': { color: 'bg-green-100 text-green-800', icon: CheckCircleIcon },
      'Rejected': { color: 'bg-red-100 text-red-800', icon: AlertTriangle }
    };

    const config = statusConfig[status] || { color: 'bg-gray-100 text-gray-800', icon: AlertCircleIcon };
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

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="flex items-center gap-4">
          <Button variant="ghost" onClick={() => navigate('/sd/upcoming-projects')}>
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back to Projects
          </Button>
          <h1 className="text-3xl font-bold text-gray-900">Project Validation</h1>
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
        <div className="flex items-center gap-4">
          <Button variant="ghost" onClick={() => navigate('/sd/upcoming-projects')}>
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back to Projects
          </Button>
          <h1 className="text-3xl font-bold text-gray-900">Project Validation</h1>
        </div>
        <Card>
          <CardContent className="p-6">
            <div className="text-center">
              <AlertTriangle className="mx-auto h-12 w-12 text-red-500" />
              <h3 className="mt-2 text-lg font-medium text-gray-900">Error Loading Project</h3>
              <p className="mt-1 text-gray-500">{error}</p>
              <Button onClick={fetchProject} className="mt-4">
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
        <div className="flex items-center gap-4">
          <Button variant="ghost" onClick={() => navigate('/sd/upcoming-projects')}>
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back to Projects
          </Button>
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Project Validation</h1>
            <p className="text-gray-600 mt-1">
              {project?.customer_name} - {project?.order_id}
            </p>
          </div>
        </div>
        <div className="text-right">
          {getStatusBadge(project?.order_status)}
        </div>
      </div>

      {/* Project Overview */}
      <Card>
        <CardHeader>
          <CardTitle>Project Overview</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div>
              <label className="text-sm font-medium text-gray-600">Customer</label>
              <p className="text-lg font-semibold text-gray-900">{project?.customer_name}</p>
            </div>
            <div>
              <label className="text-sm font-medium text-gray-600">POT ID</label>
              <p className="text-lg font-mono bg-blue-100 px-2 py-1 rounded inline-block">
                {project?.pot_id}
              </p>
            </div>
            <div>
              <label className="text-sm font-medium text-gray-600">Setup Cost</label>
              <p className="text-lg font-semibold text-green-600">
                {formatCurrency(project?.setup_cost || 0)}
              </p>
            </div>
          </div>
          
          {project?.discrepancy_notes && (
            <div className="mt-4">
              <label className="text-sm font-medium text-gray-600">Notes</label>
              <p className="text-sm text-gray-700 bg-gray-50 p-3 rounded mt-1">
                {project.discrepancy_notes}
              </p>
            </div>
          )}
        </CardContent>
      </Card>

      {/* File Upload Section */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <FileUp className="w-5 h-5" />
              File Upload
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                BOQ File (Purchase Order)
              </label>
              <Input
                type="file"
                accept=".csv,.xlsx,.xls"
                onChange={(e) => setBoqFile(e.target.files[0])}
                disabled={uploading}
              />
              {project?.po_boq_file && (
                <p className="text-sm text-green-600 mt-1 flex items-center gap-1">
                  <CheckCircleIcon className="w-4 h-4" />
                  BOQ file uploaded
                </p>
              )}
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                BOM File (Bill of Materials)
              </label>
              <Input
                type="file"
                accept=".csv,.xlsx,.xls"
                onChange={(e) => setBomFile(e.target.files[0])}
                disabled={uploading}
              />
              {project?.bom_file && (
                <p className="text-sm text-green-600 mt-1 flex items-center gap-1">
                  <CheckCircleIcon className="w-4 h-4" />
                  BOM file uploaded
                </p>
              )}
            </div>

            {uploading && (
              <div className="space-y-2">
                <div className="flex items-center justify-between text-sm">
                  <span>Uploading files...</span>
                  <span>{uploadProgress}%</span>
                </div>
                <Progress value={uploadProgress} className="h-2" />
              </div>
            )}

            <Button
              onClick={handleFileUpload}
              disabled={!boqFile || !bomFile || uploading}
              className="w-full"
            >
              <Upload className="w-4 h-4 mr-2" />
              {uploading ? 'Uploading...' : 'Upload Files'}
            </Button>
          </CardContent>
        </Card>

        {/* Validation Section */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <FileCheck className="w-5 h-5" />
              Validation Status
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center justify-between">
              <span className="text-sm font-medium">Current Status:</span>
              <Badge className={
                project?.validation_status === 'Valid' ? 'bg-green-100 text-green-800' :
                project?.validation_status === 'Invalid' ? 'bg-red-100 text-red-800' :
                'bg-yellow-100 text-yellow-800'
              }>
                {project?.validation_status || 'Not Validated'}
              </Badge>
            </div>

            {project?.validation_date && (
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium">Validated On:</span>
                <span className="text-sm text-gray-600">
                  {new Date(project.validation_date).toLocaleDateString()}
                </span>
              </div>
            )}

            <Button
              onClick={handleValidation}
              disabled={!project?.po_boq_file || !project?.bom_file || validating}
              className="w-full"
            >
              <FileCheck className="w-4 h-4 mr-2" />
              {validating ? 'Validating...' : 'Validate BOQ vs BOM'}
            </Button>

            {project?.gc_signoff_required && (
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
                <div className="flex items-center gap-2">
                  <AlertCircleIcon className="w-4 h-4 text-blue-600" />
                  <span className="text-sm font-medium text-blue-800">
                    GC Signoff Required
                  </span>
                </div>
                <p className="text-sm text-blue-700 mt-1">
                  This project requires General Counsel approval due to high value or third-party involvement.
                </p>
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Validation Results */}
      {validationResult && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              {validationResult.is_valid ? (
                <CheckCircleIcon className="w-5 h-5 text-green-600" />
              ) : (
                <AlertCircleIcon className="w-5 h-5 text-red-600" />
              )}
              Validation Results
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className={`p-4 rounded-lg border ${
              validationResult.is_valid 
                ? 'bg-green-50 border-green-200' 
                : 'bg-red-50 border-red-200'
            }`}>
              <p className="font-medium mb-2">
                {validationResult.validation_summary}
              </p>
              
              {validationResult.discrepancies.length > 0 && (
                <div className="mt-4">
                  <h4 className="font-medium text-gray-900 mb-2">Discrepancies Found:</h4>
                  <div className="space-y-2">
                    {validationResult.discrepancies.map((discrepancy, index) => (
                      <div key={index} className="bg-white border rounded p-3">
                        <div className="flex items-center justify-between">
                          <span className="font-medium text-sm">{discrepancy.sku}</span>
                          <Badge variant={discrepancy.severity === 'High' ? 'destructive' : 'secondary'}>
                            {discrepancy.severity}
                          </Badge>
                        </div>
                        <p className="text-sm text-gray-600 mt-1">{discrepancy.message}</p>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Action Buttons */}
      <Card>
        <CardHeader>
          <CardTitle>Project Actions</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex flex-col sm:flex-row gap-4">
            <Button
              onClick={handleConvertToProject}
              disabled={
                project?.order_status === 'Converted' ||
                project?.validation_status === 'Invalid' ||
                (project?.gc_signoff_required && project?.gc_signoff_status !== 'Approved') ||
                converting
              }
              className="bg-green-600 hover:bg-green-700"
            >
              <ArrowRight className="w-4 h-4 mr-2" />
              {converting ? 'Converting...' : 'Convert to Project'}
            </Button>

            <Button
              onClick={() => setShowRejectionDialog(true)}
              disabled={project?.order_status === 'Rejected' || project?.order_status === 'Converted'}
              variant="destructive"
            >
              <ThumbsDown className="w-4 h-4 mr-2" />
              Reject Project
            </Button>

            <Button variant="outline" onClick={fetchProject}>
              <RefreshCcw className="w-4 h-4 mr-2" />
              Refresh Data
            </Button>
          </div>

          {/* Conversion Requirements */}
          <div className="mt-6 space-y-2">
            <h4 className="font-medium text-gray-900">Conversion Requirements:</h4>
            <div className="space-y-1 text-sm">
              <div className={`flex items-center gap-2 ${
                project?.po_boq_file ? 'text-green-600' : 'text-gray-500'
              }`}>
                {project?.po_boq_file ? <CheckCircleIcon className="w-4 h-4" /> : <AlertCircleIcon className="w-4 h-4" />}
                BOQ file uploaded
              </div>
              <div className={`flex items-center gap-2 ${
                project?.bom_file ? 'text-green-600' : 'text-gray-500'
              }`}>
                {project?.bom_file ? <CheckCircleIcon className="w-4 h-4" /> : <AlertCircleIcon className="w-4 h-4" />}
                BOM file uploaded
              </div>
              <div className={`flex items-center gap-2 ${
                project?.validation_status === 'Valid' ? 'text-green-600' : 'text-gray-500'
              }`}>
                {project?.validation_status === 'Valid' ? <CheckCircleIcon className="w-4 h-4" /> : <AlertCircleIcon className="w-4 h-4" />}
                Validation passed
              </div>
              {project?.gc_signoff_required && (
                <div className={`flex items-center gap-2 ${
                  project?.gc_signoff_status === 'Approved' ? 'text-green-600' : 'text-gray-500'
                }`}>
                  {project?.gc_signoff_status === 'Approved' ? <CheckCircleIcon className="w-4 h-4" /> : <AlertCircleIcon className="w-4 h-4" />}
                  GC signoff approved
                </div>
              )}
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Rejection Dialog */}
      {showRejectionDialog && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <Card className="w-full max-w-md">
            <CardHeader>
              <CardTitle className="flex items-center justify-between">
                Reject Project
                <Button variant="ghost" size="sm" onClick={() => setShowRejectionDialog(false)}>
                  <X className="w-4 h-4" />
                </Button>
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Rejection Reason *
                </label>
                <Textarea
                  value={rejectionReason}
                  onChange={(e) => setRejectionReason(e.target.value)}
                  placeholder="Please provide a detailed reason for rejection..."
                  rows={4}
                />
              </div>
              <div className="flex gap-3">
                <Button
                  onClick={handleRejectProject}
                  disabled={!rejectionReason.trim() || rejecting}
                  variant="destructive"
                  className="flex-1"
                >
                  {rejecting ? 'Rejecting...' : 'Confirm Rejection'}
                </Button>
                <Button
                  onClick={() => setShowRejectionDialog(false)}
                  variant="outline"
                  className="flex-1"
                >
                  Cancel
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
};

export default ValidationInterface;