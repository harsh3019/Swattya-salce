import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import axios from 'axios';
import { Card, CardContent, CardHeader, CardTitle } from '../../ui/card';
import { Badge } from '../../ui/badge';
import { Button } from '../../ui/button';
import { Input } from '../../ui/input';
import { Textarea } from '../../ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../../ui/select';
import { Alert, AlertDescription } from '../../ui/alert';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from '../../ui/dialog';
import { 
  CheckCircle, 
  XCircle, 
  Clock, 
  AlertTriangle,
  Upload,
  FileText,
  Shield,
  Eye,
  Edit,
  ArrowLeft
} from 'lucide-react';
import { toast } from 'sonner';

const baseURL = process.env.REACT_APP_BACKEND_URL || import.meta.env.REACT_APP_BACKEND_URL;

// Status configurations with colors and rules
const STATUS_CONFIG = {
  'Pending': {
    color: 'bg-yellow-100 text-yellow-800',
    icon: Clock,
    canChangeTo: ['Approved', 'Rejected', 'Hold']
  },
  'Approved': {
    color: 'bg-green-100 text-green-800', 
    icon: CheckCircle,
    canChangeTo: ['Hold'], // Approved can only be put on hold, not rejected
    unlocks: 'bom_gc_section'
  },
  'Rejected': {
    color: 'bg-red-100 text-red-800',
    icon: XCircle,
    canChangeTo: [], // Final state - cannot be changed
    final: true
  },
  'Hold': {
    color: 'bg-orange-100 text-orange-800',
    icon: AlertTriangle,
    canChangeTo: ['Approved'] // Hold can only be moved to approved, not rejected
  }
};

const ProjectApprovalForm = () => {
  const { projectId } = useParams();
  const navigate = useNavigate();
  
  // State management
  const [project, setProject] = useState(null);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState(false);
  const [error, setError] = useState(null);
  
  // Approval form state
  const [approvalNotes, setApprovalNotes] = useState('');
  const [selectedStatus, setSelectedStatus] = useState('');
  const [showStatusChangeModal, setShowStatusChangeModal] = useState(false);
  
  // BOM/GC section state
  const [bomFile, setBomFile] = useState(null);
  const [gcSignatureFile, setGcSignatureFile] = useState(null);
  const [bomNotes, setBomNotes] = useState('');

  useEffect(() => {
    fetchProject();
  }, [projectId]);

  const fetchProject = async () => {
    try {
      setLoading(true);
      const token = localStorage.getItem('token');
      
      const response = await axios.get(`${baseURL}/api/sd/projects/${projectId}`, {
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

  const handleStatusChange = async () => {
    if (!selectedStatus || !project) return;
    
    try {
      setActionLoading(true);
      const token = localStorage.getItem('token');
      
      const response = await axios.put(
        `${baseURL}/api/sd/projects/${projectId}/status`,
        {
          status: selectedStatus,
          notes: approvalNotes
        },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      
      if (response.status === 200) {
        toast.success(`Project status changed to ${selectedStatus}`);
        setShowStatusChangeModal(false);
        setApprovalNotes('');
        setSelectedStatus('');
        await fetchProject(); // Refresh project data
      }
    } catch (error) {
      console.error('Error changing project status:', error);
      toast.error(error.response?.data?.detail || 'Failed to change project status');
    } finally {
      setActionLoading(false);
    }
  };

  const handleBomGcSubmission = async () => {
    if (!bomFile || !gcSignatureFile) {
      toast.error('Both BOM file and GC signature are required');
      return;
    }

    try {
      setActionLoading(true);
      const token = localStorage.getItem('token');
      
      const formData = new FormData();
      formData.append('bom_file', bomFile);
      formData.append('gc_signature', gcSignatureFile);
      formData.append('notes', bomNotes);
      
      const response = await axios.post(
        `${baseURL}/api/sd/projects/${projectId}/bom-gc-approval`,
        formData,
        { 
          headers: { 
            Authorization: `Bearer ${token}`,
            'Content-Type': 'multipart/form-data'
          } 
        }
      );
      
      if (response.status === 200) {
        toast.success('BOM/GC approval submitted successfully');
        setBomFile(null);
        setGcSignatureFile(null);
        setBomNotes('');
        await fetchProject(); // Refresh project data
      }
    } catch (error) {
      console.error('Error submitting BOM/GC approval:', error);
      toast.error(error.response?.data?.detail || 'Failed to submit BOM/GC approval');
    } finally {
      setActionLoading(false);
    }
  };

  const getStatusBadge = (status) => {
    const config = STATUS_CONFIG[status] || STATUS_CONFIG['Pending'];
    const Icon = config.icon;
    
    return (
      <Badge className={`${config.color} flex items-center gap-1`}>
        <Icon className="w-3 h-3" />
        {status}
      </Badge>
    );
  };

  const canChangeStatus = (currentStatus, newStatus) => {
    const config = STATUS_CONFIG[currentStatus];
    return config && config.canChangeTo.includes(newStatus);
  };

  const isBomGcSectionUnlocked = (status) => {
    const config = STATUS_CONFIG[status];
    return config && config.unlocks === 'bom_gc_section';
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center p-8">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (error) {
    return (
      <Alert className="m-6">
        <AlertTriangle className="h-4 w-4" />
        <AlertDescription>{error}</AlertDescription>
      </Alert>
    );
  }

  if (!project) {
    return (
      <Alert className="m-6">
        <AlertTriangle className="h-4 w-4" />
        <AlertDescription>Project not found</AlertDescription>
      </Alert>
    );
  }

  const currentStatus = project.status || 'Pending';
  const isFinalStatus = STATUS_CONFIG[currentStatus]?.final;

  return (
    <div className="p-6 max-w-6xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Button variant="outline" onClick={() => navigate('/sd/projects')}>
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back to Projects
          </Button>
          <div>
            <h1 className="text-3xl font-bold text-slate-800">{project.name}</h1>
            <p className="text-slate-600">Project Approval Workflow</p>
          </div>
        </div>
        <div className="flex items-center gap-4">
          {getStatusBadge(currentStatus)}
          <Button variant="outline" onClick={() => navigate(`/sd/projects/${projectId}`)}>
            <Eye className="w-4 h-4 mr-2" />
            View Details
          </Button>
        </div>
      </div>

      {/* Project Information Card */}
      <Card>
        <CardHeader>
          <CardTitle>Project Information</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div>
              <label className="text-sm font-medium text-gray-600">Customer</label>
              <p className="text-lg font-semibold text-gray-900">{project.customer_name}</p>
            </div>
            <div>
              <label className="text-sm font-medium text-gray-600">Project ID</label>
              <p className="text-lg font-mono text-gray-900">{project.project_id}</p>
            </div>
            <div>
              <label className="text-sm font-medium text-gray-600">Budget</label>
              <p className="text-lg font-semibold text-gray-900">
                ${project.budget?.toLocaleString() || '0'}
              </p>
            </div>
            <div>
              <label className="text-sm font-medium text-gray-600">Phase</label>
              <Badge variant="outline">{project.phase}</Badge>
            </div>
            <div>
              <label className="text-sm font-medium text-gray-600">Priority</label>
              <Badge variant="outline">{project.priority}</Badge>
            </div>
            <div>
              <label className="text-sm font-medium text-gray-600">Progress</label>
              <p className="text-lg font-semibold text-gray-900">
                {Math.round(project.overall_progress || 0)}%
              </p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Status Management Card */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Shield className="w-5 h-5" />
            Approval Status Management
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-6">
          <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
            <div>
              <h3 className="font-medium">Current Status</h3>
              <div className="mt-2">{getStatusBadge(currentStatus)}</div>
            </div>
            
            {!isFinalStatus && (
              <Dialog open={showStatusChangeModal} onOpenChange={setShowStatusChangeModal}>
                <DialogTrigger asChild>
                  <Button>
                    <Edit className="w-4 h-4 mr-2" />
                    Change Status
                  </Button>
                </DialogTrigger>
                <DialogContent>
                  <DialogHeader>
                    <DialogTitle>Change Project Status</DialogTitle>
                    <DialogDescription>
                      Select a new status for this project. Note: Some status changes are restricted by business rules.
                    </DialogDescription>
                  </DialogHeader>
                  
                  <div className="space-y-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        New Status
                      </label>
                      <Select value={selectedStatus} onValueChange={setSelectedStatus}>
                        <SelectTrigger>
                          <SelectValue placeholder="Select new status" />
                        </SelectTrigger>
                        <SelectContent>
                          {STATUS_CONFIG[currentStatus]?.canChangeTo.map((status) => (
                            <SelectItem key={status} value={status}>
                              <div className="flex items-center gap-2">
                                {React.createElement(STATUS_CONFIG[status].icon, { className: "w-4 h-4" })}
                                {status}
                              </div>
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>
                    
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Notes
                      </label>
                      <Textarea
                        value={approvalNotes}
                        onChange={(e) => setApprovalNotes(e.target.value)}
                        placeholder="Add notes for this status change..."
                        rows={3}
                      />
                    </div>
                    
                    <div className="flex justify-end space-x-2">
                      <Button 
                        variant="outline" 
                        onClick={() => setShowStatusChangeModal(false)}
                        disabled={actionLoading}
                      >
                        Cancel
                      </Button>
                      <Button 
                        onClick={handleStatusChange}
                        disabled={!selectedStatus || actionLoading}
                      >
                        {actionLoading ? 'Updating...' : 'Update Status'}
                      </Button>
                    </div>
                  </div>
                </DialogContent>
              </Dialog>
            )}
          </div>

          {/* Status Rules Information */}
          <Alert>
            <AlertTriangle className="h-4 w-4" />
            <AlertDescription>
              <strong>Business Rules:</strong>
              <ul className="list-disc list-inside mt-2 space-y-1">
                <li>Approved projects unlock BOM/GC approval section</li>
                <li>Rejected projects cannot be changed (final state)</li>
                <li>Hold projects can only be moved to Approved status</li>
                <li>All status changes require approval notes</li>
              </ul>
            </AlertDescription>
          </Alert>
        </CardContent>
      </Card>

      {/* BOM/GC Approval Section - Only shown when project is approved */}
      {isBomGcSectionUnlocked(currentStatus) && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <FileText className="w-5 h-5" />
              BOM/GC Approval Section
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-6">
            <Alert>
              <CheckCircle className="h-4 w-4" />
              <AlertDescription>
                This section is unlocked because the project status is <strong>Approved</strong>. 
                Please upload the required BOM file and GC signature to proceed.
              </AlertDescription>
            </Alert>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    BOM File *
                  </label>
                  <Input
                    type="file"
                    accept=".pdf,.doc,.docx,.xls,.xlsx"
                    onChange={(e) => setBomFile(e.target.files[0])}
                  />
                  {bomFile && (
                    <p className="text-sm text-green-600 mt-1">
                      Selected: {bomFile.name}
                    </p>
                  )}
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    GC Signature File *
                  </label>
                  <Input
                    type="file"
                    accept=".pdf,.png,.jpg,.jpeg"
                    onChange={(e) => setGcSignatureFile(e.target.files[0])}
                  />
                  {gcSignatureFile && (
                    <p className="text-sm text-green-600 mt-1">
                      Selected: {gcSignatureFile.name}
                    </p>
                  )}
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  BOM/GC Notes
                </label>
                <Textarea
                  value={bomNotes}
                  onChange={(e) => setBomNotes(e.target.value)}
                  placeholder="Add any additional notes for BOM/GC approval..."
                  rows={6}
                />
              </div>
            </div>

            <div className="flex justify-end">
              <Button 
                onClick={handleBomGcSubmission}
                disabled={!bomFile || !gcSignatureFile || actionLoading}
                className="bg-green-600 hover:bg-green-700"
              >
                <Upload className="w-4 h-4 mr-2" />
                {actionLoading ? 'Submitting...' : 'Submit BOM/GC Approval'}
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Status is not approved message */}
      {!isBomGcSectionUnlocked(currentStatus) && (
        <Card>
          <CardContent className="p-6">
            <Alert>
              <AlertTriangle className="h-4 w-4" />
              <AlertDescription>
                BOM/GC approval section will be unlocked when the project status is changed to <strong>Approved</strong>.
              </AlertDescription>
            </Alert>
          </CardContent>
        </Card>
      )}
    </div>
  );
};

export default ProjectApprovalForm;