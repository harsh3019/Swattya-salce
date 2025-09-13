import React from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { 
  Package, 
  Tags, 
  CreditCard, 
  Calculator,
  Plus,
  Settings,
  Database
} from 'lucide-react';
import { useNavigate } from 'react-router-dom';

const MasterDataDashboard = () => {
  const navigate = useNavigate();

  const masterDataModules = [
    {
      id: 'primary-categories',
      title: 'Primary Categories',
      description: 'Manage product categories and classification',
      icon: Tags,
      color: 'bg-blue-500',
      path: '/master-data/primary-categories',
      stats: 'Categories'
    },
    {
      id: 'products',
      title: 'Products',
      description: 'Manage products with SQU codes and specifications',
      icon: Package,
      color: 'bg-green-500',
      path: '/master-data/products',
      stats: 'Products'
    },
    {
      id: 'rate-cards',
      title: 'Rate Cards',
      description: 'Manage pricing rate cards and pricing tiers',
      icon: CreditCard,
      color: 'bg-purple-500',
      path: '/master-data/rate-cards',
      stats: 'Rate Cards'
    },
    {
      id: 'purchase-costs',
      title: 'Purchase Costs',
      description: 'Manage product purchase costs and margins',
      icon: Calculator,
      color: 'bg-orange-500',
      path: '/master-data/purchase-costs',
      stats: 'Cost Records'
    }
  ];

  return (
    <div className="container mx-auto p-6">
      {/* Header */}
      <div className="mb-8">
        <div className="flex items-center gap-3 mb-2">
          <Database className="w-8 h-8 text-blue-600" />
          <h1 className="text-3xl font-bold text-gray-900">Master Data Management</h1>
        </div>
        <p className="text-gray-600">
          Manage all master data including categories, products, pricing, and costs
        </p>
      </div>

      {/* Quick Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
        {masterDataModules.map((module) => {
          const IconComponent = module.icon;
          return (
            <Card key={module.id} className="hover:shadow-lg transition-shadow cursor-pointer">
              <CardHeader className="pb-3">
                <div className="flex items-center justify-between">
                  <div className={`p-2 rounded-lg ${module.color} bg-opacity-10`}>
                    <IconComponent className={`w-6 h-6 ${module.color.replace('bg-', 'text-')}`} />
                  </div>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => navigate(module.path)}
                  >
                    <Settings className="w-4 h-4" />
                  </Button>
                </div>
                <CardTitle className="text-lg">{module.title}</CardTitle>
                <CardDescription className="text-sm">
                  {module.description}
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="flex items-center justify-between">
                  <span className="text-2xl font-bold text-gray-900">--</span>
                  <span className="text-sm text-gray-500">{module.stats}</span>
                </div>
              </CardContent>
            </Card>
          );
        })}
      </div>

      {/* Main Action Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {masterDataModules.map((module) => {
          const IconComponent = module.icon;
          return (
            <Card key={`${module.id}-action`} className="hover:shadow-lg transition-shadow">
              <CardHeader>
                <div className="flex items-center gap-3">
                  <div className={`p-3 rounded-lg ${module.color} bg-opacity-10`}>
                    <IconComponent className={`w-8 h-8 ${module.color.replace('bg-', 'text-')}`} />
                  </div>
                  <div>
                    <CardTitle className="text-xl">{module.title}</CardTitle>
                    <CardDescription>{module.description}</CardDescription>
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  <Button 
                    className="w-full" 
                    onClick={() => navigate(module.path)}
                  >
                    <Settings className="w-4 h-4 mr-2" />
                    Manage {module.title}
                  </Button>
                  <Button 
                    variant="outline" 
                    className="w-full"
                    onClick={() => navigate(`${module.path}/new`)}
                  >
                    <Plus className="w-4 h-4 mr-2" />
                    Add New
                  </Button>
                </div>
              </CardContent>
            </Card>
          );
        })}
      </div>

      {/* Help Section */}
      <Card className="mt-8 bg-blue-50 border-blue-200">
        <CardHeader>
          <CardTitle className="text-blue-900">Getting Started</CardTitle>
          <CardDescription className="text-blue-700">
            Quick guide to master data management
          </CardDescription>
        </CardHeader>
        <CardContent className="text-blue-800">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <h4 className="font-semibold mb-2">Setup Order:</h4>
              <ol className="list-decimal list-inside space-y-1 text-sm">
                <li>Create Primary Categories first</li>
                <li>Add Products with SQU codes</li>
                <li>Set up Rate Cards</li>
                <li>Configure Purchase Costs</li>
              </ol>
            </div>
            <div>
              <h4 className="font-semibold mb-2">Key Features:</h4>
              <ul className="list-disc list-inside space-y-1 text-sm">
                <li>Bulk import/export capabilities</li>
                <li>Automated SQU code generation</li>
                <li>Multi-tier pricing support</li>
                <li>Margin calculation tools</li>
              </ul>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default MasterDataDashboard;