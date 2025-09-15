import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
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
  AlertTriangle, 
  Clock, 
  Briefcase, 
  ArrowRight, 
  Search,
  Filter,
  Plus,
  Eye,
  RefreshCcw,
  Users,
  DollarSign,
  Calendar,
  TrendingUp,
  Edit,
  Settings
} from 'lucide-react';
import { toast } from 'sonner';

const baseURL = process.env.REACT_APP_BACKEND_URL || import.meta.env.REACT_APP_BACKEND_URL;

const ProjectsList = () => {
  const navigate = useNavigate();
  const [projects, setProjects] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  const [phaseFilter, setPhaseFilter] = useState('all');
  const [refreshing, setRefreshing] = useState(false);

  // Stats state
  const [stats, setStats] = useState({
    total: 0,
    active: 0,
    planning: 0,
    execution: 0,
    completed: 0,
    onHold: 0
  });

  useEffect(() => {
    fetchProjects();
  }, [statusFilter, phaseFilter]);

  const fetchProjects = async () => {
    try {
      setLoading(true);
      const token = localStorage.getItem('token');
      
      const params = new URLSearchParams();
      if (statusFilter !== 'all') {
        params.append('status', statusFilter);
      }
      if (phaseFilter !== 'all') {
        params.append('phase', phaseFilter);
      }
      
      const response = await axios.get(`${baseURL}/api/sd/projects/?${params.toString()}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      setProjects(response.data);
      calculateStats(response.data);
      setError(null);
    } catch (error) {
      console.error('Error fetching projects:', error);
      setError('Failed to fetch projects');
    } finally {
      setLoading(false);
    }
  };

  const calculateStats = (projectsData) => {
    const stats = {
      total: projectsData.length,
      active: 0,
      planning: 0,
      execution: 0,
      completed: 0,
      onHold: 0
    };

    projectsData.forEach(project => {
      switch (project.status) {
        case 'Active':
          stats.active++;
          break;
        case 'Completed':
          stats.completed++;
          break;
        case 'On Hold':
          stats.onHold++;
          break;
        default:
          break;
      }
      
      switch (project.phase) {
        case 'Planning':
          stats.planning++;
          break;
        case 'Execution':
          stats.execution++;
          break;
        default:
          break;
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
    project.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    project.project_id.toLowerCase().includes(searchTerm.toLowerCase()) ||
    project.customer_name.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const getStatusBadge = (status) => {
    const statusConfig = {
      'Active': { color: 'bg-green-100 text-green-800', icon: CheckCircle },
      'On Hold': { color: 'bg-yellow-100 text-yellow-800', icon: Clock },
      'Completed': { color: 'bg-blue-100 text-blue-800', icon: CheckCircle },
      'Cancelled': { color: 'bg-red-100 text-red-800', icon: AlertTriangle }
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

  const getPhaseBadge = (phase) => {
    const phaseConfig = {
      'Planning': { color: 'bg-purple-100 text-purple-800', icon: Calendar },
      'Execution': { color: 'bg-orange-100 text-orange-800', icon: TrendingUp },
      'Closure': { color: 'bg-gray-100 text-gray-800', icon: CheckCircle }
    };

    const config = phaseConfig[phase] || { color: 'bg-gray-100 text-gray-800', icon: Calendar };
    const IconComponent = config.icon;

    return (
      <Badge className={`${config.color} flex items-center gap-1`}>
        <IconComponent className="w-3 h-3" />
        {phase}
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
          <h1 className="text-3xl font-bold text-gray-900">Active Projects</h1>
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
          <h1 className="text-3xl font-bold text-gray-900">Active Projects</h1>
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
          <h1 className="text-3xl font-bold text-gray-900">Active Projects</h1>
          <p className="text-gray-600 mt-1">
            Manage and track all active delivery projects
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
          <Button
            onClick={() => navigate('/sd/projects/create')}
            className="bg-blue-600 hover:bg-blue-700"
          >
            <Plus className="w-4 h-4 mr-2" />
            New Project
          </Button>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-6 gap-4">
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Total Projects</p>
                <p className="text-2xl font-bold text-gray-900">{stats.total}</p>
              </div>
              <Briefcase className="h-8 w-8 text-blue-500" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Active</p>
                <p className="text-2xl font-bold text-green-600">{stats.active}</p>
              </div>
              <CheckCircle className="h-8 w-8 text-green-500" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Planning</p>
                <p className="text-2xl font-bold text-purple-600">{stats.planning}</p>
              </div>
              <Calendar className="h-8 w-8 text-purple-500" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Execution</p>
                <p className="text-2xl font-bold text-orange-600">{stats.execution}</p>
              </div>
              <TrendingUp className="h-8 w-8 text-orange-500" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Completed</p>
                <p className="text-2xl font-bold text-blue-600">{stats.completed}</p>
              </div>
              <CheckCircle className="h-8 w-8 text-blue-500" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">On Hold</p>
                <p className="text-2xl font-bold text-yellow-600">{stats.onHold}</p>
              </div>
              <Clock className="h-8 w-8 text-yellow-500" />
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
                  placeholder="Search by project name, ID, or customer..."
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
                  <SelectItem value="Active">Active</SelectItem>
                  <SelectItem value="On Hold">On Hold</SelectItem>
                  <SelectItem value="Completed">Completed</SelectItem>
                  <SelectItem value="Cancelled">Cancelled</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="w-48">
              <Select value={phaseFilter} onValueChange={setPhaseFilter}>
                <SelectTrigger>
                  <Filter className="w-4 h-4 mr-2" />
                  <SelectValue placeholder="Filter by phase" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Phases</SelectItem>
                  <SelectItem value="Planning">Planning</SelectItem>
                  <SelectItem value="Execution">Execution</SelectItem>
                  <SelectItem value="Closure">Closure</SelectItem>
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
              <Briefcase className="mx-auto h-12 w-12 text-gray-400" />
              <h3 className="mt-2 text-lg font-medium text-gray-900">No projects found</h3>
              <p className="mt-1 text-gray-500">
                {searchTerm || statusFilter !== 'all' || phaseFilter !== 'all'
                  ? 'Try adjusting your search or filter criteria.' 
                  : 'Converted upcoming projects will appear here.'}
              </p>
              {filteredProjects.length === 0 && searchTerm === '' && statusFilter === 'all' && phaseFilter === 'all' && (
                <Button 
                  onClick={() => navigate('/sd/projects/create')} 
                  className="mt-4"
                >
                  <Plus className="w-4 h-4 mr-2" />
                  Create New Project
                </Button>
              )}
            </div>
          ) : (
            <div className="overflow-x-auto">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Project</TableHead>
                    <TableHead>Customer</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Phase</TableHead>
                    <TableHead>Progress</TableHead>
                    <TableHead>Budget</TableHead>
                    <TableHead>Timeline</TableHead>
                    <TableHead>Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {filteredProjects.map((project) => (
                    <TableRow key={project.id}>
                      <TableCell>
                        <div>
                          <div className="font-medium text-gray-900">
                            {project.name}
                          </div>
                          <div className="text-sm text-gray-500">
                            <code className="text-xs bg-gray-100 px-1 py-0.5 rounded">
                              {project.project_id}
                            </code>
                          </div>
                        </div>
                      </TableCell>
                      <TableCell>
                        <div className="font-medium text-gray-900">
                          {project.customer_name}
                        </div>
                      </TableCell>
                      <TableCell>
                        {getStatusBadge(project.status)}
                      </TableCell>
                      <TableCell>
                        {getPhaseBadge(project.phase)}
                      </TableCell>
                      <TableCell>
                        <div className="w-20">
                          <Progress 
                            value={project.overall_progress || 0} 
                            className="h-2"
                          />
                          <div className="text-xs text-gray-500 mt-1">
                            {Math.round(project.overall_progress || 0)}%
                          </div>
                        </div>
                      </TableCell>
                      <TableCell>
                        <div>
                          <div className="font-medium text-gray-900">
                            {formatCurrency(project.budget || 0)}
                          </div>
                          <div className="text-xs text-gray-500">
                            Spent: {formatCurrency(project.actual_cost || 0)}
                          </div>
                        </div>
                      </TableCell>
                      <TableCell>
                        <div className="text-sm">
                          <div className="text-gray-900">
                            Start: {formatDate(project.start_date)}
                          </div>
                          <div className="text-gray-500">
                            End: {formatDate(project.end_date)}
                          </div>
                        </div>
                      </TableCell>
                      <TableCell>
                        <div className="flex items-center gap-2">
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => navigate(`/sd/projects/${project.id}`)}
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

export default ProjectsList;