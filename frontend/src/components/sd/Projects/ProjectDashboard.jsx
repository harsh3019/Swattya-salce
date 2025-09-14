import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import axios from 'axios';
import { Card, CardContent, CardHeader, CardTitle } from '../../ui/card';
import { Badge } from '../../ui/badge';
import { Button } from '../../ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../../ui/tabs';
import { Progress } from '../../ui/progress';
import { 
  ArrowLeft,
  RefreshCcw,
  CheckCircle,
  AlertTriangle,
  Clock,
  Calendar,
  DollarSign,
  Users,
  Target,
  TrendingUp,
  Briefcase,
  FileText,
  Plus,
  Edit,
  Settings
} from 'lucide-react';

import MilestonesManager from './MilestonesManager';
import WBSManager from './WBSManager';
import ProjectForm from './ProjectForm';

const baseURL = process.env.REACT_APP_BACKEND_URL || import.meta.env.REACT_APP_BACKEND_URL;

const ProjectDashboard = () => {
  const { projectId } = useParams();
  const navigate = useNavigate();
  
  const [project, setProject] = useState(null);
  const [summary, setSummary] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [refreshing, setRefreshing] = useState(false);
  const [activeTab, setActiveTab] = useState('overview');
  const [editMode, setEditMode] = useState(false);

  useEffect(() => {
    fetchProjectData();
  }, [projectId]);

  const fetchProjectData = async () => {
    try {
      setLoading(true);
      const token = localStorage.getItem('token');
      
      // Fetch project details and summary in parallel
      const [projectResponse, summaryResponse] = await Promise.all([
        axios.get(`${baseURL}/api/sd/projects/${projectId}`, {
          headers: { Authorization: `Bearer ${token}` }
        }),
        axios.get(`${baseURL}/api/sd/projects/${projectId}/summary`, {
          headers: { Authorization: `Bearer ${token}` }
        })
      ]);
      
      setProject(projectResponse.data);
      setSummary(summaryResponse.data);
      setError(null);
    } catch (error) {
      console.error('Error fetching project data:', error);
      setError('Failed to fetch project data');
    } finally {
      setLoading(false);
    }
  };

  const handleRefresh = async () => {
    setRefreshing(true);
    await fetchProjectData();
    setRefreshing(false);
  };

  const handleProjectUpdate = async () => {
    setEditMode(false);
    await fetchProjectData();
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

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="flex items-center gap-4">
          <Button variant="ghost" onClick={() => navigate('/sd/projects')}>
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back to Projects
          </Button>
          <h1 className="text-3xl font-bold text-gray-900">Project Dashboard</h1>
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
          <Button variant="ghost" onClick={() => navigate('/sd/projects')}>
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back to Projects
          </Button>
          <h1 className="text-3xl font-bold text-gray-900">Project Dashboard</h1>
        </div>
        <Card>
          <CardContent className="p-6">
            <div className="text-center">
              <AlertTriangle className="mx-auto h-12 w-12 text-red-500" />
              <h3 className="mt-2 text-lg font-medium text-gray-900">Error Loading Project</h3>
              <p className="mt-1 text-gray-500">{error}</p>
              <Button onClick={fetchProjectData} className="mt-4">
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
          <Button variant="ghost" onClick={() => navigate('/sd/projects')}>
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back to Projects
          </Button>
          <div>
            <h1 className="text-3xl font-bold text-gray-900">{project?.name}</h1>
            <div className="flex items-center gap-4 mt-1">
              <code className="text-sm bg-gray-100 px-2 py-1 rounded">
                {project?.project_id}
              </code>
              {getStatusBadge(project?.status)}
              {getPhaseBadge(project?.phase)}
            </div>
          </div>
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
            onClick={() => setEditMode(!editMode)}
            variant={editMode ? "default" : "outline"}
          >
            <Edit className="w-4 h-4 mr-2" />
            {editMode ? 'Cancel Edit' : 'Edit Project'}
          </Button>
        </div>
      </div>

      {/* Project Overview Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Budget</p>
                <p className="text-2xl font-bold text-green-600">
                  {formatCurrency(project?.budget || 0)}
                </p>
                <p className="text-xs text-gray-500 mt-1">
                  Spent: {formatCurrency(project?.actual_cost || 0)}
                </p>
              </div>
              <DollarSign className="h-8 w-8 text-green-500" />
            </div>
            <div className="mt-4">
              <Progress 
                value={project?.budget ? (project.actual_cost / project.budget * 100) : 0} 
                className="h-2"
              />
              <p className="text-xs text-gray-500 mt-1">
                {project?.budget ? Math.round((project.actual_cost / project.budget * 100)) : 0}% utilized
              </p>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Progress</p>
                <p className="text-2xl font-bold text-blue-600">
                  {Math.round(project?.overall_progress || 0)}%
                </p>
                <p className="text-xs text-gray-500 mt-1">
                  Overall completion
                </p>
              </div>
              <TrendingUp className="h-8 w-8 text-blue-500" />
            </div>
            <div className="mt-4">
              <Progress 
                value={project?.overall_progress || 0} 
                className="h-2"
              />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Milestones</p>
                <p className="text-2xl font-bold text-purple-600">
                  {summary?.completed_milestones || 0}/{summary?.milestones_count || 0}
                </p>
                <p className="text-xs text-gray-500 mt-1">
                  {summary?.overdue_milestones || 0} overdue
                </p>
              </div>
              <Target className="h-8 w-8 text-purple-500" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Tasks</p>
                <p className="text-2xl font-bold text-orange-600">
                  {summary?.completed_tasks || 0}/{summary?.tasks_count || 0}
                </p>
                <p className="text-xs text-gray-500 mt-1">
                  {summary?.overdue_tasks || 0} overdue
                </p>
              </div>
              <FileText className="h-8 w-8 text-orange-500" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Main Content Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-6">
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="milestones">Milestones</TabsTrigger>
          <TabsTrigger value="tasks">Tasks (WBS)</TabsTrigger>
          <TabsTrigger value="settings">Settings</TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Project Details */}
            <Card>
              <CardHeader>
                <CardTitle>Project Details</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div>
                  <label className="text-sm font-medium text-gray-600">Customer</label>
                  <p className="text-lg font-semibold text-gray-900">{project?.customer_name}</p>
                </div>
                <div>
                  <label className="text-sm font-medium text-gray-600">Description</label>
                  <p className="text-gray-700">{project?.description || 'No description provided'}</p>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="text-sm font-medium text-gray-600">Start Date</label>
                    <p className="text-gray-900">{formatDate(project?.start_date)}</p>
                  </div>
                  <div>
                    <label className="text-sm font-medium text-gray-600">End Date</label>
                    <p className="text-gray-900">{formatDate(project?.end_date)}</p>
                  </div>
                </div>
                <div>
                  <label className="text-sm font-medium text-gray-600">Priority</label>
                  <Badge variant="outline" className="ml-2">
                    {project?.priority || 'Medium'}
                  </Badge>
                </div>
                {project?.tags && project.tags.length > 0 && (
                  <div>
                    <label className="text-sm font-medium text-gray-600">Tags</label>
                    <div className="flex flex-wrap gap-2 mt-1">
                      {project.tags.map((tag, index) => (
                        <Badge key={index} variant="secondary" className="text-xs">
                          {tag}
                        </Badge>
                      ))}
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Team & Timeline */}
            <Card>
              <CardHeader>
                <CardTitle>Team & Timeline</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div>
                  <label className="text-sm font-medium text-gray-600">Team Size</label>
                  <div className="flex items-center gap-2 mt-1">
                    <Users className="w-4 h-4 text-gray-500" />
                    <span className="text-lg font-semibold">{summary?.team_size || 0} members</span>
                  </div>
                </div>
                <div>
                  <label className="text-sm font-medium text-gray-600">Schedule Variance</label>
                  <div className="flex items-center gap-2 mt-1">
                    <Calendar className="w-4 h-4 text-gray-500" />
                    <span className={`text-lg font-semibold ${
                      (summary?.schedule_variance || 0) > 0 ? 'text-red-600' : 'text-green-600'
                    }`}>
                      {summary?.schedule_variance > 0 ? '+' : ''}{Math.round(summary?.schedule_variance || 0)}%
                    </span>
                  </div>
                </div>
                <div>
                  <label className="text-sm font-medium text-gray-600">Budget Utilization</label>
                  <div className="flex items-center gap-2 mt-1">
                    <DollarSign className="w-4 h-4 text-gray-500" />
                    <span className={`text-lg font-semibold ${
                      (summary?.budget_utilization || 0) > 80 ? 'text-red-600' : 'text-green-600'
                    }`}>
                      {Math.round(summary?.budget_utilization || 0)}%
                    </span>
                  </div>
                </div>
                
                {project?.notes && (
                  <div>
                    <label className="text-sm font-medium text-gray-600">Notes</label>
                    <p className="text-sm text-gray-700 bg-gray-50 p-3 rounded mt-1">
                      {project.notes}
                    </p>
                  </div>
                )}
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="milestones">
          <MilestonesManager projectId={projectId} />
        </TabsContent>

        <TabsContent value="tasks">
          <WBSManager projectId={projectId} />
        </TabsContent>

        <TabsContent value="settings">
          {editMode ? (
            <ProjectForm 
              project={project} 
              onSave={handleProjectUpdate}
              onCancel={() => setEditMode(false)}
            />
          ) : (
            <Card>
              <CardHeader>
                <CardTitle>Project Settings</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-gray-600 mb-4">
                  Configure project settings and advanced options.
                </p>
                <Button onClick={() => setEditMode(true)}>
                  <Settings className="w-4 h-4 mr-2" />
                  Edit Project Settings
                </Button>
              </CardContent>
            </Card>
          )}
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default ProjectDashboard;