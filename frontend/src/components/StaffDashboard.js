import React, { useState, useEffect } from 'react';
import { useAuth } from '../App';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Badge } from '@/components/ui/badge';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Label } from '@/components/ui/label';
import { toast } from 'sonner';
import axios from 'axios';

const StaffDashboard = () => {
  const { user, logout } = useAuth();
  const [queueData, setQueueData] = useState([]);
  const [loading, setLoading] = useState(false);
  const [selectedToken, setSelectedToken] = useState(null);
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [showPriorityDialog, setShowPriorityDialog] = useState(false);
  const [analytics, setAnalytics] = useState(null);

  const [tokenForm, setTokenForm] = useState({
    patient_name: '',
    patient_phone: '',
    category: '',
    symptoms: ''
  });

  const [priorityForm, setPriorityForm] = useState({
    new_priority: '',
    token_id: ''
  });

  const categories = [
    { value: 'emergency', label: 'Emergency', priority: 1 },
    { value: 'urgent_medical', label: 'Urgent Medical', priority: 2 },
    { value: 'serious_condition', label: 'Serious Condition', priority: 3 },
    { value: 'regular_consultation', label: 'Regular Consultation', priority: 4 },
    { value: 'report_pickup', label: 'Report Pickup', priority: 5 },
    { value: 'report_consultation', label: 'Report Consultation', priority: 6 }
  ];

  const priorityLevels = [
    { value: 1, label: 'Critical', color: 'text-red-600' },
    { value: 2, label: 'High', color: 'text-orange-600' },
    { value: 3, label: 'Medium-High', color: 'text-yellow-600' },
    { value: 4, label: 'Medium-Low', color: 'text-blue-600' },
    { value: 5, label: 'Report Pickup', color: 'text-green-600' },
    { value: 6, label: 'Consultation', color: 'text-purple-600' }
  ];

  useEffect(() => {
    fetchQueue();
    fetchAnalytics();
    
    // Set up polling for real-time updates
    const interval = setInterval(() => {
      fetchQueue();
      fetchAnalytics();
    }, 30000); // Poll every 30 seconds

    return () => clearInterval(interval);
  }, []);

  const fetchQueue = async () => {
    try {
      const response = await axios.get('/queue');
      setQueueData(response.data.queue || []);
    } catch (error) {
      console.error('Error fetching queue:', error);
      toast.error('Failed to fetch queue data');
    }
  };

  const fetchAnalytics = async () => {
    try {
      const response = await axios.get('/analytics/dashboard');
      setAnalytics(response.data);
    } catch (error) {
      console.error('Error fetching analytics:', error);
    }
  };

  const handleCreateEmergencyToken = async (e) => {
    e.preventDefault();
    
    if (!tokenForm.patient_name || !tokenForm.patient_phone || !tokenForm.category) {
      toast.error('Please fill all required fields');
      return;
    }

    if (!/^\d{10}$/.test(tokenForm.patient_phone)) {
      toast.error('Phone number must be 10 digits');
      return;
    }

    setLoading(true);
    
    try {
      const response = await axios.post('/tokens', {
        ...tokenForm,
        patient_id: `staff_created_${Date.now()}` // Unique ID for staff-created tokens
      });
      
      toast.success('Emergency token created successfully!');
      setShowCreateForm(false);
      setTokenForm({ patient_name: '', patient_phone: '', category: '', symptoms: '' });
      fetchQueue();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to create token');
    } finally {
      setLoading(false);
    }
  };

  const handleCompleteToken = async (tokenId) => {
    try {
      await axios.put(`/tokens/${tokenId}/complete`);
      toast.success('Token marked as completed');
      fetchQueue();
      fetchAnalytics();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to complete token');
    }
  };

  const handleUpdatePriority = async (e) => {
    e.preventDefault();
    
    try {
      await axios.put(`/tokens/${priorityForm.token_id}/priority?new_priority=${priorityForm.new_priority}`);
      toast.success('Token priority updated successfully');
      setShowPriorityDialog(false);
      setPriorityForm({ new_priority: '', token_id: '' });
      fetchQueue();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to update priority');
    }
  };

  const openPriorityDialog = (token) => {
    setPriorityForm({ 
      new_priority: token.priority_level.toString(), 
      token_id: token.token_id 
    });
    setSelectedToken(token);
    setShowPriorityDialog(true);
  };

  const getPriorityBadge = (priority) => {
    const priorityConfig = {
      1: { label: 'CRITICAL', className: 'priority-critical' },
      2: { label: 'HIGH', className: 'priority-high' },
      3: { label: 'MEDIUM-HIGH', className: 'priority-medium-high' },
      4: { label: 'MEDIUM-LOW', className: 'priority-medium-low' },
      5: { label: 'REPORT PICKUP', className: 'priority-report-pickup' },
      6: { label: 'CONSULTATION', className: 'priority-consultation' }
    };
    
    const config = priorityConfig[priority] || priorityConfig[4];
    return <Badge className={`${config.className} font-semibold text-xs`}>{config.label}</Badge>;
  };

  const getEstimatedTime = () => {
    const now = new Date();
    const currentTime = now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    return currentTime;
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 via-white to-blue-50">
      {/* Header */}
      <div className="bg-white shadow-sm border-b border-gray-200">
        <div className="container mx-auto px-4 py-4">
          <div className="flex justify-between items-center">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">Staff Dashboard</h1>
              <p className="text-gray-600">Manage hospital queue and patient tokens</p>
            </div>
            <div className="flex items-center space-x-4">
              <span className="text-sm text-gray-500">Last updated: {getEstimatedTime()}</span>
              <Button
                onClick={() => {
                  fetchQueue();
                  fetchAnalytics();
                  toast.success('Data refreshed');
                }}
                variant="outline"
                size="sm"
                data-testid="refresh-btn"
              >
                <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                </svg>
                Refresh
              </Button>
              <Button onClick={logout} variant="outline" size="sm" data-testid="logout-btn">
                Logout
              </Button>
            </div>
          </div>
        </div>
      </div>

      <div className="container mx-auto px-4 py-6">
        {/* Analytics Cards */}
        {analytics && (
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
            <Card data-testid="analytics-total">
              <CardContent className="p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-gray-600">Total Tokens Today</p>
                    <p className="text-2xl font-bold text-blue-600">{analytics.total_tokens_today}</p>
                  </div>
                  <div className="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center">
                    <svg className="w-5 h-5 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                    </svg>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card data-testid="analytics-active">
              <CardContent className="p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-gray-600">Active in Queue</p>
                    <p className="text-2xl font-bold text-green-600">{analytics.active_tokens}</p>
                  </div>
                  <div className="w-10 h-10 bg-green-100 rounded-lg flex items-center justify-center">
                    <svg className="w-5 h-5 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card data-testid="analytics-completed">
              <CardContent className="p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-gray-600">Completed Today</p>
                    <p className="text-2xl font-bold text-purple-600">{analytics.completed_tokens_today}</p>
                  </div>
                  <div className="w-10 h-10 bg-purple-100 rounded-lg flex items-center justify-center">
                    <svg className="w-5 h-5 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card data-testid="analytics-wait-time">
              <CardContent className="p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-gray-600">Avg Wait Time</p>
                    <p className="text-2xl font-bold text-orange-600">{analytics.average_wait_time}m</p>
                  </div>
                  <div className="w-10 h-10 bg-orange-100 rounded-lg flex items-center justify-center">
                    <svg className="w-5 h-5 text-orange-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                    </svg>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        )}

        <div className="grid lg:grid-cols-4 gap-6">
          {/* Queue Management */}
          <div className="lg:col-span-3">
            <Card data-testid="queue-management">
              <CardHeader>
                <div className="flex justify-between items-center">
                  <div>
                    <CardTitle>Current Queue</CardTitle>
                    <CardDescription>Manage patient tokens and queue positions</CardDescription>
                  </div>
                  <Button 
                    onClick={() => setShowCreateForm(true)}
                    className="bg-red-600 hover:bg-red-700"
                    data-testid="create-emergency-btn"
                  >
                    <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v3m0 0v3m0-3h3m-3 0H9m12 0a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                    Emergency Token
                  </Button>
                </div>
              </CardHeader>
              <CardContent>
                {queueData.length === 0 ? (
                  <div className="text-center py-12" data-testid="empty-queue">
                    <div className="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-4">
                      <svg className="w-8 h-8 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                      </svg>
                    </div>
                    <h3 className="text-lg font-semibold text-gray-900 mb-2">No Tokens in Queue</h3>
                    <p className="text-gray-600">The queue is currently empty.</p>
                  </div>
                ) : (
                  <div className="space-y-3">
                    {queueData.map((token, index) => (
                      <div 
                        key={token.token_id} 
                        className="queue-item flex items-center justify-between p-4 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors"
                        data-testid={`queue-item-${index}`}
                      >
                        <div className="flex items-center space-x-4">
                          <div className="w-8 h-8 bg-blue-100 text-blue-600 rounded-full flex items-center justify-center font-bold text-sm">
                            #{token.position}
                          </div>
                          <div>
                            <div className="flex items-center space-x-2 mb-1">
                              <span className="font-mono font-bold text-sm">{token.token_number}</span>
                              {getPriorityBadge(token.priority_level)}
                            </div>
                            <p className="text-sm text-gray-600">{token.patient_name}</p>
                          </div>
                        </div>
                        
                        <div className="flex items-center space-x-2">
                          <span className="text-xs text-gray-500 mr-4">
                            Wait: {token.estimated_wait_time}m
                          </span>
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => openPriorityDialog(token)}
                            data-testid={`priority-btn-${index}`}
                          >
                            Priority
                          </Button>
                          <Button
                            size="sm"
                            onClick={() => handleCompleteToken(token.token_id)}
                            className="bg-green-600 hover:bg-green-700"
                            data-testid={`complete-btn-${index}`}
                          >
                            Complete
                          </Button>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          </div>

          {/* Quick Actions Sidebar */}
          <div className="space-y-6">
            {/* Quick Stats */}
            <Card data-testid="quick-stats">
              <CardHeader>
                <CardTitle className="text-lg">Quick Stats</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <div className="flex justify-between items-center">
                  <span className="text-sm text-gray-600">Critical Cases</span>
                  <Badge className="priority-critical text-xs">
                    {queueData.filter(t => t.priority_level === 1).length}
                  </Badge>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-sm text-gray-600">High Priority</span>
                  <Badge className="priority-high text-xs">
                    {queueData.filter(t => t.priority_level === 2).length}
                  </Badge>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-sm text-gray-600">Regular</span>
                  <Badge className="priority-medium-low text-xs">
                    {queueData.filter(t => t.priority_level >= 3).length}
                  </Badge>
                </div>
              </CardContent>
            </Card>

            {/* Quick Actions */}
            <Card data-testid="quick-actions">
              <CardHeader>
                <CardTitle className="text-lg">Quick Actions</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <Button 
                  onClick={() => setShowCreateForm(true)}
                  className="w-full bg-red-600 hover:bg-red-700"
                  data-testid="quick-emergency"
                >
                  <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v3m0 0v3m0-3h3m-3 0H9" />
                  </svg>
                  Emergency Token
                </Button>
                <Button 
                  onClick={() => {
                    fetchQueue();
                    fetchAnalytics();
                    toast.success('Queue refreshed');
                  }}
                  variant="outline" 
                  className="w-full"
                  data-testid="quick-refresh"
                >
                  <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                  </svg>
                  Refresh Queue
                </Button>
              </CardContent>
            </Card>
          </div>
        </div>

        {/* Emergency Token Creation Dialog */}
        {showCreateForm && (
          <Dialog open={showCreateForm} onOpenChange={setShowCreateForm}>
            <DialogContent data-testid="emergency-dialog">
              <DialogHeader>
                <DialogTitle>Create Emergency Token</DialogTitle>
                <DialogDescription>
                  Create a high-priority token for emergency cases
                </DialogDescription>
              </DialogHeader>
              <form onSubmit={handleCreateEmergencyToken} className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label htmlFor="patient-name">Patient Name</Label>
                    <Input
                      id="patient-name"
                      value={tokenForm.patient_name}
                      onChange={(e) => setTokenForm({...tokenForm, patient_name: e.target.value})}
                      required
                      data-testid="emergency-name"
                    />
                  </div>
                  <div>
                    <Label htmlFor="patient-phone">Phone Number</Label>
                    <Input
                      id="patient-phone"
                      value={tokenForm.patient_phone}
                      onChange={(e) => setTokenForm({...tokenForm, patient_phone: e.target.value.replace(/\D/g, '').slice(0, 10)})}
                      required
                      data-testid="emergency-phone"
                    />
                  </div>
                </div>
                
                <div>
                  <Label>Priority Category</Label>
                  <Select 
                    value={tokenForm.category} 
                    onValueChange={(value) => setTokenForm({...tokenForm, category: value})}
                  >
                    <SelectTrigger data-testid="emergency-category">
                      <SelectValue placeholder="Select category" />
                    </SelectTrigger>
                    <SelectContent>
                      {categories.map((category) => (
                        <SelectItem key={category.value} value={category.value}>
                          {category.label} (Priority {category.priority})
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>

                <div>
                  <Label htmlFor="symptoms">Symptoms/Reason</Label>
                  <Textarea
                    id="symptoms"
                    placeholder="Describe symptoms or reason for visit..."
                    value={tokenForm.symptoms}
                    onChange={(e) => setTokenForm({...tokenForm, symptoms: e.target.value})}
                    rows={3}
                    data-testid="emergency-symptoms"
                  />
                </div>

                <div className="flex space-x-4 pt-4">
                  <Button 
                    type="submit" 
                    disabled={loading}
                    className="bg-red-600 hover:bg-red-700 flex-1"
                    data-testid="emergency-submit"
                  >
                    {loading ? 'Creating...' : 'Create Token'}
                  </Button>
                  <Button 
                    type="button" 
                    variant="outline" 
                    onClick={() => setShowCreateForm(false)}
                    data-testid="emergency-cancel"
                  >
                    Cancel
                  </Button>
                </div>
              </form>
            </DialogContent>
          </Dialog>
        )}

        {/* Priority Update Dialog */}
        {showPriorityDialog && (
          <Dialog open={showPriorityDialog} onOpenChange={setShowPriorityDialog}>
            <DialogContent data-testid="priority-dialog">
              <DialogHeader>
                <DialogTitle>Update Token Priority</DialogTitle>
                <DialogDescription>
                  Change priority for token: {selectedToken?.token_number}
                </DialogDescription>
              </DialogHeader>
              <form onSubmit={handleUpdatePriority} className="space-y-4">
                <div>
                  <Label>New Priority Level</Label>
                  <Select 
                    value={priorityForm.new_priority} 
                    onValueChange={(value) => setPriorityForm({...priorityForm, new_priority: value})}
                  >
                    <SelectTrigger data-testid="priority-select">
                      <SelectValue placeholder="Select priority" />
                    </SelectTrigger>
                    <SelectContent>
                      {priorityLevels.map((level) => (
                        <SelectItem key={level.value} value={level.value.toString()}>
                          <span className={level.color}>{level.label} (Level {level.value})</span>
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>

                <div className="flex space-x-4 pt-4">
                  <Button 
                    type="submit" 
                    className="bg-blue-600 hover:bg-blue-700 flex-1"
                    data-testid="priority-submit"
                  >
                    Update Priority
                  </Button>
                  <Button 
                    type="button" 
                    variant="outline" 
                    onClick={() => setShowPriorityDialog(false)}
                    data-testid="priority-cancel"
                  >
                    Cancel
                  </Button>
                </div>
              </form>
            </DialogContent>
          </Dialog>
        )}
      </div>
    </div>
  );
};

export default StaffDashboard;