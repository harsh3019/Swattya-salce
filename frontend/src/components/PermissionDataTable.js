import React from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from './ui/table';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Alert, AlertDescription } from './ui/alert';
import { 
  Plus, 
  Search, 
  Download, 
  Eye, 
  Edit2, 
  Trash2, 
  ChevronLeft,
  ChevronRight,
  ArrowUpDown,
  AlertCircle
} from 'lucide-react';
import { usePermissions } from '../contexts/PermissionContext';
import axios from 'axios';
import { toast } from 'sonner';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const PermissionDataTable = ({ 
  data, 
  columns, 
  loading, 
  error,
  searchTerm,
  setSearchTerm,
  sortField,
  sortDirection,
  currentPage,
  setCurrentPage,
  totalPages,
  onSort,
  onView,
  onEdit,
  onDelete,
  onAdd,
  title,
  modulePath = '',
  entityName = ''
}) => {
  const { canAdd, canEdit, canDelete, canView, hasPermission } = usePermissions();

  const handleExport = async () => {
    if (!hasPermission(modulePath, 'Export')) {
      toast.error('You do not have permission to export this data');
      return;
    }

    try {
      const endpoint = entityName ? `${entityName}/export` : `${modulePath.replace('/', '')}/export`;
      const response = await axios.get(`${API}/${endpoint}`);
      
      if (response.data.data && response.data.filename) {
        // Create and download CSV file
        const blob = new Blob([response.data.data], { type: 'text/csv' });
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = response.data.filename;
        a.click();
        window.URL.revokeObjectURL(url);
        
        toast.success('Data exported successfully');
      }
    } catch (error) {
      console.error('Export error:', error);
      toast.error(error.response?.data?.detail || 'Failed to export data');
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center p-8">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="text-2xl font-bold">{title}</CardTitle>
            <CardDescription>Manage {title.toLowerCase()}</CardDescription>
          </div>
          <div className="flex items-center space-x-2">
            {canAdd(modulePath) && (
              <Button onClick={onAdd} className="bg-blue-600 hover:bg-blue-700">
                <Plus className="w-4 h-4 mr-2" />
                Add {title.slice(0, -1)}
              </Button>
            )}
          </div>
        </div>
      </CardHeader>
      <CardContent>
        {error && (
          <Alert className="mb-4 border-red-200 bg-red-50">
            <AlertCircle className="h-4 w-4 text-red-600" />
            <AlertDescription className="text-red-800">{error}</AlertDescription>
          </Alert>
        )}

        {/* Search and Export */}
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center space-x-2">
            <div className="relative">
              <Search className="absolute left-2 top-2.5 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="Search..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pl-8 w-64"
              />
            </div>
          </div>
          {hasPermission(modulePath, 'Export') && (
            <Button
              variant="outline"
              onClick={handleExport}
              className="flex items-center space-x-2"
            >
              <Download className="w-4 h-4" />
              <span>Export CSV</span>
            </Button>
          )}
        </div>

        {/* Table */}
        <div className="rounded-md border">
          <Table>
            <TableHeader>
              <TableRow>
                {columns.map((column) => (
                  <TableHead
                    key={column.key}
                    className={column.sortable ? "cursor-pointer hover:bg-slate-50" : ""}
                    onClick={() => column.sortable && onSort(column.key)}
                  >
                    <div className="flex items-center space-x-1">
                      <span>{column.label}</span>
                      {column.sortable && (
                        <ArrowUpDown className="w-4 h-4" />
                      )}
                      {sortField === column.key && (
                        <span className="text-xs">
                          {sortDirection === 'asc' ? '↑' : '↓'}
                        </span>
                      )}
                    </div>
                  </TableHead>
                ))}
                {(canView(modulePath) || canEdit(modulePath) || canDelete(modulePath)) && (
                  <TableHead>Actions</TableHead>
                )}
              </TableRow>
            </TableHeader>
            <TableBody>
              {data.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={columns.length + 1} className="text-center py-8">
                    <div className="text-gray-500">
                      <p className="text-lg font-medium">No data found</p>
                      <p className="text-sm">
                        {canAdd(modulePath) 
                          ? "Add new items to get started"
                          : "No items available"
                        }
                      </p>
                    </div>
                  </TableCell>
                </TableRow>
              ) : (
                data.map((item) => (
                  <TableRow key={item.id}>
                    {columns.map((column) => (
                      <TableCell key={column.key}>
                        {column.render ? column.render(item) : item[column.key]}
                      </TableCell>
                    ))}
                    {(canView(modulePath) || canEdit(modulePath) || canDelete(modulePath)) && (
                      <TableCell>
                        <div className="flex items-center space-x-1">
                          {canView(modulePath) && (
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => onView(item)}
                              className="h-8 w-8 p-0"
                              title="View details"
                            >
                              <Eye className="w-4 h-4" />
                            </Button>
                          )}
                          {canEdit(modulePath) && (
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => onEdit(item)}
                              className="h-8 w-8 p-0"
                              title="Edit"
                            >
                              <Edit2 className="w-4 h-4" />
                            </Button>
                          )}
                          {canDelete(modulePath) && (
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => onDelete(item)}
                              className="h-8 w-8 p-0 text-red-600 hover:text-red-700 hover:bg-red-50"
                              title="Delete"
                            >
                              <Trash2 className="w-4 h-4" />
                            </Button>
                          )}
                        </div>
                      </TableCell>
                    )}
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </div>

        {/* Pagination */}
        {totalPages > 1 && (
          <div className="flex items-center justify-between mt-4">
            <div className="text-sm text-gray-500">
              Page {currentPage} of {totalPages}
            </div>
            <div className="flex items-center space-x-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => setCurrentPage(prev => Math.max(1, prev - 1))}
                disabled={currentPage === 1}
              >
                <ChevronLeft className="w-4 h-4" />
                Previous
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={() => setCurrentPage(prev => Math.min(totalPages, prev + 1))}
                disabled={currentPage === totalPages}
              >
                Next
                <ChevronRight className="w-4 h-4" />
              </Button>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
};

export default PermissionDataTable;