import React, { useState, useEffect } from 'react';
import { useAuth } from '../App';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Badge } from '@/components/ui/badge';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { toast } from 'sonner';
import axios from 'axios';

const AdminDashboard = () => {
  const { user, logout } = useAuth();
  const [analytics, setAnalytics] = useState(null);
  const [users, setUsers] = useState([]);
  const [queueData, setQueueData] = useState([]);
  const [loading, setLoading] = useState(false);
  const [showCreateUserDialog, setShowCreateUserDialog] = useState(false);

  const [createUserForm, setCreateUserForm] = useState({
    name: '',
    email: '',
    phone: '',
    password: '',
    role: 'staff'
  });

  useEffect(() => {
    fetchAnalytics();
    fetchUsers();
    fetchQueue();
    
    // Set up polling for real-time updates
    const interval = setInterval(() => {
      fetchAnalytics();
      fetchQueue();
    }, 60000); // Poll every minute

    return () => clearInterval(interval);
  }, []);

  const fetchAnalytics = async () => {
    try {
      const response = await axios.get('/analytics/dashboard');
      setAnalytics(response.data);
    } catch (error) {
      console.error('Error fetching analytics:', error);
    }
  };

  const fetchUsers = async () => {
    try {
      const response = await axios.get('/users');
      setUsers(response.data);
    } catch (error) {
      console.error('Error fetching users:', error);
      toast.error('Failed to fetch users');
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

  const handleCreateUser = async (e) => {
    e.preventDefault();
    
    if (!createUserForm.name || !createUserForm.email || !createUserForm.password) {
      toast.error('Please fill all required fields');
      return;
    }

    if (!/^\d{10}$/.test(createUserForm.phone)) {
      toast.error('Phone number must be 10 digits');
      return;
    }

    setLoading(true);
    
    try {
      await axios.post('/users/create-staff', createUserForm);
      toast.success('User created successfully!');
      setShowCreateUserDialog(false);
      setCreateUserForm({ name: '', email: '', phone: '', password: '', role: 'staff' });
      fetchUsers();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to create user');
    } finally {
      setLoading(false);
    }
  };

  const getPriorityDistribution = () => {
    if (!analytics?.priority_distribution) return [];
    
    return Object.entries(analytics.priority_distribution).map(([priority, count]) => ({
      priority,
      count,
      percentage: analytics.total_tokens_today > 0 ? 
        Math.round((count / analytics.total_tokens_today) * 100) : 0
    }));
  };

  const getRoleColor = (role) => {
    switch (role) {
      case 'admin': return 'bg-red-100 text-red-800';
      case 'staff': return 'bg-blue-100 text-blue-800';
      case 'patient': return 'bg-green-100 text-green-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 via-white to-purple-50">
      {/* Header */}
      <div className="bg-white shadow-sm border-b border-gray-200">
        <div className="container mx-auto px-4 py-4">
          <div className="flex justify-between items-center">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">Admin Dashboard</h1>
              <p className="text-gray-600">System overview and user management</p>
            </div>
            <div className="flex items-center space-x-4">
              <Button
                onClick={() => {
                  fetchAnalytics();
                  fetchUsers();
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

      <div className="container mx-auto px-4 py-6">
        <Tabs defaultValue="overview" className="w-full">
          <TabsList className="grid w-full grid-cols-3 mb-6">
            <TabsTrigger value="overview" data-testid="overview-tab">System Overview</TabsTrigger>
            <TabsTrigger value="users" data-testid="users-tab">User Management</TabsTrigger>
            <TabsTrigger value="analytics" data-testid="analytics-tab">Analytics</TabsTrigger>
          </TabsList>

          {/* System Overview Tab */}
          <TabsContent value="overview">
            {/* Key Metrics */}
            {analytics && (
              <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
                <Card className="bg-gradient-to-br from-blue-50 to-blue-100 border-blue-200" data-testid="metric-total">
                  <CardContent className="p-6">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-sm font-medium text-blue-600">Total Tokens Today</p>
                        <p className="text-3xl font-bold text-blue-900">{analytics.total_tokens_today}</p>
                      </div>
                      <div className="w-12 h-12 bg-blue-200 rounded-xl flex items-center justify-center">
                        <svg className="w-6 h-6 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                        </svg>
                      </div>
                    </div>
                  </CardContent>
                </Card>

                <Card className="bg-gradient-to-br from-green-50 to-green-100 border-green-200" data-testid="metric-active">
                  <CardContent className="p-6">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-sm font-medium text-green-600">Active Queue</p>
                        <p className="text-3xl font-bold text-green-900">{analytics.active_tokens}</p>
                      </div>
                      <div className="w-12 h-12 bg-green-200 rounded-xl flex items-center justify-center">
                        <svg className="w-6 h-6 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                        </svg>
                      </div>
                    </div>
                  </CardContent>
                </Card>

                <Card className="bg-gradient-to-br from-purple-50 to-purple-100 border-purple-200" data-testid="metric-completed">
                  <CardContent className="p-6">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-sm font-medium text-purple-600">Completed Today</p>
                        <p className="text-3xl font-bold text-purple-900">{analytics.completed_tokens_today}</p>
                      </div>
                      <div className="w-12 h-12 bg-purple-200 rounded-xl flex items-center justify-center">
                        <svg className="w-6 h-6 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                        </svg>
                      </div>
                    </div>
                  </CardContent>
                </Card>

                <Card className="bg-gradient-to-br from-orange-50 to-orange-100 border-orange-200" data-testid="metric-wait">
                  <CardContent className="p-6">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-sm font-medium text-orange-600">Avg Wait Time</p>
                        <p className="text-3xl font-bold text-orange-900">{analytics.average_wait_time}m</p>
                      </div>
                      <div className="w-12 h-12 bg-orange-200 rounded-xl flex items-center justify-center">
                        <svg className="w-6 h-6 text-orange-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                        </svg>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </div>
            )}

            {/* Current Queue Status */}
            <div className="grid lg:grid-cols-2 gap-6">
              <Card data-testid="queue-overview">
                <CardHeader>
                  <CardTitle>Current Queue Status</CardTitle>
                  <CardDescription>Real-time queue overview</CardDescription>
                </CardHeader>
                <CardContent>
                  {queueData.length === 0 ? (
                    <div className="text-center py-8">
                      <p className="text-gray-500">No patients in queue</p>
                    </div>
                  ) : (
                    <div className="space-y-3">
                      {queueData.slice(0, 5).map((token, index) => (
                        <div key={token.token_id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                          <div className="flex items-center space-x-3">
                            <span className="w-6 h-6 bg-blue-100 text-blue-600 rounded-full flex items-center justify-center text-sm font-bold">
                              {token.position}
                            </span>
                            <div>
                              <p className="font-medium text-sm">{token.patient_name}</p>
                              <p className="text-xs text-gray-500 font-mono">{token.token_number}</p>
                            </div>
                          </div>
                          <Badge 
                            className={`
                              ${token.priority_level === 1 ? 'priority-critical' : ''}
                              ${token.priority_level === 2 ? 'priority-high' : ''}
                              ${token.priority_level >= 3 ? 'priority-medium-low' : ''}
                              text-xs
                            `}
                          >
                            Priority {token.priority_level}
                          </Badge>
                        </div>
                      ))}
                      {queueData.length > 5 && (
                        <p className="text-center text-sm text-gray-500 pt-2">
                          +{queueData.length - 5} more in queue
                        </p>
                      )}
                    </div>
                  )}
                </CardContent>
              </Card>

              <Card data-testid="user-overview">
                <CardHeader>
                  <CardTitle>User Statistics</CardTitle>
                  <CardDescription>System user breakdown</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    <div className="flex justify-between items-center">
                      <span className="text-sm text-gray-600">Total Users</span>
                      <span className="font-semibold text-lg">{users.length}</span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-sm text-gray-600">Admins</span>
                      <Badge className="bg-red-100 text-red-800">
                        {users.filter(u => u.role === 'admin').length}
                      </Badge>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-sm text-gray-600">Staff</span>
                      <Badge className="bg-blue-100 text-blue-800">
                        {users.filter(u => u.role === 'staff').length}
                      </Badge>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-sm text-gray-600">Patients</span>
                      <Badge className="bg-green-100 text-green-800">
                        {users.filter(u => u.role === 'patient').length}
                      </Badge>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-sm text-gray-600">Active Users</span>
                      <Badge className="bg-emerald-100 text-emerald-800">
                        {users.filter(u => u.is_active).length}
                      </Badge>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>
          </TabsContent>

          {/* User Management Tab */}
          <TabsContent value="users">
            <div className="flex justify-between items-center mb-6">
              <div>
                <h2 className="text-xl font-semibold text-gray-900">User Management</h2>
                <p className="text-gray-600">Manage system users and their roles</p>
              </div>
              <Button 
                onClick={() => setShowCreateUserDialog(true)}
                className="bg-blue-600 hover:bg-blue-700"
                data-testid="create-user-btn"
              >
                <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
                </svg>
                Create User
              </Button>
            </div>

            <Card data-testid="users-list">
              <CardContent className="p-0">
                <div className="overflow-x-auto">
                  <table className="w-full">
                    <thead>
                      <tr className="border-b border-gray-200 bg-gray-50">
                        <th className="text-left p-4 font-medium text-gray-700">Name</th>
                        <th className="text-left p-4 font-medium text-gray-700">Email</th>
                        <th className="text-left p-4 font-medium text-gray-700">Phone</th>
                        <th className="text-left p-4 font-medium text-gray-700">Role</th>
                        <th className="text-left p-4 font-medium text-gray-700">Status</th>
                        <th className="text-left p-4 font-medium text-gray-700">Created</th>
                      </tr>
                    </thead>
                    <tbody>
                      {users.map((user, index) => (
                        <tr key={user.id} className="border-b border-gray-100 hover:bg-gray-50" data-testid={`user-row-${index}`}>
                          <td className="p-4">
                            <div className="font-medium text-gray-900">{user.name}</div>
                          </td>
                          <td className="p-4 text-gray-600">{user.email}</td>
                          <td className="p-4 text-gray-600 font-mono text-sm">{user.phone}</td>
                          <td className="p-4">
                            <Badge className={`${getRoleColor(user.role)} capitalize`}>
                              {user.role}
                            </Badge>
                          </td>
                          <td className="p-4">
                            <Badge className={user.is_active ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}>
                              {user.is_active ? 'Active' : 'Inactive'}
                            </Badge>
                          </td>
                          <td className="p-4 text-gray-600 text-sm">
                            {new Date(user.created_at).toLocaleDateString()}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Analytics Tab */}
          <TabsContent value="analytics">
            {analytics && (
              <div className="grid lg:grid-cols-2 gap-6">
                {/* Priority Distribution */}
                <Card data-testid="priority-analytics">
                  <CardHeader>
                    <CardTitle>Priority Distribution</CardTitle>
                    <CardDescription>Token distribution by priority level</CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-4">
                      {getPriorityDistribution().map(({ priority, count, percentage }) => (
                        <div key={priority} className="flex items-center justify-between">
                          <div className="flex items-center space-x-3">
                            <div className={`w-3 h-3 rounded-full ${
                              priority === 'CRITICAL' ? 'bg-red-500' :
                              priority === 'HIGH' ? 'bg-orange-500' :
                              priority === 'MEDIUM_HIGH' ? 'bg-yellow-500' :
                              priority === 'MEDIUM_LOW' ? 'bg-blue-500' :
                              priority === 'REPORT_PICKUP' ? 'bg-green-500' :
                              'bg-purple-500'
                            }`}></div>
                            <span className="text-sm capitalize">{priority.replace('_', ' ')}</span>
                          </div>
                          <div className="flex items-center space-x-2">
                            <span className="text-sm font-medium">{count}</span>
                            <span className="text-xs text-gray-500">({percentage}%)</span>
                          </div>
                        </div>
                      ))}
                    </div>
                  </CardContent>
                </Card>

                {/* System Performance */}
                <Card data-testid="performance-analytics">
                  <CardHeader>
                    <CardTitle>System Performance</CardTitle>
                    <CardDescription>Key performance indicators</CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-6">
                      <div>
                        <div className="flex justify-between items-center mb-2">
                          <span className="text-sm text-gray-600">Completion Rate</span>
                          <span className="text-sm font-medium">
                            {analytics.total_tokens_today > 0 ? 
                              Math.round((analytics.completed_tokens_today / analytics.total_tokens_today) * 100) : 0
                            }%
                          </span>
                        </div>
                        <div className="w-full bg-gray-200 rounded-full h-2">
                          <div 
                            className="bg-green-600 h-2 rounded-full" 
                            style={{ 
                              width: `${analytics.total_tokens_today > 0 ? 
                                Math.round((analytics.completed_tokens_today / analytics.total_tokens_today) * 100) : 0
                              }%` 
                            }}
                          ></div>
                        </div>
                      </div>

                      <div className="grid grid-cols-2 gap-4">
                        <div className="text-center p-4 bg-gray-50 rounded-lg">
                          <p className="text-2xl font-bold text-blue-600">{analytics.active_tokens}</p>
                          <p className="text-xs text-gray-600">In Queue</p>
                        </div>
                        <div className="text-center p-4 bg-gray-50 rounded-lg">
                          <p className="text-2xl font-bold text-green-600">{analytics.average_wait_time}m</p>
                          <p className="text-xs text-gray-600">Avg Wait</p>
                        </div>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </div>
            )}
          </TabsContent>
        </Tabs>

        {/* Create User Dialog */}
        {showCreateUserDialog && (
          <Dialog open={showCreateUserDialog} onOpenChange={setShowCreateUserDialog}>
            <DialogContent data-testid="create-user-dialog">
              <DialogHeader>
                <DialogTitle>Create New User</DialogTitle>
                <DialogDescription>
                  Create a new staff or admin user account
                </DialogDescription>
              </DialogHeader>
              <form onSubmit={handleCreateUser} className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label htmlFor="user-name">Full Name</Label>
                    <Input
                      id="user-name"
                      value={createUserForm.name}
                      onChange={(e) => setCreateUserForm({...createUserForm, name: e.target.value})}
                      required
                      data-testid="user-name-input"
                    />
                  </div>
                  <div>
                    <Label htmlFor="user-email">Email</Label>
                    <Input
                      id="user-email"
                      type="email"
                      value={createUserForm.email}
                      onChange={(e) => setCreateUserForm({...createUserForm, email: e.target.value})}
                      required
                      data-testid="user-email-input"
                    />
                  </div>
                </div>
                
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label htmlFor="user-phone">Phone Number</Label>
                    <Input
                      id="user-phone"
                      value={createUserForm.phone}
                      onChange={(e) => setCreateUserForm({...createUserForm, phone: e.target.value.replace(/\D/g, '').slice(0, 10)})}
                      required
                      data-testid="user-phone-input"
                    />
                  </div>
                  <div>
                    <Label>Role</Label>
                    <Select 
                      value={createUserForm.role} 
                      onValueChange={(value) => setCreateUserForm({...createUserForm, role: value})}
                    >
                      <SelectTrigger data-testid="user-role-select">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="staff">Staff</SelectItem>
                        <SelectItem value="admin">Admin</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                </div>

                <div>
                  <Label htmlFor="user-password">Password</Label>
                  <Input
                    id="user-password"
                    type="password"
                    value={createUserForm.password}
                    onChange={(e) => setCreateUserForm({...createUserForm, password: e.target.value})}
                    required
                    data-testid="user-password-input"
                  />
                </div>

                <div className="flex space-x-4 pt-4">
                  <Button 
                    type="submit" 
                    disabled={loading}
                    className="bg-blue-600 hover:bg-blue-700 flex-1"
                    data-testid="user-submit-btn"
                  >
                    {loading ? 'Creating...' : 'Create User'}
                  </Button>
                  <Button 
                    type="button" 
                    variant="outline" 
                    onClick={() => setShowCreateUserDialog(false)}
                    data-testid="user-cancel-btn"
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

export default AdminDashboard;