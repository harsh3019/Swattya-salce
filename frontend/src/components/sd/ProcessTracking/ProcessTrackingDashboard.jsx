import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Card, CardContent, CardHeader, CardTitle } from '../../ui/card';
import { Badge } from '../../ui/badge';
import { Button } from '../../ui/button';
import { Input } from '../../ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../../ui/select';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../../ui/table';
import { Progress } from '../../ui/progress';
import { 
  CheckCircle, 
  Clock, 
  AlertTriangle,
  ArrowRight,
  Search,
  Filter,
  Calendar,
  User,
  FileText,
  Target,
  TrendingUp,
  BarChart3,
  Activity,
  Eye,
  RefreshCcw
} from 'lucide-react';

const baseURL = process.env.REACT_APP_BACKEND_URL || import.meta.env.REACT_APP_BACKEND_URL;

// Status configurations for visual consistency
const STATUS_COLORS = {
  // Opportunity stages
  'L1': 'bg-blue-100 text-blue-800',
  'L2': 'bg-indigo-100 text-indigo-800', 
  'L3': 'bg-purple-100 text-purple-800',
  'L4': 'bg-pink-100 text-pink-800',
  'L5': 'bg-orange-100 text-orange-800',
  'L6': 'bg-green-100 text-green-800',
  'L7': 'bg-red-100 text-red-800',
  
  // SD statuses
  'Pending': 'bg-yellow-100 text-yellow-800',
  'Validated': 'bg-blue-100 text-blue-800',
  'Converted': 'bg-green-100 text-green-800',
  'Rejected': 'bg-red-100 text-red-800',
  'Active': 'bg-green-100 text-green-800',
  'Completed': 'bg-gray-100 text-gray-800',
  'On Hold': 'bg-orange-100 text-orange-800',
  
  // Approval statuses
  'Approved': 'bg-green-100 text-green-800',
  'Hold': 'bg-orange-100 text-orange-800'
};

const ProcessTrackingDashboard = () => {
  const [trackingData, setTrackingData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  const [dateFilter, setDateFilter] = useState('all');
  const [refreshing, setRefreshing] = useState(false);

  // Summary stats
  const [stats, setStats] = useState({
    total_opportunities: 0,
    active_opportunities: 0,
    won_opportunities: 0,
    upcoming_projects: 0,
    active_projects: 0,
    approved_projects: 0,
    completion_rate: 0,
    avg_cycle_time: 0
  });

  useEffect(() => {
    fetchProcessTracking();
  }, [statusFilter, dateFilter]);

  const fetchProcessTracking = async () => {
    try {
      setLoading(true);
      const token = localStorage.getItem('token');
      const headers = { Authorization: `Bearer ${token}` };

      // Build query parameters
      const params = new URLSearchParams();
      if (statusFilter !== 'all') params.append('status', statusFilter);
      if (dateFilter !== 'all') params.append('date_range', dateFilter);
      
      const response = await axios.get(`${baseURL}/api/sd/tracking?${params.toString()}`, { headers });
      
      setTrackingData(response.data.tracking_data || []);
      setStats(response.data.summary || stats);
      setError(null);
    } catch (error) {
      console.error('Error fetching process tracking:', error);
      setError('Failed to fetch process tracking data');
    } finally {
      setLoading(false);
    }
  };

  const handleRefresh = async () => {
    setRefreshing(true);
    await fetchProcessTracking();
    setRefreshing(false);
  };

  const formatDate = (dateString) => {
    if (!dateString) return 'N/A';
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    });
  };

  const formatDateTime = (dateString) => {
    if (!dateString) return 'N/A';
    return new Date(dateString).toLocaleString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const getStatusBadge = (status) => {
    const colorClass = STATUS_COLORS[status] || 'bg-gray-100 text-gray-800';
    return (
      <Badge className={colorClass}>
        {status}
      </Badge>
    );
  };

  const calculateCycleTime = (startDate, endDate) => {
    if (!startDate || !endDate) return 'N/A';
    const start = new Date(startDate);
    const end = new Date(endDate);
    const diffTime = Math.abs(end - start);
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
    return `${diffDays} days`;
  };

  const getTimelineStatus = (record) => {
    const timeline = [];
    
    // Opportunity creation
    timeline.push({
      title: 'Opportunity Created',
      description: `Started at ${record.opportunity_stage || 'L1'}`,
      timestamp: record.opportunity_created_at,
      status: 'completed',
      icon: Target
    });

    // Opportunity progression through stages
    if (record.opportunity_stage && record.opportunity_stage !== 'L1') {
      timeline.push({
        title: `Reached Stage ${record.opportunity_stage}`,
        description: record.opportunity_stage === 'L6' ? 'Won!' : `Stage ${record.opportunity_stage} completed`,
        timestamp: record.opportunity_updated_at,
        status: record.opportunity_stage === 'L6' ? 'completed' : 'in-progress',
        icon: CheckCircle
      });
    }

    // SD upcoming project creation
    if (record.upcoming_project_id) {
      timeline.push({
        title: 'Upcoming Project Created',
        description: 'Moved to Services Delivery',
        timestamp: record.upcoming_project_created_at,
        status: 'completed',
        icon: ArrowRight
      });
    }

    // Project conversion
    if (record.active_project_id) {
      timeline.push({
        title: 'Converted to Active Project',
        description: 'Project management initiated',
        timestamp: record.project_created_at,
        status: 'completed',
        icon: Activity
      });
    }

    // Project approval
    if (record.project_approval_status) {
      timeline.push({
        title: 'Project Approval',
        description: `Status: ${record.project_approval_status}`,
        timestamp: record.project_approval_timestamp,
        status: record.project_approval_status === 'Approved' ? 'completed' : 'pending',
        icon: record.project_approval_status === 'Approved' ? CheckCircle : Clock
      });
    }

    return timeline;
  };

  const filteredData = trackingData.filter(record => {
    const matchesSearch = 
      record.customer_name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      record.opportunity_id?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      record.project_name?.toLowerCase().includes(searchTerm.toLowerCase());
    
    return matchesSearch;
  });

  if (loading) {
    return (
      <div className="flex items-center justify-center p-8">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-slate-800">Process Tracking</h1>
          <p className="text-slate-600">Complete opportunity-to-project lifecycle visibility</p>
        </div>
        <Button onClick={handleRefresh} disabled={refreshing}>
          <RefreshCcw className={`w-4 h-4 mr-2 ${refreshing ? 'animate-spin' : ''}`} />
          Refresh
        </Button>
      </div>

      {/* Summary Statistics */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <Card className="border-0 shadow-sm bg-gradient-to-br from-blue-50 to-blue-100">
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-blue-600">Total Opportunities</p>
                <p className="text-3xl font-bold text-blue-800 mt-2">{stats.total_opportunities}</p>
              </div>
              <Target className="w-12 h-12 text-blue-600" />
            </div>
          </CardContent>
        </Card>
        
        <Card className="border-0 shadow-sm bg-gradient-to-br from-green-50 to-green-100">
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-green-600">Won Opportunities</p>
                <p className="text-3xl font-bold text-green-800 mt-2">{stats.won_opportunities}</p>
              </div>
              <CheckCircle className="w-12 h-12 text-green-600" />
            </div>
          </CardContent>
        </Card>
        
        <Card className="border-0 shadow-sm bg-gradient-to-br from-purple-50 to-purple-100">
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-purple-600">Active Projects</p>
                <p className="text-3xl font-bold text-purple-800 mt-2">{stats.active_projects}</p>
              </div>
              <Activity className="w-12 h-12 text-purple-600" />
            </div>
          </CardContent>
        </Card>
        
        <Card className="border-0 shadow-sm bg-gradient-to-br from-orange-50 to-orange-100">
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-orange-600">Completion Rate</p>
                <p className="text-3xl font-bold text-orange-800 mt-2">{stats.completion_rate}%</p>
              </div>
              <TrendingUp className="w-12 h-12 text-orange-600" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Filters */}
      <Card>
        <CardContent className="p-6">
          <div className="flex flex-col sm:flex-row gap-4 items-start sm:items-center">
            <div className="relative flex-1 max-w-sm">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
              <Input
                placeholder="Search by customer, opportunity, or project..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pl-10"
              />
            </div>
            
            <Select value={statusFilter} onValueChange={setStatusFilter}>
              <SelectTrigger className="w-[200px]">
                <SelectValue placeholder="Filter by status" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Statuses</SelectItem>
                <SelectItem value="L1-L5">Opportunity Stages (L1-L5)</SelectItem>
                <SelectItem value="L6">Won Opportunities (L6)</SelectItem>
                <SelectItem value="upcoming">Upcoming Projects</SelectItem>
                <SelectItem value="active">Active Projects</SelectItem>
                <SelectItem value="approved">Approved Projects</SelectItem>
              </SelectContent>
            </Select>
            
            <Select value={dateFilter} onValueChange={setDateFilter}>
              <SelectTrigger className="w-[180px]">
                <SelectValue placeholder="Filter by date" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Time</SelectItem>
                <SelectItem value="7d">Last 7 days</SelectItem>
                <SelectItem value="30d">Last 30 days</SelectItem>
                <SelectItem value="90d">Last 90 days</SelectItem>
                <SelectItem value="1y">Last year</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </CardContent>
      </Card>

      {/* Process Tracking Table */}
      <Card>
        <CardHeader>
          <CardTitle>End-to-End Process Tracking</CardTitle>
        </CardHeader>
        <CardContent>
          {error ? (
            <div className="text-center py-8">
              <AlertTriangle className="w-12 h-12 text-red-400 mx-auto mb-4" />
              <p className="text-red-600">{error}</p>
            </div>
          ) : filteredData.length === 0 ? (
            <div className="text-center py-8">
              <FileText className="w-12 h-12 text-gray-400 mx-auto mb-4" />
              <p className="text-gray-600">No tracking data found</p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Customer</TableHead>
                    <TableHead>Opportunity</TableHead>
                    <TableHead>Current Stage</TableHead>
                    <TableHead>SD Status</TableHead>
                    <TableHead>Project Status</TableHead>
                    <TableHead>Timeline</TableHead>
                    <TableHead>Cycle Time</TableHead>
                    <TableHead>Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {filteredData.map((record) => (
                    <TableRow key={record.id}>
                      <TableCell>
                        <div>
                          <div className="font-medium text-gray-900">
                            {record.customer_name || 'Unknown'}
                          </div>
                          <div className="text-sm text-gray-500">
                            {record.opportunity_id}
                          </div>
                        </div>
                      </TableCell>
                      
                      <TableCell>
                        <div>
                          <div className="font-medium text-gray-900">
                            {record.opportunity_name || 'Unnamed Opportunity'}
                          </div>
                          <div className="text-sm text-gray-500">
                            Created: {formatDate(record.opportunity_created_at)}
                          </div>
                        </div>
                      </TableCell>
                      
                      <TableCell>
                        {getStatusBadge(record.opportunity_stage || 'L1')}
                      </TableCell>
                      
                      <TableCell>
                        {record.upcoming_project_status ? 
                          getStatusBadge(record.upcoming_project_status) : 
                          <span className="text-gray-400">Not in SD</span>
                        }
                      </TableCell>
                      
                      <TableCell>
                        {record.project_status ? 
                          getStatusBadge(record.project_status) : 
                          <span className="text-gray-400">No Project</span>
                        }
                      </TableCell>
                      
                      <TableCell>
                        <div className="text-sm">
                          <div className="text-gray-900">
                            Started: {formatDate(record.opportunity_created_at)}
                          </div>
                          {record.project_created_at && (
                            <div className="text-gray-500">
                              Project: {formatDate(record.project_created_at)}
                            </div>
                          )}
                        </div>
                      </TableCell>
                      
                      <TableCell>
                        <div className="text-sm font-medium">
                          {calculateCycleTime(record.opportunity_created_at, record.project_created_at)}
                        </div>
                      </TableCell>
                      
                      <TableCell>
                        <div className="flex items-center gap-2">
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => {
                              // Show detailed timeline modal
                              console.log('View timeline for:', record);
                            }}
                          >
                            <Eye className="w-4 h-4 mr-1" />
                            Timeline
                          </Button>
                        </div>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
};

export default ProcessTrackingDashboard;