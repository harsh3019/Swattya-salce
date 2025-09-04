import React from 'react';
import { Badge } from './ui/badge';
import { Label } from './ui/label';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from './ui/dialog';
import { useCRUD, DataTable } from './UserManagement';
import * as z from 'zod';

// Activity logs are read-only, so no schema validation needed for forms
const activityLogSchema = z.object({});

export const ActivityLogs = () => {
  const crud = useCRUD('activity-logs', activityLogSchema);

  const getStatusBadge = (status) => {
    return (
      <Badge variant={status === 'success' ? 'default' : 'destructive'}>
        {status}
      </Badge>
    );
  };

  const getActionBadge = (action) => {
    const colors = {
      create: 'default',
      read: 'secondary',
      update: 'outline',
      delete: 'destructive',
      login: 'default',
      logout: 'secondary'
    };
    
    return (
      <Badge variant={colors[action] || 'secondary'}>
        {action}
      </Badge>
    );
  };

  const columns = [
    { 
      key: 'created_at', 
      label: 'Timestamp', 
      sortable: true,
      render: (item) => new Date(item.created_at).toLocaleString()
    },
    { key: 'module_name', label: 'Module', sortable: true },
    { key: 'table_name', label: 'Table', sortable: true },
    { 
      key: 'action', 
      label: 'Action', 
      sortable: true,
      render: (item) => getActionBadge(item.action)
    },
    { 
      key: 'status', 
      label: 'Status', 
      sortable: true,
      render: (item) => getStatusBadge(item.status)
    },
    { key: 'user_id', label: 'User ID', sortable: true },
    { key: 'ip', label: 'IP Address', sortable: true }
  ];

  // Override the add functionality since activity logs are read-only
  const handleAdd = () => {
    alert('Activity logs are read-only and cannot be created manually.');
  };

  // Override delete functionality since activity logs should be immutable
  const handleDelete = () => {
    alert('Activity logs are immutable and cannot be deleted.');
  };

  return (
    <div className="space-y-6">
      <DataTable
        data={crud.data}
        columns={columns}
        loading={crud.loading}
        error={crud.error}
        searchTerm={crud.searchTerm}
        setSearchTerm={crud.setSearchTerm}
        sortField={crud.sortField}
        sortDirection={crud.sortDirection}
        currentPage={crud.currentPage}
        setCurrentPage={crud.setCurrentPage}
        totalPages={crud.totalPages}
        onSort={crud.handleSort}
        onExport={crud.exportToCSV}
        onView={crud.openViewDialog}
        onEdit={() => alert('Activity logs cannot be edited.')}
        onDelete={handleDelete}
        onAdd={handleAdd}
        title="Activity Logs"
        modulePath="/activity-logs"
      />

      {/* View Dialog */}
      <Dialog open={!!crud.viewingItem} onOpenChange={() => crud.setViewingItem(null)}>
        <DialogContent className="max-w-lg">
          <DialogHeader>
            <DialogTitle>Activity Log Details</DialogTitle>
          </DialogHeader>
          {crud.viewingItem && (
            <div className="space-y-3">
              <div>
                <Label className="font-medium">Timestamp:</Label>
                <p className="text-sm text-gray-600">
                  {new Date(crud.viewingItem.created_at).toLocaleString()}
                </p>
              </div>
              <div>
                <Label className="font-medium">Module:</Label>
                <p className="text-sm text-gray-600">{crud.viewingItem.module_name}</p>
              </div>
              <div>
                <Label className="font-medium">Table:</Label>
                <p className="text-sm text-gray-600">{crud.viewingItem.table_name}</p>
              </div>
              <div>
                <Label className="font-medium">Action:</Label>
                {getActionBadge(crud.viewingItem.action)}
              </div>
              <div>
                <Label className="font-medium">Status:</Label>
                {getStatusBadge(crud.viewingItem.status)}
              </div>
              <div>
                <Label className="font-medium">User ID:</Label>
                <p className="text-sm text-gray-600">{crud.viewingItem.user_id || 'System'}</p>
              </div>
              <div>
                <Label className="font-medium">IP Address:</Label>
                <p className="text-sm text-gray-600">{crud.viewingItem.ip || 'N/A'}</p>
              </div>
              <div>
                <Label className="font-medium">User Agent:</Label>
                <p className="text-sm text-gray-600 break-all">
                  {crud.viewingItem.user_agent || 'N/A'}
                </p>
              </div>
              {crud.viewingItem.details && (
                <div>
                  <Label className="font-medium">Details:</Label>
                  <pre className="text-xs text-gray-600 bg-gray-50 p-2 rounded mt-1 overflow-auto max-h-32">
                    {JSON.stringify(crud.viewingItem.details, null, 2)}
                  </pre>
                </div>
              )}
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
};