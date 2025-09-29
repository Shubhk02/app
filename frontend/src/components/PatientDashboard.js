import React, { useState, useEffect } from 'react';
import { useAuth } from '../App';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Textarea } from '@/components/ui/textarea';
import { Badge } from '@/components/ui/badge';
import { toast } from 'sonner';
import axios from 'axios';

const PatientDashboard = () => {
  const { user, logout } = useAuth();
  const [activeToken, setActiveToken] = useState(null);
  const [tokenHistory, setTokenHistory] = useState([]);
  const [loading, setLoading] = useState(false);
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [queueData, setQueueData] = useState([]);

  const [tokenForm, setTokenForm] = useState({
    category: '',
    symptoms: ''
  });

  const categories = [
    { value: 'emergency', label: 'Emergency', priority: 1, description: 'Life-threatening conditions' },
    { value: 'urgent_medical', label: 'Urgent Medical', priority: 2, description: 'Serious medical attention needed' },
    { value: 'serious_condition', label: 'Serious Condition', priority: 3, description: 'Medical condition requiring prompt care' },
    { value: 'regular_consultation', label: 'Regular Consultation', priority: 4, description: 'Routine medical consultation' },
    { value: 'report_pickup', label: 'Report Pickup', priority: 5, description: 'Collect medical reports' },
    { value: 'report_consultation', label: 'Report Consultation', priority: 6, description: 'Discuss medical reports with doctor' }
  ];

  useEffect(() => {
    fetchTokens();
    fetchQueue();
    
    // Set up polling for real-time updates
    const interval = setInterval(() => {
      fetchTokens();
      fetchQueue();
    }, 30000); // Poll every 30 seconds

    return () => clearInterval(interval);
  }, []);

  const fetchTokens = async () => {
    try {
      const response = await axios.get('/tokens');
      const tokens = response.data;
      
      // Find active token
      const active = tokens.find(token => token.status === 'active');
      setActiveToken(active);
      
      // Set token history (completed/cancelled tokens)
      const history = tokens.filter(token => token.status !== 'active');
      setTokenHistory(history.slice(0, 5)); // Show last 5
    } catch (error) {
      console.error('Error fetching tokens:', error);
    }
  };

  const fetchQueue = async () => {
    try {
      const response = await axios.get('/queue');
      setQueueData(response.data.queue || []);
    } catch (error) {
      console.error('Error fetching queue:', error);
    }
  };

  const handleCreateToken = async (e) => {
    e.preventDefault();
    
    if (!tokenForm.category) {
      toast.error('Please select a category');
      return;
    }

    setLoading(true);
    
    try {
      const response = await axios.post('/tokens', tokenForm);
      toast.success('Token created successfully!');
      setActiveToken(response.data);
      setShowCreateForm(false);
      setTokenForm({ category: '', symptoms: '' });
      fetchQueue(); // Refresh queue
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to create token');
    } finally {
      setLoading(false);
    }
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
    return <Badge className={`${config.className} font-semibold`}>{config.label}</Badge>;
  };

  const getPositionInQueue = () => {
    if (!activeToken || !queueData.length) return null;
    
    const tokenInQueue = queueData.find(item => item.token_id === activeToken.id);
    return tokenInQueue ? tokenInQueue.position : null;
  };

  const getAheadCount = () => {
    const position = getPositionInQueue();
    return position ? position - 1 : 0;
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-indigo-50">
      {/* Header */}
      <div className="bg-white shadow-sm border-b border-gray-200">
        <div className="container mx-auto px-4 py-4">
          <div className="flex justify-between items-center">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">Patient Dashboard</h1>
              <p className="text-gray-600">Welcome back, {user?.name}</p>
            </div>
            <div className="flex items-center space-x-4">
              <Button
                onClick={() => {
                  fetchTokens();
                  fetchQueue();
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

      <div className="container mx-auto px-4 py-8">
        <div className="grid lg:grid-cols-3 gap-8">
          {/* Main Content */}
          <div className="lg:col-span-2 space-y-6">
            {/* Active Token Card */}
            {activeToken ? (
              <Card className="border-2 border-blue-200 bg-blue-50/50" data-testid="active-token-card">
                <CardHeader>
                  <div className="flex justify-between items-start">
                    <div>
                      <CardTitle className="text-xl text-blue-900">Your Current Token</CardTitle>
                      <CardDescription>Track your queue position and estimated wait time</CardDescription>
                    </div>
                    {getPriorityBadge(activeToken.priority_level)}
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="grid md:grid-cols-2 gap-6">
                    <div className="space-y-4">
                      <div>
                        <p className="text-sm font-medium text-gray-600">Token Number</p>
                        <p className="text-2xl font-bold token-number text-blue-800" data-testid="token-number">
                          {activeToken.token_number}
                        </p>
                      </div>
                      <div>
                        <p className="text-sm font-medium text-gray-600">Category</p>
                        <p className="text-lg capitalize text-gray-900">{activeToken.category.replace('_', ' ')}</p>
                      </div>
                      {activeToken.symptoms && (
                        <div>
                          <p className="text-sm font-medium text-gray-600">Symptoms</p>
                          <p className="text-gray-800">{activeToken.symptoms}</p>
                        </div>
                      )}
                    </div>
                    
                    <div className="space-y-4">
                      <div>
                        <p className="text-sm font-medium text-gray-600">Position in Queue</p>
                        <div className="flex items-center space-x-2">
                          <span className="text-3xl font-bold text-green-600" data-testid="queue-position">
                            #{getPositionInQueue() || activeToken.position}
                          </span>
                          <div className="text-sm text-gray-600">
                            {getAheadCount()} ahead
                          </div>
                        </div>
                      </div>
                      <div>
                        <p className="text-sm font-medium text-gray-600">Estimated Wait Time</p>
                        <p className="text-xl font-semibold text-orange-600" data-testid="wait-time">
                          {activeToken.estimated_wait_time} minutes
                        </p>
                      </div>
                      <div className="flex items-center space-x-2 text-green-600">
                        <div className="w-3 h-3 bg-green-500 rounded-full animate-pulse"></div>
                        <span className="text-sm font-medium">Active</span>
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ) : (
              <Card className="text-center py-12" data-testid="no-token-card">
                <CardContent>
                  <div className="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-4">
                    <svg className="w-8 h-8 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
                    </svg>
                  </div>
                  <h3 className="text-lg font-semibold text-gray-900 mb-2">No Active Token</h3>
                  <p className="text-gray-600 mb-6">You don't have any active tokens. Create one to join the queue.</p>
                  <Button 
                    onClick={() => setShowCreateForm(true)}
                    className="bg-blue-600 hover:bg-blue-700"
                    data-testid="create-token-btn"
                  >
                    Create New Token
                  </Button>
                </CardContent>
              </Card>
            )}

            {/* Create Token Form */}
            {showCreateForm && (
              <Card className="fade-in" data-testid="create-token-form">
                <CardHeader>
                  <CardTitle>Create New Token</CardTitle>
                  <CardDescription>Select your visit type and provide any relevant symptoms</CardDescription>
                </CardHeader>
                <CardContent>
                  <form onSubmit={handleCreateToken} className="space-y-6">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Visit Category
                      </label>
                      <Select 
                        value={tokenForm.category} 
                        onValueChange={(value) => setTokenForm({...tokenForm, category: value})}
                      >
                        <SelectTrigger data-testid="category-select">
                          <SelectValue placeholder="Select visit type" />
                        </SelectTrigger>
                        <SelectContent>
                          {categories.map((category) => (
                            <SelectItem key={category.value} value={category.value}>
                              <div className="flex flex-col">
                                <span className="font-medium">{category.label}</span>
                                <span className="text-xs text-gray-500">{category.description}</span>
                              </div>
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Symptoms (Optional)
                      </label>
                      <Textarea
                        placeholder="Describe your symptoms or reason for visit..."
                        value={tokenForm.symptoms}
                        onChange={(e) => setTokenForm({...tokenForm, symptoms: e.target.value})}
                        rows={3}
                        data-testid="symptoms-textarea"
                      />
                    </div>

                    <div className="flex space-x-4">
                      <Button 
                        type="submit" 
                        disabled={loading}
                        className="bg-green-600 hover:bg-green-700 flex-1"
                        data-testid="submit-token-btn"
                      >
                        {loading ? (
                          <>
                            <div className="loading-spinner mr-2"></div>
                            Creating...
                          </>
                        ) : (
                          'Create Token'
                        )}
                      </Button>
                      <Button 
                        type="button" 
                        variant="outline" 
                        onClick={() => setShowCreateForm(false)}
                        data-testid="cancel-token-btn"
                      >
                        Cancel
                      </Button>
                    </div>
                  </form>
                </CardContent>
              </Card>
            )}

            {/* Token History */}
            {tokenHistory.length > 0 && (
              <Card data-testid="token-history">
                <CardHeader>
                  <CardTitle>Recent Visits</CardTitle>
                  <CardDescription>Your previous token history</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    {tokenHistory.map((token) => (
                      <div key={token.id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                        <div className="flex items-center space-x-4">
                          <span className="token-number font-mono text-sm">{token.token_number}</span>
                          <span className="capitalize text-sm text-gray-600">{token.category.replace('_', ' ')}</span>
                          <Badge className={`status-${token.status} text-xs`}>
                            {token.status}
                          </Badge>
                        </div>
                        <span className="text-xs text-gray-500">
                          {new Date(token.created_at).toLocaleDateString()}
                        </span>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            )}
          </div>

          {/* Sidebar */}
          <div className="space-y-6">
            {/* Quick Actions */}
            <Card data-testid="quick-actions">
              <CardHeader>
                <CardTitle className="text-lg">Quick Actions</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                {!activeToken && (
                  <Button 
                    onClick={() => setShowCreateForm(true)}
                    className="w-full bg-blue-600 hover:bg-blue-700"
                    data-testid="quick-create-token"
                  >
                    <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
                    </svg>
                    Create Token
                  </Button>
                )}
                <Button 
                  onClick={() => {
                    fetchTokens();
                    fetchQueue();
                    toast.success('Updated successfully');
                  }}
                  variant="outline" 
                  className="w-full"
                  data-testid="quick-refresh"
                >
                  <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                  </svg>
                  Refresh Status
                </Button>
              </CardContent>
            </Card>

            {/* Current Queue Status */}
            <Card data-testid="queue-status">
              <CardHeader>
                <CardTitle className="text-lg">Queue Status</CardTitle>
                <CardDescription>Current hospital queue information</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-gray-600">Total in Queue</span>
                    <span className="font-semibold">{queueData.length}</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-gray-600">Critical Cases</span>
                    <span className="font-semibold text-red-600">
                      {queueData.filter(item => item.priority_level === 1).length}
                    </span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-gray-600">Your Position</span>
                    <span className="font-semibold text-blue-600">
                      {getPositionInQueue() ? `#${getPositionInQueue()}` : 'N/A'}
                    </span>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Help & Support */}
            <Card data-testid="help-support">
              <CardHeader>
                <CardTitle className="text-lg">Need Help?</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3 text-sm">
                  <div className="flex items-start space-x-2">
                    <div className="w-2 h-2 bg-blue-500 rounded-full mt-2"></div>
                    <span>Emergency cases receive immediate attention</span>
                  </div>
                  <div className="flex items-start space-x-2">
                    <div className="w-2 h-2 bg-blue-500 rounded-full mt-2"></div>
                    <span>Queue positions update automatically</span>
                  </div>
                  <div className="flex items-start space-x-2">
                    <div className="w-2 h-2 bg-blue-500 rounded-full mt-2"></div>
                    <span>Wait times are estimates based on current queue</span>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </div>
  );
};

export default PatientDashboard;