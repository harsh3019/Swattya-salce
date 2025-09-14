import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { Card, CardContent, CardHeader, CardTitle } from '../../ui/card';
import { Badge } from '../../ui/badge';
import { Button } from '../../ui/button';
import { Input } from '../../ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../../ui/select';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../../ui/table';
import { 
  CheckCircle, 
  AlertTriangle, 
  Clock, 
  FileText, 
  ArrowRight, 
  Search,
  Filter,
  Plus,
  Eye,
  RefreshCcw
} from 'lucide-react';

const baseURL = process.env.REACT_APP_BACKEND_URL || import.meta.env.REACT_APP_BACKEND_URL;

const UpcomingProjectsList = () => {
  const navigate = useNavigate();
  const [projects, setProjects] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  const [refreshing, setRefreshing] = useState(false);

  // Stats state
  const [stats, setStats] = useState({
    total: 0,
    pending: 0,
    validated: 0,
    converted: 0,
    rejected: 0
  });

  useEffect(() => {
    fetchProjects();
  }, [statusFilter]);

  const fetchProjects = async () => {
    try {
      setLoading(true);
      const token = localStorage.getItem('token');
      
      const params = new URLSearchParams();
      if (statusFilter !== 'all') {
        params.append('status', statusFilter);
      }
      
      const response = await axios.get(`${baseURL}/api/sd/upcoming-projects/?${params.toString()}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      setProjects(response.data);
      calculateStats(response.data);
      setError(null);
    } catch (error) {
      console.error('Error fetching upcoming projects:', error);
      setError('Failed to fetch upcoming projects');
    } finally {
      setLoading(false);
    }
  };

  const calculateStats = (projectsData) => {
    const stats = {
      total: projectsData.length,
      pending: 0,
      validated: 0,
      converted: 0,
      rejected: 0
    };

    projectsData.forEach(project => {
      switch (project.order_status) {
        case 'Pending':
          stats.pending++;
          break;
        case 'Converted':
          stats.converted++;
          break;
        case 'Rejected':
          stats.rejected++;
          break;
        default:
          break;
      }
      
      if (project.validation_status === 'Valid') {
        stats.validated++;
      }
    });

    setStats(stats);
  };

  const handleRefresh = async () => {
    setRefreshing(true);
    await fetchProjects();
    setRefreshing(false);
  };

  const filteredProjects = projects.filter(project =>
    project.customer_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    project.order_id.toLowerCase().includes(searchTerm.toLowerCase()) ||
    project.pot_id.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const getStatusBadge = (status) => {
    const statusConfig = {
      'Pending': { color: 'bg-yellow-100 text-yellow-800', icon: Clock },
      'Converted': { color: 'bg-green-100 text-green-800', icon: CheckCircle },
      'Rejected': { color: 'bg-red-100 text-red-800', icon: AlertTriangle }
    };

    const config = statusConfig[status] || { color: 'bg-gray-100 text-gray-800', icon: Clock };
    const IconComponent = config.icon;

    return (
      <Badge className={`${config.color} flex items-center gap-1`}>
        <IconComponent className="w-3 h-3" />
        {status}
      </Badge>
    );
  };

  const getValidationBadge = (status) => {
    const statusConfig = {
      'Valid': { color: 'bg-green-100 text-green-800', icon: CheckCircle },
      'Invalid': { color: 'bg-red-100 text-red-800', icon: AlertTriangle },
      'Pending GC Sign-off': { color: 'bg-blue-100 text-blue-800', icon: Clock }
    };

    const config = statusConfig[status] || { color: 'bg-gray-100 text-gray-800', icon: Clock };
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

  const formatDate = (dateString) => {
    if (!dateString) return 'Not set';
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    });
  };

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <h1 className="text-3xl font-bold text-gray-900">Upcoming Projects</h1>
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
        <div className="flex items-center justify-between">
          <h1 className="text-3xl font-bold text-gray-900">Upcoming Projects</h1>
        </div>
        <Card>
          <CardContent className="p-6">
            <div className="text-center">
              <AlertTriangle className="mx-auto h-12 w-12 text-red-500" />
              <h3 className="mt-2 text-lg font-medium text-gray-900">Error Loading Projects</h3>
              <p className="mt-1 text-gray-500">{error}</p>
              <Button onClick={fetchProjects} className="mt-4">
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
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Upcoming Projects</h1>
          <p className="text-gray-600 mt-1">
            Manage project validation and conversion from won opportunities
          </p>
        </div>
        <div className="flex items-center gap-3">
          <Button
            onClick={handleRefresh}
            variant="outline"
            disabled={refreshing}
          >
            <RefreshCcw className={`w-4 h-4 mr-2 ${refreshing ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Total Projects</p>
                <p className="text-2xl font-bold text-gray-900">{stats.total}</p>
              </div>
              <FileText className="h-8 w-8 text-blue-500" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Pending</p>
                <p className="text-2xl font-bold text-yellow-600">{stats.pending}</p>
              </div>
              <Clock className="h-8 w-8 text-yellow-500" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Validated</p>
                <p className="text-2xl font-bold text-green-600">{stats.validated}</p>
              </div>
              <CheckCircle className="h-8 w-8 text-green-500" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Converted</p>
                <p className="text-2xl font-bold text-blue-600">{stats.converted}</p>
              </div>
              <ArrowRight className="h-8 w-8 text-blue-500" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Rejected</p>
                <p className="text-2xl font-bold text-red-600">{stats.rejected}</p>
              </div>
              <AlertTriangle className="h-8 w-8 text-red-500" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Filters */}
      <Card>
        <CardContent className="p-4">
          <div className="flex flex-col sm:flex-row gap-4">
            <div className="flex-1">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 h-4 w-4" />
                <Input
                  placeholder="Search by customer, order ID, or POT ID..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="pl-10"
                />
              </div>
            </div>
            <div className="w-48">
              <Select value={statusFilter} onValueChange={setStatusFilter}>
                <SelectTrigger>
                  <Filter className="w-4 h-4 mr-2" />
                  <SelectValue placeholder="Filter by status" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Status</SelectItem>
                  <SelectItem value="Pending">Pending</SelectItem>
                  <SelectItem value="Converted">Converted</SelectItem>
                  <SelectItem value="Rejected">Rejected</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Projects Table */}
      <Card>
        <CardHeader>
          <CardTitle>Projects List ({filteredProjects.length})</CardTitle>
        </CardHeader>
        <CardContent>
          {filteredProjects.length === 0 ? (
            <div className="text-center py-12">
              <FileText className="mx-auto h-12 w-12 text-gray-400" />
              <h3 className="mt-2 text-lg font-medium text-gray-900">No projects found</h3>
              <p className="mt-1 text-gray-500">
                {searchTerm || statusFilter !== 'all' 
                  ? 'Try adjusting your search or filter criteria.' 
                  : 'Won opportunities will automatically appear here.'}
              </p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Customer</TableHead>
                    <TableHead>Order ID</TableHead>
                    <TableHead>POT ID</TableHead>
                    <TableHead>Setup Cost</TableHead>
                    <TableHead>Order Status</TableHead>
                    <TableHead>Validation</TableHead>
                    <TableHead>GC Signoff</TableHead>
                    <TableHead>Created</TableHead>
                    <TableHead>Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {filteredProjects.map((project) => (
                    <TableRow key={project.id}>
                      <TableCell>
                        <div>
                          <div className="font-medium text-gray-900">
                            {project.customer_name}
                          </div>
                          <div className="text-sm text-gray-500">
                            {project.opp_id}
                          </div>
                        </div>
                      </TableCell>
                      <TableCell>
                        <code className="text-sm bg-gray-100 px-2 py-1 rounded">
                          {project.order_id}
                        </code>
                      </TableCell>
                      <TableCell>
                        <code className="text-sm bg-blue-100 px-2 py-1 rounded">
                          {project.pot_id}
                        </code>
                      </TableCell>
                      <TableCell>
                        <div className="font-medium">
                          {formatCurrency(project.setup_cost)}
                        </div>
                      </TableCell>
                      <TableCell>
                        {getStatusBadge(project.order_status)}
                      </TableCell>
                      <TableCell>
                        {getValidationBadge(project.validation_status)}
                      </TableCell>
                      <TableCell>
                        {project.gc_signoff_required ? (
                          getStatusBadge(project.gc_signoff_status)
                        ) : (
                          <Badge className="bg-gray-100 text-gray-600">
                            Not Required
                          </Badge>
                        )}
                      </TableCell>
                      <TableCell>
                        <div className="text-sm text-gray-900">
                          {formatDate(project.created_at)}
                        </div>
                      </TableCell>
                      <TableCell>
                        <div className="flex items-center gap-2">
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => navigate(`/sd/upcoming-projects/${project.id}`)}
                          >
                            <Eye className="w-4 h-4 mr-1" />
                            View
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

export default UpcomingProjectsList;