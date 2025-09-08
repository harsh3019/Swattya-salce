import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogFooter } from './ui/dialog';
import { Button } from './ui/button';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './ui/select';
import { Badge } from './ui/badge';
import { Label } from './ui/label';
import { Card, CardContent } from './ui/card';
import { Separator } from './ui/separator';
import { toast } from 'sonner';
import { 
  User, 
  Building, 
  Phone, 
  Mail, 
  CheckCircle2, 
  XCircle, 
  TrendingUp,
  Loader2,
  X
} from 'lucide-react';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

/**
 * LeadChangeStatusModal Component
 * 
 * A modal for changing lead status with opportunity conversion support.
 * 
 * Props:
 * - leadId: string - The ID of the lead to update
 * - initialLead: object (optional) - Initial lead data to avoid extra API call
 * - isOpen: boolean - Whether the modal is open
 * - onClose: function - Callback when modal closes
 * - onSuccess: function - Callback when status change succeeds, receives updated lead
 * 
 * Behavior Decision: Modal stays open after approval to allow immediate conversion.
 * This provides better UX by letting users complete the full workflow in one session.
 */
export const LeadChangeStatusModal = ({ 
  leadId, 
  initialLead = null, 
  isOpen, 
  onClose, 
  onSuccess 
}) => {
  // State
  const [lead, setLead] = useState(initialLead);
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [selectedStatus, setSelectedStatus] = useState('');
  const [availableStatuses, setAvailableStatuses] = useState([
    { value: 'approved', label: 'Approved' },
    { value: 'Rejected', label: 'Rejected' }
  ]);

  // Refs for focus management
  const modalRef = useRef(null);
  const firstFocusableRef = useRef(null);
  const lastFocusableRef = useRef(null);

  // Load lead data when modal opens
  useEffect(() => {
    if (isOpen && leadId && !initialLead) {
      fetchLead();
    } else if (initialLead) {
      setLead(initialLead);
      initializeForm(initialLead);
    }
  }, [isOpen, leadId, initialLead]);

  // Initialize form with lead data
  useEffect(() => {
    if (lead) {
      initializeForm(lead);
    }
  }, [lead]);

  // Focus management for accessibility
  useEffect(() => {
    if (isOpen) {
      // Focus the first focusable element when modal opens
      setTimeout(() => {
        if (firstFocusableRef.current) {
          firstFocusableRef.current.focus();
        }
      }, 100);
    }
  }, [isOpen]);

  // Keyboard event handler for accessibility
  useEffect(() => {
    const handleKeyDown = (event) => {
      if (!isOpen) return;

      if (event.key === 'Escape') {
        onClose();
        return;
      }

      if (event.key === 'Tab') {
        const focusableElements = modalRef.current?.querySelectorAll(
          'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
        );

        if (!focusableElements || focusableElements.length === 0) return;

        const firstElement = focusableElements[0];
        const lastElement = focusableElements[focusableElements.length - 1];

        if (event.shiftKey) {
          if (document.activeElement === firstElement) {
            event.preventDefault();
            lastElement.focus();
          }
        } else {
          if (document.activeElement === lastElement) {
            event.preventDefault();
            firstElement.focus();
          }
        }
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, onClose]);

  const fetchLead = async () => {
    try {
      setLoading(true);
      const response = await axios.get(`${API}/leads/${leadId}`);
      setLead(response.data);
    } catch (error) {
      console.error('Failed to fetch lead:', error);
      toast.error('Failed to load lead data');
      onClose();
    } finally {
      setLoading(false);
    }
  };

  const initializeForm = (leadData) => {
    // Set initial status based on current approval status
    const currentApprovalStatus = leadData.approval_status || 'Pending';
    
    if (currentApprovalStatus === 'Approved') {
      setSelectedStatus('approved');
      // Add convert option if already approved
      setAvailableStatuses([
        { value: 'approved', label: 'Approved' },
        { value: 'Rejected', label: 'Rejected' },
        { value: 'convert_to_opp', label: 'Convert to Opportunity' }
      ]);
    } else if (currentApprovalStatus === 'Rejected') {
      setSelectedStatus('Rejected');
    } else {
      setSelectedStatus('approved'); // Default to approved for pending leads
    }
  };

  const handleStatusChange = async () => {
    if (!selectedStatus || !lead) return;

    try {
      setSaving(true);

      const response = await axios.post(`${API}/leads/${lead.id}/status`, {
        status: selectedStatus
      });

      const { success, lead: updatedLead, converted, opportunity_id } = response.data;

      if (success) {
        setLead(updatedLead);

        // Show appropriate toast messages
        if (converted) {
          toast.success('Lead converted to Opportunity.', {
            description: `Opportunity ID: ${opportunity_id}`
          });
        } else {
          toast.success('Lead status updated.');
        }

        // Update available statuses if lead was just approved
        if (selectedStatus === 'approved' && !converted) {
          setAvailableStatuses([
            { value: 'approved', label: 'Approved' },
            { value: 'Rejected', label: 'Rejected' },
            { value: 'convert_to_opp', label: 'Convert to Opportunity' }
          ]);
          
          // Keep modal open to allow immediate conversion
          // User can now select "Convert to Opportunity" option
        } else {
          // Close modal for other status changes or after conversion
          if (onSuccess) {
            onSuccess(updatedLead);
          }
          onClose();
        }
      }
    } catch (error) {
      console.error('Failed to update lead status:', error);
      const errorMessage = error.response?.data?.detail || 'Failed to update lead status';
      toast.error(errorMessage);
    } finally {
      setSaving(false);
    }
  };

  const getStatusBadgeProps = (status) => {
    switch (status?.toLowerCase()) {
      case 'approved':
        return { className: 'bg-green-100 text-green-800', icon: CheckCircle2 };
      case 'rejected':
        return { className: 'bg-red-100 text-red-800', icon: XCircle };
      case 'pending':
        return { className: 'bg-yellow-100 text-yellow-800', icon: TrendingUp };
      default:
        return { className: 'bg-gray-100 text-gray-800', icon: TrendingUp };
    }
  };

  const formatPhoneNumber = (phone) => {
    if (!phone) return 'Not provided';
    // Format Indian phone numbers
    const cleaned = phone.replace(/\D/g, '');
    if (cleaned.length === 10) {
      return `+91 ${cleaned.slice(0, 5)} ${cleaned.slice(5)}`;
    }
    return phone;
  };

  if (!isOpen) return null;

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent 
        className="sm:max-w-md max-h-[90vh] overflow-y-auto"
        ref={modalRef}
        aria-labelledby="lead-status-modal-title"
        aria-describedby="lead-status-modal-description"
      >
        <DialogHeader>
          <DialogTitle id="lead-status-modal-title" className="flex items-center space-x-2">
            <TrendingUp className="h-5 w-5" />
            <span>Change Lead Status</span>
          </DialogTitle>
          <DialogDescription id="lead-status-modal-description">
            Update the status of this lead or convert it to an opportunity.
          </DialogDescription>
        </DialogHeader>

        {loading ? (
          <div className="flex items-center justify-center py-8">
            <Loader2 className="h-6 w-6 animate-spin" />
            <span className="ml-2">Loading lead data...</span>
          </div>
        ) : lead ? (
          <div className="space-y-6">
            {/* Lead Preview Card */}
            <Card>
              <CardContent className="p-4">
                <div className="space-y-3">
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <h3 className="font-semibold text-lg flex items-center space-x-2">
                        <User className="h-4 w-4 text-blue-600" />
                        <span>{lead.project_title}</span>
                      </h3>
                      <p className="text-sm text-gray-600 font-mono">{lead.lead_id}</p>
                    </div>
                    
                    <div className="flex items-center space-x-1">
                      {(() => {
                        const { className, icon: StatusIcon } = getStatusBadgeProps(lead.approval_status);
                        return (
                          <Badge className={className}>
                            <StatusIcon className="h-3 w-3 mr-1" />
                            {lead.approval_status || 'Pending'}
                          </Badge>
                        );
                      })()}
                    </div>
                  </div>

                  <Separator />

                  <div className="grid grid-cols-1 gap-3">
                    <div className="flex items-center space-x-2">
                      <Building className="h-4 w-4 text-gray-500" />
                      <div>
                        <p className="text-sm font-medium">Company</p>
                        <p className="text-sm text-gray-600">{lead.company_name || 'Not specified'}</p>
                      </div>
                    </div>

                    <div className="flex items-center space-x-2">
                      <Phone className="h-4 w-4 text-gray-500" />
                      <div>
                        <p className="text-sm font-medium">Contact Number</p>
                        <p className="text-sm text-gray-600">{formatPhoneNumber(lead.contact_phone)}</p>
                      </div>
                    </div>

                    <div className="flex items-center space-x-2">
                      <Mail className="h-4 w-4 text-gray-500" />
                      <div>
                        <p className="text-sm font-medium">Email</p>
                        <p className="text-sm text-gray-600">{lead.contact_email || 'Not provided'}</p>
                      </div>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Status Selection */}
            <div className="space-y-3">
              <Label htmlFor="status-select" className="text-sm font-medium">
                New Status
              </Label>
              <Select 
                value={selectedStatus} 
                onValueChange={setSelectedStatus}
                disabled={saving}
              >
                <SelectTrigger 
                  id="status-select"
                  ref={firstFocusableRef}
                  className="w-full"
                >
                  <SelectValue placeholder="Select new status" />
                </SelectTrigger>
                <SelectContent>
                  {availableStatuses.map((status) => (
                    <SelectItem key={status.value} value={status.value}>
                      {status.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              
              {selectedStatus === 'convert_to_opp' && (
                <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
                  <div className="flex items-center space-x-2">
                    <CheckCircle2 className="h-4 w-4 text-blue-600" />
                    <p className="text-sm text-blue-800">
                      This will convert the lead to an opportunity with ID format: POT-XXXXXXXX
                    </p>
                  </div>
                </div>
              )}
            </div>
          </div>
        ) : (
          <div className="flex items-center justify-center py-8">
            <XCircle className="h-6 w-6 text-red-500" />
            <span className="ml-2">Failed to load lead data</span>
          </div>
        )}

        <DialogFooter className="flex space-x-2">
          <Button
            variant="outline"
            onClick={onClose}
            disabled={saving}
            ref={lastFocusableRef}
          >
            Cancel
          </Button>
          <Button
            onClick={handleStatusChange}
            disabled={saving || !selectedStatus || loading}
            className="min-w-[120px]"
          >
            {saving ? (
              <>
                <Loader2 className="h-4 w-4 animate-spin mr-2" />
                Updating...
              </>
            ) : (
              'Update Status'
            )}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
};

export default LeadChangeStatusModal;