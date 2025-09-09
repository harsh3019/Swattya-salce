import React, { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Badge } from '@/components/ui/badge';
import { Textarea } from '@/components/ui/textarea';
import { Label } from '@/components/ui/label';
import { ArrowRight, ChevronRight, Target, MessageSquare } from 'lucide-react';
import axios from 'axios';

const StageManagement = ({ 
  opportunity, 
  stages, 
  currentStage, 
  onStageUpdate,
  onClose 
}) => {
  const [selectedStageId, setSelectedStageId] = useState('');
  const [notes, setNotes] = useState('');
  const [updating, setUpdating] = useState(false);

  const baseURL = process.env.REACT_APP_BACKEND_URL;

  const getStageBadgeColor = (stageCode) => {
    const colors = {
      'L1': 'bg-slate-100 text-slate-800 border-slate-200',
      'L2': 'bg-blue-100 text-blue-800 border-blue-200',
      'L3': 'bg-indigo-100 text-indigo-800 border-indigo-200',
      'L4': 'bg-purple-100 text-purple-800 border-purple-200',
      'L5': 'bg-pink-100 text-pink-800 border-pink-200',
      'L6': 'bg-orange-100 text-orange-800 border-orange-200',
      'L7': 'bg-yellow-100 text-yellow-800 border-yellow-200',
      'L8': 'bg-green-100 text-green-800 border-green-200'
    };
    return colors[stageCode] || 'bg-gray-100 text-gray-800 border-gray-200';
  };

  const getStageInfo = (stageId) => {
    const stage = stages.find(s => s.id === stageId);
    return stage ? { 
      name: stage.stage_name, 
      code: stage.stage_code,
      order: stage.stage_order 
    } : null;
  };

  const handleStageUpdate = async () => {
    if (!selectedStageId) return;

    try {
      setUpdating(true);
      const token = localStorage.getItem('token');

      const updateData = {
        stage_id: selectedStageId,
        stage_change_notes: notes
      };

      await axios.patch(`${baseURL}/api/opportunities/${opportunity.id}/stage`, updateData, {
        headers: { Authorization: `Bearer ${token}` }
      });

      onStageUpdate();
      onClose();
    } catch (error) {
      console.error('Error updating stage:', error);
      alert('Failed to update stage. Please try again.');
    } finally {
      setUpdating(false);
    }
  };

  const selectedStage = getStageInfo(selectedStageId);
  const canMoveForward = selectedStage && selectedStage.order > currentStage.order;
  const canMoveBackward = selectedStage && selectedStage.order < currentStage.order;

  return (
    <div className="space-y-6">
      <div>
        <h3 className="text-lg font-semibold text-gray-900 mb-2">Change Stage</h3>
        <p className="text-sm text-gray-600">
          Move this opportunity to a different stage in the L1-L8 pipeline
        </p>
      </div>

      {/* Current Stage */}
      <Card className="border-blue-200 bg-blue-50">
        <CardHeader className="pb-3">
          <CardTitle className="text-sm text-blue-900">Current Stage</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center gap-3">
            <Badge variant="outline" className={getStageBadgeColor(currentStage.code)}>
              {currentStage.code}
            </Badge>
            <div>
              <p className="font-medium text-blue-900">{currentStage.name}</p>
              <p className="text-xs text-blue-700">Stage {currentStage.order} of 8</p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Stage Selection */}
      <div>
        <Label htmlFor="stage_select">Select New Stage</Label>
        <Select value={selectedStageId} onValueChange={setSelectedStageId}>
          <SelectTrigger className="mt-1">
            <SelectValue placeholder="Choose a stage to move to..." />
          </SelectTrigger>
          <SelectContent>
            {stages
              .sort((a, b) => a.stage_order - b.stage_order)
              .map((stage) => (
                <SelectItem 
                  key={stage.id} 
                  value={stage.id}
                  disabled={stage.id === opportunity.stage_id}
                >
                  <div className="flex items-center gap-2">
                    <Badge 
                      variant="outline" 
                      className={`${getStageBadgeColor(stage.stage_code)} text-xs`}
                    >
                      {stage.stage_code}
                    </Badge>
                    <span>{stage.stage_name}</span>
                    {stage.id === opportunity.stage_id && (
                      <span className="text-xs text-gray-500">(Current)</span>
                    )}
                  </div>
                </SelectItem>
              ))}
          </SelectContent>
        </Select>
      </div>

      {/* Stage Preview */}
      {selectedStageId && selectedStage && (
        <Card className={`border-2 ${
          canMoveForward 
            ? 'border-green-200 bg-green-50' 
            : canMoveBackward 
              ? 'border-yellow-200 bg-yellow-50'
              : 'border-gray-200 bg-gray-50'
        }`}>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm flex items-center gap-2">
              <Target className="w-4 h-4" />
              Stage Change Preview
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <Badge variant="outline" className={getStageBadgeColor(currentStage.code)}>
                  {currentStage.code}
                </Badge>
                <span className="text-sm font-medium">{currentStage.name}</span>
              </div>
              
              <ArrowRight className={`w-5 h-5 ${
                canMoveForward 
                  ? 'text-green-600' 
                  : canMoveBackward 
                    ? 'text-yellow-600'
                    : 'text-gray-400'
              }`} />
              
              <div className="flex items-center gap-3">
                <Badge variant="outline" className={getStageBadgeColor(selectedStage.code)}>
                  {selectedStage.code}
                </Badge>
                <span className="text-sm font-medium">{selectedStage.name}</span>
              </div>
            </div>
            
            <div className="mt-3 text-xs">
              {canMoveForward && (
                <p className="text-green-700 bg-green-100 px-2 py-1 rounded">
                  ✓ Moving forward in pipeline (Stage {currentStage.order} → {selectedStage.order})
                </p>
              )}
              {canMoveBackward && (
                <p className="text-yellow-700 bg-yellow-100 px-2 py-1 rounded">
                  ⚠ Moving backward in pipeline (Stage {currentStage.order} → {selectedStage.order})
                </p>
              )}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Notes */}
      <div>
        <Label htmlFor="notes">Stage Change Notes</Label>
        <Textarea
          id="notes"
          placeholder="Add notes about this stage change (optional)..."
          value={notes}
          onChange={(e) => setNotes(e.target.value)}
          rows={3}
          className="mt-1"
        />
        <p className="text-xs text-gray-500 mt-1">
          These notes will be added to the opportunity's activity log
        </p>
      </div>

      {/* Pipeline Overview */}
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-sm">Pipeline Overview</CardTitle>
          <CardDescription className="text-xs">
            L1-L8 Sales Pipeline Stages
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex flex-wrap gap-2">
            {stages
              .sort((a, b) => a.stage_order - b.stage_order)
              .map((stage) => (
                <div key={stage.id} className="flex items-center gap-1">
                  <Badge 
                    variant="outline" 
                    className={`text-xs ${getStageBadgeColor(stage.stage_code)} ${
                      stage.id === opportunity.stage_id 
                        ? 'ring-2 ring-blue-400 ring-offset-1' 
                        : ''
                    } ${
                      stage.id === selectedStageId 
                        ? 'ring-2 ring-green-400 ring-offset-1' 
                        : ''
                    }`}
                  >
                    {stage.stage_code}
                  </Badge>
                  {stage.stage_order < 8 && (
                    <ChevronRight className="w-3 h-3 text-gray-400" />
                  )}
                </div>
              ))}
          </div>
          <div className="mt-3 text-xs text-gray-600">
            <p>🔵 Current Stage • 🟢 Selected Stage</p>
          </div>
        </CardContent>
      </Card>

      {/* Action Buttons */}
      <div className="flex gap-3 pt-4">
        <Button 
          onClick={handleStageUpdate}
          disabled={!selectedStageId || updating}
          className="flex-1 bg-blue-600 hover:bg-blue-700"
        >
          {updating ? 'Updating...' : `Move to ${selectedStage?.code || 'Stage'}`}
        </Button>
        <Button 
          variant="outline" 
          onClick={onClose}
          className="flex-1"
        >
          Cancel
        </Button>
      </div>
    </div>
  );
};

export default StageManagement;