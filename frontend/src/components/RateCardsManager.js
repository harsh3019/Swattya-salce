import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Label } from './ui/label';
import { Textarea } from './ui/textarea';
import { Badge } from './ui/badge';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from './ui/dialog';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from './ui/table';
import { 
  Plus, 
  Edit, 
  Trash2, 
  CreditCard, 
  Search,
  Filter,
  Download,
  Upload,
  AlertCircle,
  CheckCircle,
  Calendar,
  DollarSign
} from 'lucide-react';
import axios from 'axios';

const RateCardsManager = () => {
  const [rateCards, setRateCards] = useState([]);
  const [loading, setLoading] = useState(true);
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [isEditing, setIsEditing] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [formData, setFormData] = useState({
    rate_card_name: '',
    rate_card_code: '',
    effective_from: '',
    effective_to: '',
    description: '',
    is_active: true
  });
  const [errors, setErrors] = useState({});
  const [saving, setSaving] = useState(false);

  const baseURL = process.env.REACT_APP_BACKEND_URL;

  useEffect(() => {
    fetchRateCards();
  }, []);

  const fetchRateCards = async () => {
    try {
      setLoading(true);
      const token = localStorage.getItem('token');
      const response = await axios.get(`${baseURL}/api/mst/rate-cards`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setRateCards(response.data || []);
    } catch (error) {
      console.error('Error fetching rate cards:', error);
      alert('Error fetching rate cards. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleInputChange = (field, value) => {
    setFormData(prev => ({
      ...prev,
      [field]: value
    }));
    
    // Auto-generate rate card code from name
    if (field === 'rate_card_name' && !isEditing) {
      const code = value.split(' ').map(word => word.charAt(0).toUpperCase()).join('').substring(0, 6);
      const year = new Date().getFullYear();
      setFormData(prev => ({
        ...prev,
        rate_card_code: `${code}-${year}`
      }));
    }
    
    // Clear error when user starts typing
    if (errors[field]) {
      setErrors(prev => ({
        ...prev,
        [field]: ''
      }));
    }
  };

  const validateForm = () => {
    const newErrors = {};
    
    if (!formData.rate_card_name.trim()) {
      newErrors.rate_card_name = 'Rate card name is required';
    }
    
    if (!formData.rate_card_code.trim()) {
      newErrors.rate_card_code = 'Rate card code is required';
    }
    
    if (!formData.effective_from) {
      newErrors.effective_from = 'Effective from date is required';
    }
    
    if (!formData.effective_to) {
      newErrors.effective_to = 'Effective to date is required';
    }
    
    // Check date range
    if (formData.effective_from && formData.effective_to) {
      const fromDate = new Date(formData.effective_from);
      const toDate = new Date(formData.effective_to);
      if (fromDate >= toDate) {
        newErrors.effective_to = 'Effective to date must be after effective from date';
      }
    }
    
    // Check for duplicate code
    const existingCard = rateCards.find(card => 
      card.rate_card_code?.toLowerCase() === formData.rate_card_code.toLowerCase() &&
      (!isEditing || card.id !== formData.id)
    );
    if (existingCard) {
      newErrors.rate_card_code = 'Rate card code already exists';
    }
    
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!validateForm()) {
      return;
    }
    
    setSaving(true);
    try {
      const token = localStorage.getItem('token');
      const url = isEditing 
        ? `${baseURL}/api/mst/rate-cards/${formData.id}`
        : `${baseURL}/api/mst/rate-cards`;
      
      const method = isEditing ? 'put' : 'post';
      
      await axios[method](url, formData, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      alert(`Rate card ${isEditing ? 'updated' : 'created'} successfully!`);
      setIsDialogOpen(false);
      resetForm();
      fetchRateCards();
    } catch (error) {
      console.error('Error saving rate card:', error);
      const errorMessage = error.response?.data?.detail || 'Error saving rate card. Please try again.';
      alert(errorMessage);
    } finally {
      setSaving(false);
    }
  };

  const handleEdit = (rateCard) => {
    const formatDate = (dateStr) => {
      if (!dateStr) return '';
      const date = new Date(dateStr);
      return date.toISOString().split('T')[0];
    };

    setFormData({
      id: rateCard.id,
      rate_card_name: rateCard.rate_card_name || '',
      rate_card_code: rateCard.rate_card_code || '',
      effective_from: formatDate(rateCard.effective_from),
      effective_to: formatDate(rateCard.effective_to),
      description: rateCard.description || '',
      is_active: rateCard.is_active !== false
    });
    setIsEditing(true);
    setIsDialogOpen(true);
  };

  const handleDelete = async (rateCard) => {
    if (!window.confirm(`Are you sure you want to delete "${rateCard.rate_card_name}"?`)) {
      return;
    }
    
    try {
      const token = localStorage.getItem('token');
      await axios.delete(`${baseURL}/api/mst/rate-cards/${rateCard.id}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      alert('Rate card deleted successfully!');
      fetchRateCards();
    } catch (error) {
      console.error('Error deleting rate card:', error);
      alert('Error deleting rate card. Please try again.');
    }
  };

  const resetForm = () => {
    setFormData({
      rate_card_name: '',
      rate_card_code: '',
      effective_from: '',
      effective_to: '',
      description: '',
      is_active: true
    });
    setIsEditing(false);
    setErrors({});
  };

  const openNewDialog = () => {
    resetForm();
    // Set default dates
    const now = new Date();
    const nextYear = new Date(now.getFullYear() + 1, 11, 31); // Dec 31 next year
    setFormData(prev => ({
      ...prev,
      effective_from: now.toISOString().split('T')[0],
      effective_to: nextYear.toISOString().split('T')[0]
    }));
    setIsDialogOpen(true);
  };

  const isCardActive = (rateCard) => {
    if (!rateCard.is_active) return false;
    const now = new Date();
    const from = new Date(rateCard.effective_from);
    const to = new Date(rateCard.effective_to);
    return now >= from && now <= to;
  };

  const formatDate = (dateStr) => {
    if (!dateStr) return 'N/A';
    return new Date(dateStr).toLocaleDateString();
  };

  const filteredRateCards = rateCards.filter(card =>
    card.rate_card_name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
    card.rate_card_code?.toLowerCase().includes(searchTerm.toLowerCase()) ||
    card.description?.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div className="container mx-auto p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <CreditCard className="w-8 h-8 text-purple-600" />
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Rate Cards</h1>
            <p className="text-gray-600">Manage pricing rate cards and pricing tiers</p>
          </div>
        </div>
        <Button onClick={openNewDialog} className="flex items-center gap-2">
          <Plus className="w-4 h-4" />
          Add Rate Card
        </Button>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-6">
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Total Rate Cards</p>
                <p className="text-2xl font-bold text-gray-900">{rateCards.length}</p>
              </div>
              <CreditCard className="w-8 h-8 text-purple-500" />
            </div>
          </CardContent>
        </Card>
        
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Active Now</p>
                <p className="text-2xl font-bold text-green-600">
                  {rateCards.filter(card => isCardActive(card)).length}
                </p>
              </div>
              <CheckCircle className="w-8 h-8 text-green-500" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Expiring Soon</p>
                <p className="text-2xl font-bold text-orange-600">
                  {rateCards.filter(card => {
                    const to = new Date(card.effective_to);
                    const now = new Date();
                    const thirtyDaysFromNow = new Date();
                    thirtyDaysFromNow.setDate(now.getDate() + 30);
                    return isCardActive(card) && to <= thirtyDaysFromNow;
                  }).length}
                </p>
              </div>
              <Calendar className="w-8 h-8 text-orange-500" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">This Year</p>
                <p className="text-2xl font-bold text-blue-600">
                  {rateCards.filter(card => {
                    const year = new Date().getFullYear();
                    const from = new Date(card.effective_from);
                    return from.getFullYear() === year;
                  }).length}
                </p>
              </div>
              <Calendar className="w-8 h-8 text-blue-500" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Search and Filters */}
      <Card className="mb-6">
        <CardHeader>
          <CardTitle>Search & Filters</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex flex-col md:flex-row gap-4">
            <div className="flex-1">
              <div className="relative">
                <Search className="absolute left-3 top-3 h-4 w-4 text-gray-400" />
                <Input
                  placeholder="Search rate cards by name, code, or description..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="pl-10"
                />
              </div>
            </div>
            <div className="flex gap-2">
              <Button variant="outline" size="sm">
                <Filter className="w-4 h-4 mr-2" />
                Filter
              </Button>
              <Button variant="outline" size="sm">
                <Download className="w-4 h-4 mr-2" />
                Export
              </Button>
              <Button variant="outline" size="sm">
                <Upload className="w-4 h-4 mr-2" />
                Import
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Rate Cards Table */}
      <Card>
        <CardHeader>
          <CardTitle>Rate Cards List ({filteredRateCards.length})</CardTitle>
          <CardDescription>
            Manage all pricing rate cards and their validity periods
          </CardDescription>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="flex justify-center py-8">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-purple-600"></div>
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Rate Card Name</TableHead>
                  <TableHead>Code</TableHead>
                  <TableHead className="hidden md:table-cell">Effective From</TableHead>
                  <TableHead className="hidden md:table-cell">Effective To</TableHead>
                  <TableHead className="hidden lg:table-cell">Description</TableHead>
                  <TableHead className="hidden sm:table-cell">Status</TableHead>
                  <TableHead className="text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {filteredRateCards.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={7} className="text-center py-8 text-gray-500">
                      {searchTerm ? 'No rate cards found matching your search.' : 'No rate cards found. Create your first rate card!'}
                    </TableCell>
                  </TableRow>
                ) : (
                  filteredRateCards.map((rateCard) => (
                    <TableRow key={rateCard.id}>
                      <TableCell className="font-medium">
                        <div>
                          <div className="font-medium">{rateCard.rate_card_name}</div>
                          {rateCard.description && (
                            <div className="text-sm text-gray-500 truncate max-w-xs">
                              {rateCard.description}
                            </div>
                          )}
                        </div>
                      </TableCell>
                      <TableCell>
                        <Badge variant="outline" className="font-mono text-xs">
                          {rateCard.rate_card_code}
                        </Badge>
                      </TableCell>
                      <TableCell className="hidden md:table-cell text-sm">
                        {formatDate(rateCard.effective_from)}
                      </TableCell>
                      <TableCell className="hidden md:table-cell text-sm">
                        {formatDate(rateCard.effective_to)}
                      </TableCell>
                      <TableCell className="hidden lg:table-cell max-w-xs truncate text-sm">
                        {rateCard.description || 'No description'}
                      </TableCell>
                      <TableCell className="hidden sm:table-cell">
                        {isCardActive(rateCard) ? (
                          <Badge variant="success">Active</Badge>
                        ) : rateCard.is_active ? (
                          <Badge variant="secondary">Scheduled</Badge>
                        ) : (
                          <Badge variant="destructive">Inactive</Badge>
                        )}
                      </TableCell>
                      <TableCell className="text-right">
                        <div className="flex justify-end gap-2">
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => handleEdit(rateCard)}
                          >
                            <Edit className="w-4 h-4" />
                          </Button>
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => handleDelete(rateCard)}
                            className="text-red-600 hover:text-red-700"
                          >
                            <Trash2 className="w-4 h-4" />
                          </Button>
                        </div>
                      </TableCell>
                    </TableRow>
                  ))
                )}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>

      {/* Add/Edit Dialog */}
      <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
        <DialogContent className="sm:max-w-[500px]">
          <DialogHeader>
            <DialogTitle>
              {isEditing ? 'Edit Rate Card' : 'Add New Rate Card'}
            </DialogTitle>
            <DialogDescription>
              {isEditing 
                ? 'Update the rate card information below.' 
                : 'Create a new rate card for pricing management.'
              }
            </DialogDescription>
          </DialogHeader>
          
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="grid gap-4">
              <div>
                <Label htmlFor="rate_card_name">Rate Card Name *</Label>
                <Input
                  id="rate_card_name"
                  value={formData.rate_card_name}
                  onChange={(e) => handleInputChange('rate_card_name', e.target.value)}
                  placeholder="e.g., Standard Pricing 2024"
                  className={errors.rate_card_name ? 'border-red-500' : ''}
                />
                {errors.rate_card_name && (
                  <p className="text-sm text-red-500 mt-1">{errors.rate_card_name}</p>
                )}
              </div>

              <div>
                <Label htmlFor="rate_card_code">Rate Card Code *</Label>
                <Input
                  id="rate_card_code"
                  value={formData.rate_card_code}
                  onChange={(e) => handleInputChange('rate_card_code', e.target.value.toUpperCase())}
                  placeholder="e.g., STD-2024"
                  className={`font-mono ${errors.rate_card_code ? 'border-red-500' : ''}`}
                />
                {errors.rate_card_code && (
                  <p className="text-sm text-red-500 mt-1">{errors.rate_card_code}</p>
                )}
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label htmlFor="effective_from">Effective From *</Label>
                  <Input
                    id="effective_from"
                    type="date"
                    value={formData.effective_from}
                    onChange={(e) => handleInputChange('effective_from', e.target.value)}
                    className={errors.effective_from ? 'border-red-500' : ''}
                  />
                  {errors.effective_from && (
                    <p className="text-sm text-red-500 mt-1">{errors.effective_from}</p>
                  )}
                </div>

                <div>
                  <Label htmlFor="effective_to">Effective To *</Label>
                  <Input
                    id="effective_to"
                    type="date"
                    value={formData.effective_to}
                    onChange={(e) => handleInputChange('effective_to', e.target.value)}
                    className={errors.effective_to ? 'border-red-500' : ''}
                  />
                  {errors.effective_to && (
                    <p className="text-sm text-red-500 mt-1">{errors.effective_to}</p>
                  )}
                </div>
              </div>

              <div>
                <Label htmlFor="description">Description</Label>
                <Textarea
                  id="description"
                  value={formData.description}
                  onChange={(e) => handleInputChange('description', e.target.value)}
                  placeholder="Describe this rate card..."
                  rows={3}
                />
              </div>

              <div className="flex items-center space-x-2">
                <input
                  type="checkbox"
                  id="is_active"
                  checked={formData.is_active}
                  onChange={(e) => handleInputChange('is_active', e.target.checked)}
                  className="w-4 h-4 text-purple-600"
                />
                <Label htmlFor="is_active">Active</Label>
              </div>
            </div>

            <DialogFooter>
              <Button
                type="button"
                variant="outline"
                onClick={() => setIsDialogOpen(false)}
                disabled={saving}
              >
                Cancel
              </Button>
              <Button type="submit" disabled={saving}>
                {saving ? 'Saving...' : (isEditing ? 'Update' : 'Create')}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default RateCardsManager;