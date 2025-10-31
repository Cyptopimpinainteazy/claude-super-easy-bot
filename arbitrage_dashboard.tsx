import React, { useState, useEffect } from 'react';
import { LineChart, Line, AreaChart, Area, BarChart, Bar, PieChart, Pie, Cell, RadarChart, Radar, PolarGrid, PolarAngleAxis, PolarRadiusAxis, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { ArrowUpDown, TrendingUp, Zap, DollarSign, AlertTriangle, Settings, Play, Pause, RefreshCw, Activity, Target, Layers, Cpu, Database, Flame, Award, BarChart3, Radio, Bell, Shield, Download, Share2, Lock, Unlock } from 'lucide-react';

const ArbitrageDashboard = () => {
  const [isRunning, setIsRunning] = useState(true);
  const [selectedPair, setSelectedPair] = useState(0);
  const [timeframe, setTimeframe] = useState('1m');
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [soundEnabled, setSoundEnabled] = useState(false);
  const [autoExecute, setAutoExecute] = useState(false);

  const [profitHistory, setProfitHistory] = useState([
    { time: '00:00', profit: 120, trades: 5, success: 80, volume: 45000, gas: 42 },
    { time: '00:05', profit: 145, trades: 7, success: 85, volume: 52000, gas: 38 },
    { time: '00:10', profit: 180, trades: 9, success: 88, volume: 61000, gas: 45 },
    { time: '00:15', profit: 165, trades: 8, success: 82, volume: 58000, gas: 51 },
    { time: '00:20', profit: 200, trades: 11, success: 90, volume: 67000, gas: 47 },
    { time: '00:25', profit: 235, trades: 13, success: 92, volume: 74000, gas: 43 },
    { time: '00:30', profit: 280, trades: 15, success: 93, volume: 82000, gas: 49 },
    { time: '00:35', profit: 320, trades: 17, success: 94, volume: 89000, gas: 46 },
    { time: '00:40', profit: 365, trades: 19, success: 91, volume: 95000, gas: 52 },
    { time: '00:45', profit: 410, trades: 22, success: 95, volume: 103000, gas: 44 },
    { time: '00:50', profit: 456, trades: 24, success: 96, volume: 112000, gas: 41 },
  ]);

  const chainData = [
    { name: 'Ethereum', value: 35, trades: 420, profit: 4580, color: '#627EEA' },
    { name: 'Polygon', value: 25, trades: 380, profit: 3240, color: '#8247E5' },
    { name: 'Arbitrum', value: 18, trades: 290, profit: 2890, color: '#28A0F0' },
    { name: 'BSC', value: 12, trades: 210, profit: 1650, color: '#F3BA2F' },
    { name: 'Avalanche', value: 7, trades: 145, profit: 980, color: '#E84142' },
    { name: 'Base', value: 3, trades: 95, profit: 520, color: '#0052FF' },
  ];

  const [gasPrices] = useState([
    { time: '00:00', eth: 45, polygon: 120, arbitrum: 0.15, bsc: 3 },
    { time: '00:10', eth: 52, polygon: 135, arbitrum: 0.18, bsc: 3.2 },
    { time: '00:20', eth: 48, polygon: 128, arbitrum: 0.16, bsc: 3.1 },
    { time: '00:30', eth: 55, polygon: 142, arbitrum: 0.19, bsc: 3.4 },
    { time: '00:40', eth: 61, polygon: 155, arbitrum: 0.21, bsc: 3.6 },
    { time: '00:50', eth: 58, polygon: 148, arbitrum: 0.20, bsc: 3.5 },
  ]);

  const spreadData = [
    { range: '0-0.1%', count: 145, avgProfit: 35 },
    { range: '0.1-0.2%', count: 320, avgProfit: 58 },
    { range: '0.2-0.5%', count: 480, avgProfit: 92 },
    { range: '0.5-1%', count: 280, avgProfit: 145 },
    { range: '1%+', count: 120, avgProfit: 280 },
  ];

  const performanceData = [
    { metric: 'Speed', value: 92 },
    { metric: 'Accuracy', value: 88 },
    { metric: 'Profit', value: 85 },
    { metric: 'Efficiency', value: 90 },
    { metric: 'Risk Mgmt', value: 87 },
    { metric: 'Execution', value: 94 },
  ];

  const [opportunities, setOpportunities] = useState([
    {
      id: 1,
      pair: 'ETH/USDT',
      buyExchange: 'Uniswap V3',
      sellExchange: 'SushiSwap',
      buyPrice: 3247.82,
      sellPrice: 3251.45,
      spread: 0.11,
      profit: 125.80,
      gasEstimate: 45.20,
      netProfit: 80.60,
      volume24h: 2450000,
      liquidity: 850000,
      confidence: 95,
      risk: 'Low',
      chain: 'Ethereum',
      flashLoanAvailable: true,
      trend: [3240, 3245, 3248, 3252, 3255, 3251, 3249, 3252],
      volatility: 0.08,
      impact: 0.05
    },
    {
      id: 2,
      pair: 'BTC/USDC',
      buyExchange: 'PancakeSwap',
      sellExchange: 'Curve',
      buyPrice: 67891.20,
      sellPrice: 67945.80,
      spread: 0.08,
      profit: 89.40,
      gasEstimate: 28.50,
      netProfit: 60.90,
      volume24h: 5670000,
      liquidity: 1200000,
      confidence: 87,
      risk: 'Medium',
      chain: 'BSC',
      flashLoanAvailable: true,
      trend: [67850, 67880, 67910, 67890, 67920, 67945, 67930, 67940],
      volatility: 0.12,
      impact: 0.08
    },
    {
      id: 3,
      pair: 'MATIC/USDT',
      buyExchange: 'QuickSwap',
      sellExchange: 'Balancer',
      buyPrice: 0.8924,
      sellPrice: 0.8941,
      spread: 0.19,
      profit: 67.30,
      gasEstimate: 12.80,
      netProfit: 54.50,
      volume24h: 890000,
      liquidity: 450000,
      confidence: 78,
      risk: 'High',
      chain: 'Polygon',
      flashLoanAvailable: true,
      trend: [0.889, 0.891, 0.892, 0.894, 0.893, 0.894, 0.892, 0.893],
      volatility: 0.15,
      impact: 0.12
    },
    {
      id: 4,
      pair: 'AVAX/USDT',
      buyExchange: 'TraderJoe',
      sellExchange: 'Pangolin',
      buyPrice: 38.45,
      sellPrice: 38.56,
      spread: 0.29,
      profit: 52.30,
      gasEstimate: 8.20,
      netProfit: 44.10,
      volume24h: 680000,
      liquidity: 320000,
      confidence: 82,
      risk: 'Medium',
      chain: 'Avalanche',
      flashLoanAvailable: true,
      trend: [38.40, 38.42, 38.45, 38.48, 38.52, 38.56, 38.54, 38.55],
      volatility: 0.11,
      impact: 0.09
    },
    {
      id: 5,
      pair: 'ARB/USDC',
      buyExchange: 'Camelot',
      sellExchange: 'SushiSwap',
      buyPrice: 1.245,
      sellPrice: 1.252,
      spread: 0.56,
      profit: 95.40,
      gasEstimate: 6.80,
      netProfit: 88.60,
      volume24h: 450000,
      liquidity: 280000,
      confidence: 91,
      risk: 'Low',
      chain: 'Arbitrum',
      flashLoanAvailable: true,
      trend: [1.240, 1.242, 1.245, 1.248, 1.250, 1.252, 1.251, 1.252],
      volatility: 0.09,
      impact: 0.06
    }
  ]);

  const [portfolioStats] = useState({
    totalPnL: 12847.63,
    todayPnL: 456.89,
    successRate: 87.3,
    totalTrades: 1247,
    averageProfit: 23.45,
    maxDrawdown: -156.80,
    winRate: 89.2,
    avgExecutionTime: 2.3,
    gasEfficiency: 92.5,
    sharpeRatio: 2.34,
    maxConsecutiveWins: 17,
    activeCapital: 25000
  });

  const [systemStats] = useState({
    cpu: 34,
    memory: 58,
    network: 125,
    latency: 12,
    uptime: '99.97%',
    requestsPerSec: 847
  });

  const chains = ['Ethereum', 'Polygon', 'Arbitrum', 'BSC', 'Avalanche', 'Base'];
  const timeframes = ['15s', '1m', '5m', '15m', '1h', '4h'];

  useEffect(() => {
    if (autoRefresh && isRunning) {
      const interval = setInterval(() => {
        setOpportunities(prev => prev.map(opp => ({
          ...opp,
          buyPrice: opp.buyPrice * (1 + (Math.random() - 0.5) * 0.002),
          sellPrice: opp.sellPrice * (1 + (Math.random() - 0.5) * 0.002),
          confidence: Math.max(60, Math.min(99, opp.confidence + (Math.random() - 0.5) * 3)),
          spread: Math.max(0.05, Math.min(0.5, opp.spread + (Math.random() - 0.5) * 0.03)),
          trend: [...opp.trend.slice(1), opp.sellPrice * (1 + (Math.random() - 0.5) * 0.001)]
        })));

        setProfitHistory(prev => {
          const last = prev[prev.length - 1];
          const newEntry = {
            time: new Date().toLocaleTimeString().slice(0, 5),
            profit: last.profit + Math.random() * 50,
            trades: last.trades + Math.floor(Math.random() * 3),
            success: Math.min(100, Math.max(70, last.success + (Math.random() - 0.5) * 2)),
            volume: last.volume + Math.random() * 10000,
            gas: 35 + Math.random() * 20
          };
          return [...prev.slice(1), newEntry];
        });
      }, 2000);
      return () => clearInterval(interval);
    }
  }, [autoRefresh, isRunning]);

  const getRiskColor = (risk) => {
    switch (risk.toLowerCase()) {
      case 'low': return 'text-green-400 bg-green-400/10 border-green-400/30';
      case 'medium': return 'text-yellow-400 bg-yellow-400/10 border-yellow-400/30';
      case 'high': return 'text-red-400 bg-red-400/10 border-red-400/30';
      default: return 'text-gray-400 bg-gray-400/10 border-gray-400/30';
    }
  };

  const getChainColor = (chain) => {
    const colors = {
      'Ethereum': 'from-blue-500 to-blue-600',
      'Polygon': 'from-purple-500 to-purple-600',
      'Arbitrum': 'from-cyan-500 to-cyan-600',
      'BSC': 'from-yellow-500 to-yellow-600',
      'Avalanche': 'from-red-500 to-red-600',
      'Base': 'from-indigo-500 to-indigo-600'
    };
    return colors[chain] || 'from-gray-500 to-gray-600';
  };

  const CustomTooltip = ({ active, payload }) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-gray-900/95 backdrop-blur-sm border border-cyan-400/30 rounded-lg p-3 shadow-xl">
          <p className="text-cyan-400 font-bold mb-1">{payload[0].payload.time}</p>
          {payload.map((entry, index) => (
            <p key={index} className="text-sm" style={{ color: entry.color }}>
              {entry.name}: {typeof entry.value === 'number' ? entry.value.toFixed(2) : entry.value}
            </p>
          ))}
        </div>
      );
    }
    return null;
  };

  const selectedOpp = opportunities[selectedPair];

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-slate-900 to-gray-900 text-white overflow-hidden">
      {/* Enhanced Animated background */}
      <div className="fixed inset-0 overflow-hidden pointer-events-none">
        <div className="absolute w-96 h-96 bg-cyan-500/5 rounded-full blur-3xl animate-pulse" style={{ top: '10%', left: '20%' }} />
        <div className="absolute w-96 h-96 bg-blue-500/5 rounded-full blur-3xl animate-pulse" style={{ top: '60%', right: '10%', animationDelay: '1s' }} />
        <div className="absolute w-96 h-96 bg-purple-500/5 rounded-full blur-3xl animate-pulse" style={{ top: '40%', left: '60%', animationDelay: '2s' }} />
      </div>

      <div className="relative z-10">
        {/* Ultra Premium Header */}
        <div className="border-b border-cyan-500/20 bg-black/70 backdrop-blur-xl shadow-2xl shadow-cyan-500/10">
          <div className="flex items-center justify-between p-4">
            <div className="flex items-center space-x-8">
              <div className="flex items-center space-x-3">
                <div className="relative">
                  <div className="absolute inset-0 bg-gradient-to-r from-cyan-500 to-blue-500 blur-xl opacity-50 animate-pulse" />
                  <ArrowUpDown className="relative w-12 h-12 text-cyan-400" />
                </div>
                <div>
                  <h1 className="text-4xl font-black bg-gradient-to-r from-cyan-400 via-blue-400 to-purple-400 bg-clip-text text-transparent">
                    ARBITRAGE NEXUS
                  </h1>
                  <p className="text-xs text-cyan-400/60 font-mono tracking-widest">⚡ QUANTUM ENGINE v5.0 ⚡</p>
                </div>
              </div>
              
              <div className="flex items-center space-x-3">
                <button
                  onClick={() => setIsRunning(!isRunning)}
                  className={`flex items-center space-x-2 px-8 py-4 rounded-xl font-black transition-all transform hover:scale-105 shadow-2xl relative overflow-hidden group ${
                    isRunning 
                      ? 'bg-gradient-to-r from-red-500 to-red-600 shadow-red-500/50' 
                      : 'bg-gradient-to-r from-green-500 to-green-600 shadow-green-500/50'
                  }`}
                >
                  <div className="absolute inset-0 bg-white/20 transform translate-x-[-100%] group-hover:translate-x-[100%] transition-transform duration-500" />
                  {isRunning ? <Pause className="w-6 h-6" /> : <Play className="w-6 h-6" />}
                  <span className="text-lg">{isRunning ? 'STOP' : 'START'}</span>
                </button>
                
                <button 
                  onClick={() => setAutoExecute(!autoExecute)}
                  className={`p-4 rounded-xl transition-all border-2 ${autoExecute ? 'bg-purple-500/20 border-purple-500' : 'bg-gray-800/50 border-gray-700'}`}
                >
                  {autoExecute ? <Unlock className="w-6 h-6 text-purple-400" /> : <Lock className="w-6 h-6 text-gray-400" />}
                </button>
                
                <button 
                  onClick={() => setSoundEnabled(!soundEnabled)}
                  className="p-4 bg-gray-800/50 hover:bg-gray-700/50 rounded-xl transition-all border border-gray-700"
                >
                  {soundEnabled ? <Bell className="w-6 h-6 text-yellow-400" /> : <Bell className="w-6 h-6 text-gray-400" />}
                </button>
                
                <div className="flex items-center space-x-2 px-6 py-4 bg-gray-800/50 rounded-xl border-2 border-cyan-500/30">
                  <Radio className={`w-5 h-5 ${isRunning ? 'text-green-400 animate-pulse' : 'text-gray-400'}`} />
                  <div>
                    <div className="text-xs text-gray-400 font-mono">STATUS</div>
                    <div className="text-sm font-black">
                      {isRunning ? <span className="text-green-400">LIVE</span> : <span className="text-red-400">PAUSED</span>}
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <div className="flex items-center space-x-6">
              <div className="text-right bg-gradient-to-br from-green-500/10 to-emerald-500/10 rounded-xl p-4 border border-green-500/20">
                <div className="text-4xl font-black bg-gradient-to-r from-green-400 to-emerald-400 bg-clip-text text-transparent">
                  ${portfolioStats.totalPnL.toLocaleString()}
                </div>
                <div className="text-xs text-gray-400 font-mono">TOTAL P&L</div>
              </div>
              
              <div className="text-right bg-gradient-to-br from-cyan-500/10 to-blue-500/10 rounded-xl p-4 border border-cyan-500/20">
                <div className={`text-3xl font-black ${portfolioStats.todayPnL >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                  {portfolioStats.todayPnL >= 0 ? '+' : ''}${portfolioStats.todayPnL.toLocaleString()}
                </div>
                <div className="text-xs text-gray-400 font-mono">TODAY</div>
              </div>

              <div className="flex space-x-2">
                <button className="p-4 bg-gray-800/50 hover:bg-cyan-500/20 rounded-xl transition-all border border-gray-700 hover:border-cyan-500">
                  <Download className="w-6 h-6 text-gray-400 hover:text-cyan-400 transition-colors" />
                </button>
                <button className="p-4 bg-gray-800/50 hover:bg-cyan-500/20 rounded-xl transition-all border border-gray-700 hover:border-cyan-500">
                  <Share2 className="w-6 h-6 text-gray-400 hover:text-cyan-400 transition-colors" />
                </button>
                <button className="p-4 bg-gray-800/50 hover:bg-cyan-500/20 rounded-xl transition-all border border-gray-700 hover:border-cyan-500">
                  <Settings className="w-6 h-6 text-gray-400 hover:text-cyan-400 hover:rotate-90 transition-all duration-300" />
                </button>
              </div>
            </div>
          </div>

          {/* Mega Stats Bar */}
          <div className="bg-gradient-to-r from-gray-900/80 via-gray-800/80 to-gray-900/80 border-t border-cyan-500/20 p-4">
            <div className="grid grid-cols-10 gap-3">
              {[
                { icon: Target, label: 'Win Rate', value: `${portfolioStats.winRate}%`, color: 'text-green-400', bg: 'from-green-500/10 to-green-600/10', border: 'border-green-500/20' },
                { icon: Zap, label: 'Exec', value: `${portfolioStats.avgExecutionTime}s`, color: 'text-cyan-400', bg: 'from-cyan-500/10 to-cyan-600/10', border: 'border-cyan-500/20' },
                { icon: BarChart3, label: 'Trades', value: portfolioStats.totalTrades, color: 'text-blue-400', bg: 'from-blue-500/10 to-blue-600/10', border: 'border-blue-500/20' },
                { icon: DollarSign, label: 'Avg', value: `$${portfolioStats.averageProfit}`, color: 'text-green-400', bg: 'from-green-500/10 to-green-600/10', border: 'border-green-500/20' },
                { icon: Flame, label: 'Active', value: opportunities.length, color: 'text-orange-400', bg: 'from-orange-500/10 to-orange-600/10', border: 'border-orange-500/20' },
                { icon: Layers, label: 'Flash', value: opportunities.filter(o => o.flashLoanAvailable).length, color: 'text-purple-400', bg: 'from-purple-500/10 to-purple-600/10', border: 'border-purple-500/20' },
                { icon: Cpu, label: 'Gas Eff', value: `${portfolioStats.gasEfficiency}%`, color: 'text-yellow-400', bg: 'from-yellow-500/10 to-yellow-600/10', border: 'border-yellow-500/20' },
                { icon: Shield, label: 'Sharpe', value: portfolioStats.sharpeRatio, color: 'text-indigo-400', bg: 'from-indigo-500/10 to-indigo-600/10', border: 'border-indigo-500/20' },
                { icon: Award, label: 'Streak', value: portfolioStats.maxConsecutiveWins, color: 'text-pink-400', bg: 'from-pink-500/10 to-pink-600/10', border: 'border-pink-500/20' },
                { icon: Database, label: 'Capital', value: `$${(portfolioStats.activeCapital/1000).toFixed(0)}K`, color: 'text-emerald-400', bg: 'from-emerald-500/10 to-emerald-600/10', border: 'border-emerald-500/20' },
              ].map((stat, idx) => (
                <div key={idx} className={`flex flex-col justify-center bg-gradient-to-br ${stat.bg} rounded-lg p-3 border ${stat.border} hover:scale-105 transition-transform`}>
                  <div className="flex items-center space-x-2 mb-1">
                    <stat.icon className={`w-4 h-4 ${stat.color}`} />
                    <div className="text-xs text-gray-400 font-mono">{stat.label}</div>
                  </div>
                  <div className={`text-xl font-black ${stat.color}`}>{stat.value}</div>
                </div>
              ))}
            </div>
          </div>

          {/* System Stats Bar */}
          <div className="bg-black/50 border-t border-gray-800 p-2">
            <div className="flex items-center justify-between text-xs font-mono">
              <div className="flex items-center space-x-6">
                <div className="flex items-center space-x-2">
                  <Cpu className="w-3 h-3 text-cyan-400" />
                  <span className="text-gray-400">CPU:</span>
                  <span className="text-cyan-400 font-bold">{systemStats.cpu}%</span>
                </div>
                <div className="flex items-center space-x-2">
                  <Database className="w-3 h-3 text-purple-400" />
                  <span className="text-gray-400">MEM:</span>
                  <span className="text-purple-400 font-bold">{systemStats.memory}%</span>
                </div>
                <div className="flex items-center space-x-2">
                  <Activity className="w-3 h-3 text-green-400" />
                  <span className="text-gray-400">NET:</span>
                  <span className="text-green-400 font-bold">{systemStats.network}MB/s</span>
                </div>
                <div className="flex items-center space-x-2">
                  <Zap className="w-3 h-3 text-yellow-400" />
                  <span className="text-gray-400">LATENCY:</span>
                  <span className="text-yellow-400 font-bold">{systemStats.latency}ms</span>
                </div>
              </div>
              <div className="flex items-center space-x-6">
                <div className="flex items-center space-x-2">
                  <span className="text-gray-400">UPTIME:</span>
                  <span className="text-green-400 font-bold">{systemStats.uptime}</span>
                </div>
                <div className="flex items-center space-x-2">
                  <span className="text-gray-400">REQ/SEC:</span>
                  <span className="text-cyan-400 font-bold">{systemStats.requestsPerSec}</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Main Content */}
        <div className="p-4 space-y-4">
          {/* Top Charts Row */}
          <div className="grid grid-cols-3 gap-4">
            {/* Profit Timeline */}
            <div className="col-span-2 bg-black/40 backdrop-blur-sm rounded-xl border border-gray-700/50 p-6 shadow-2xl">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-xl font-black text-cyan-400 flex items-center space-x-2">
                  <TrendingUp className="w-6 h-6" />
                  <span>PROFIT EVOLUTION</span>
                </h3>
                <div className="flex space-x-2">
                  {['1H', '4H', '1D', '1W'].map(tf => (
                    <button key={tf} className="px-4 py-2 bg-gray-800/50 hover:bg-cyan-500/20 rounded-lg text-xs font-bold transition-all border border-gray-700">
                      {tf}
                    </button>
                  ))}
                </div>
              </div>
              <ResponsiveContainer width="100%" height={250}>
                <AreaChart data={profitHistory}>
                  <defs>
                    <linearGradient id="colorProfit" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#06b6d4" stopOpacity={0.8}/>
                      <stop offset="95%" stopColor="#06b6d4" stopOpacity={0}/>
                    </linearGradient>
                    <linearGradient id="colorVolume" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#8b5cf6" stopOpacity={0.8}/>
                      <stop offset="95%" stopColor="#8b5cf6" stopOpacity={0}/>
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                  <XAxis dataKey="time" stroke="#9ca3af" style={{ fontSize: '12px' }} />
                  <YAxis yAxisId="left" stroke="#9ca3af" style={{ fontSize: '12px' }} />
                  <YAxis yAxisId="right" orientation="right" stroke="#9ca3af" style={{ fontSize: '12px' }} />
                  <Tooltip content={<CustomTooltip />} />
                  <Legend />
                  <Area yAxisId="left" type="monotone" dataKey="profit" stroke="#06b6d4" strokeWidth={3} fillOpacity={1} fill="url(#colorProfit)" name="Profit ($)" />
                  <Area yAxisId="right" type="monotone" dataKey="volume" stroke="#8b5cf6" strokeWidth={2} fillOpacity={0.3} fill="url(#colorVolume)" name="Volume" />
                </AreaChart>
              </ResponsiveContainer>
            </div>

            {/* Performance Radar */}
            <div className="bg-black/40 backdrop-blur-sm rounded-xl border border-gray-700/50 p-6 shadow-2xl">
              <h3 className="text-xl font-black text-purple-400 mb-4 flex items-center space-x-2">
                <Activity className="w-6 h-6" />
                <span>PERFORMANCE</span>
              </h3>
              <ResponsiveContainer width="100%" height={250}>
                <RadarChart data={performanceData}>
                  <PolarGrid stroke="#374151" />
                  <PolarAngleAxis dataKey="metric" stroke="#9ca3af" style={{ fontSize: '11px' }} />
                  <PolarRadiusAxis angle={90} domain={[0, 100]} stroke="#9ca3af" style={{ fontSize: '10px' }} />
                  <Radar name="Score" dataKey="value" stroke="#a855f7" fill="#a855f7" fillOpacity={0.6} />
                  <Tooltip content={<CustomTooltip />} />
                </RadarChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Middle Charts Row */}
          <div className="grid grid-cols-4 gap-4">
            {/* Chain Distribution */}
            <div className="bg-black/40 backdrop-blur-sm rounded-xl border border-gray-700/50 p-6 shadow-2xl">
              <h3 className="text-lg font-bold text-blue-400 mb-4 flex items-center space-x-2">
                <Layers className="w-5 h-5" />
                <span>CHAINS</span>
              </h3>
              <ResponsiveContainer width="100%" height={200}>
                <PieChart>
                  <Pie
                    data={chainData}
                    cx="50%"
                    cy="50%"
                    innerRadius={50}
                    outerRadius={80}
                    paddingAngle={5}
                    dataKey="value"
                  >
                    {chainData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Pie>
                  <Tooltip content={<CustomTooltip />} />
                </PieChart>
              </ResponsiveContainer>
            </div>

            {/* Gas Prices */}
            <div className="bg-black/40 backdrop-blur-sm rounded-xl border border-gray-700/50 p-6 shadow-2xl">
              <h3 className="text-lg font-bold text-yellow-400 mb-4 flex items-center space-x-2">
                <Flame className="w-5 h-5" />
                <span>GAS TRENDS</span>
              </h3>
              <ResponsiveContainer width="100%" height={200}>
                <LineChart data={gasPrices}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                  <XAxis dataKey="time" stroke="#9ca3af" style={{ fontSize: '10px' }} />
                  <YAxis stroke="#9ca3af" style={{ fontSize: '10px' }} />
                  <Tooltip content={<CustomTooltip />} />
                  <Line type="monotone" dataKey="eth" stroke="#627EEA" strokeWidth={2} dot={false} name="ETH" />
                  <Line type="monotone" dataKey="polygon" stroke="#8247E5" strokeWidth={2} dot={false} name="Polygon" />
                </LineChart>
              </ResponsiveContainer>
            </div>

            {/* Spread Distribution */}
            <div className="bg-black/40 backdrop-blur-sm rounded-xl border border-gray-700/50 p-6 shadow-2xl">
              <h3 className="text-lg font-bold text-green-400 mb-4 flex items-center space-x-2">
                <BarChart3 className="w-5 h-5" />
                <span>SPREADS</span>
              </h3>
              <ResponsiveContainer width="100%" height={200}>
                <BarChart data={spreadData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                  <XAxis dataKey="range" stroke="#9ca3af" style={{ fontSize: '10px' }} />
                  <YAxis stroke="#9ca3af" style={{ fontSize: '10px' }} />
                  <Tooltip content={<CustomTooltip />} />
                  <Bar dataKey="count" fill="#10b981" radius={[8, 8, 0, 0]} name="Count" />
                </BarChart>
              </ResponsiveContainer>
            </div>

            {/* Success Rate */}
            <div className="bg-black/40 backdrop-blur-sm rounded-xl border border-gray-700/50 p-6 shadow-2xl">
              <h3 className="text-lg font-bold text-cyan-400 mb-4 flex items-center space-x-2">
                <Award className="w-5 h-5" />
                <span>SUCCESS</span>
              </h3>
              <ResponsiveContainer width="100%" height={200}>
                <AreaChart data={profitHistory}>
                  <defs>
                    <linearGradient id="colorSuccess" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#10b981" stopOpacity={0.8}/>
                      <stop offset="95%" stopColor="#10b981" stopOpacity={0}/>
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                  <XAxis dataKey="time" stroke="#9ca3af" style={{ fontSize: '10px' }} />
                  <YAxis stroke="#9ca3af" style={{ fontSize: '10px' }} domain={[0, 100]} />
                  <Tooltip content={<CustomTooltip />} />
                  <Area type="monotone" dataKey="success" stroke="#10b981" strokeWidth={2} fillOpacity={1} fill="url(#colorSuccess)" name="Success %" />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Opportunities Table */}
          <div className="bg-black/40 backdrop-blur-sm rounded-xl border border-gray-700/50 shadow-2xl">
            <div className="flex items-center justify-between p-6 border-b border-gray-700/50">
              <h2 className="text-2xl font-black text-cyan-400 flex items-center space-x-2">
                <Zap className="w-7 h-7 animate-pulse" />
                <span>LIVE ARBITRAGE OPPORTUNITIES</span>
              </h2>
              <div className="flex items-center space-x-3">
                <select 
                  value={timeframe} 
                  onChange={(e) => setTimeframe(e.target.value)}
                  className="bg-gray-800 border border-gray-600 rounded-lg px-4 py-2 text-sm font-mono hover:border-cyan-400 transition-all"
                >
                  {timeframes.map(tf => (
                    <option key={tf} value={tf}>{tf}</option>
                  ))}
                </select>
              </div>
            </div>

            <div className="overflow-hidden">
              <div className="grid grid-cols-12 gap-2 p-4 text-xs font-black text-gray-400 border-b border-gray-800/50 bg-gray-900/50">
                <div className="col-span-2">TRADING PAIR</div>
                <div className="col-span-1">CHAIN</div>
                <div className="col-span-2">BUY @ EXCHANGE</div>
                <div className="col-span-2">SELL @ EXCHANGE</div>
                <div className="col-span-1">SPREAD</div>
                <div className="col-span-1">NET PROFIT</div>
                <div className="col-span-1">CONFIDENCE</div>
                <div className="col-span-1">RISK</div>
                <div className="col-span-1">ACTION</div>
              </div>

              {opportunities.map((opp, idx) => (
                <div 
                  key={opp.id} 
                  className="grid grid-cols-12 gap-2 p-4 hover:bg-gradient-to-r hover:from-cyan-500/5 hover:to-blue-500/5 border-b border-gray-800/30 cursor-pointer transition-all group"
                  onClick={() => setSelectedPair(idx)}
                  style={{ animationDelay: `${idx * 50}ms` }}
                >
                  <div className="col-span-2">
                    <div className="font-black text-white text-lg group-hover:text-cyan-400 transition-all">{opp.pair}</div>
                    <div className="text-xs text-gray-400 font-mono">
                      Vol: ${(opp.volume24h / 1000000).toFixed(1)}M | Liq: ${(opp.liquidity / 1000).toFixed(0)}K
                    </div>
                  </div>
                  
                  <div className="col-span-1">
                    <span className={`px-3 py-1 rounded-lg text-xs font-bold text-white bg-gradient-to-r ${getChainColor(opp.chain)} shadow-lg`}>
                      {opp.chain}
                    </span>
                  </div>
                  
                  <div className="col-span-2">
                    <div className="font-bold text-green-400 text-sm">{opp.buyExchange}</div>
                    <div className="text-xs text-gray-300 font-mono">${opp.buyPrice.toFixed(4)}</div>
                  </div>
                  
                  <div className="col-span-2">
                    <div className="font-bold text-red-400 text-sm">{opp.sellExchange}</div>
                    <div className="text-xs text-gray-300 font-mono">${opp.sellPrice.toFixed(4)}</div>
                  </div>
                  
                  <div className="col-span-1">
                    <div className="font-black text-yellow-400 text-lg">{opp.spread.toFixed(2)}%</div>
                    <div className="w-full bg-gray-700 rounded-full h-1 mt-1">
                      <div className="bg-gradient-to-r from-yellow-400 to-orange-400 h-1 rounded-full" style={{ width: `${Math.min(100, opp.spread * 50)}%` }} />
                    </div>
                  </div>
                  
                  <div className="col-span-1">
                    <div className="font-black text-green-400 text-lg">${opp.netProfit.toFixed(2)}</div>
                    <div className="text-xs text-gray-400 font-mono">-${opp.gasEstimate.toFixed(2)} gas</div>
                  </div>
                  
                  <div className="col-span-1">
                    <div className="relative w-16 h-16">
                      <svg className="transform -rotate-90 w-16 h-16">
                        <circle cx="32" cy="32" r="28" stroke="#374151" strokeWidth="4" fill="none" />
                        <circle 
                          cx="32" cy="32" r="28" 
                          stroke={opp.confidence >= 90 ? '#10b981' : opp.confidence >= 80 ? '#fbbf24' : '#ef4444'} 
                          strokeWidth="4" 
                          fill="none"
                          strokeDasharray={`${2 * Math.PI * 28}`}
                          strokeDashoffset={`${2 * Math.PI * 28 * (1 - opp.confidence / 100)}`}
                          className="transition-all duration-500"
                        />
                      </svg>
                      <div className="absolute inset-0 flex items-center justify-center">
                        <span className={`text-xs font-black ${opp.confidence >= 90 ? 'text-green-400' : opp.confidence >= 80 ? 'text-yellow-400' : 'text-red-400'}`}>
                          {opp.confidence.toFixed(0)}%
                        </span>
                      </div>
                    </div>
                  </div>
                  
                  <div className="col-span-1">
                    <span className={`px-3 py-2 rounded-lg text-xs font-bold border ${getRiskColor(opp.risk)}`}>
                      {opp.risk.toUpperCase()}
                    </span>
                  </div>
                  
                  <div className="col-span-1 flex flex-col space-y-2">
                    <button className="bg-gradient-to-r from-cyan-500 to-blue-500 hover:from-cyan-400 hover:to-blue-400 text-white px-4 py-2 rounded-lg text-xs font-black transition-all transform hover:scale-105 shadow-lg shadow-cyan-500/30 flex items-center justify-center space-x-1">
                      <Zap className="w-3 h-3" />
                      <span>EXECUTE</span>
                    </button>
                    {opp.flashLoanAvailable && (
                      <div className="bg-purple-500/20 text-purple-400 px-2 py-1 rounded text-xs font-bold text-center border border-purple-500/30">
                        ⚡ FLASH
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Bottom Row - Enhanced Details */}
          <div className="grid grid-cols-3 gap-4">
            {/* Selected Pair Deep Analysis */}
            <div className="bg-black/40 backdrop-blur-sm rounded-xl border border-gray-700/50 p-6 shadow-2xl">
              <h3 className="text-xl font-black text-cyan-400 mb-4 flex items-center space-x-2">
                <Target className="w-6 h-6" />
                <span>{selectedOpp.pair} ANALYSIS</span>
              </h3>
              
              {/* Price Trend Mini Chart */}
              <div className="mb-4">
                <ResponsiveContainer width="100%" height={120}>
                  <LineChart data={selectedOpp.trend.map((price, idx) => ({ idx, price }))}>
                    <defs>
                      <linearGradient id="trendGradient" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="#06b6d4" stopOpacity={0.3}/>
                        <stop offset="95%" stopColor="#06b6d4" stopOpacity={0}/>
                      </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                    <XAxis dataKey="idx" stroke="#9ca3af" style={{ fontSize: '10px' }} />
                    <YAxis stroke="#9ca3af" style={{ fontSize: '10px' }} domain={['dataMin - 5', 'dataMax + 5']} />
                    <Tooltip content={<CustomTooltip />} />
                    <Line type="monotone" dataKey="price" stroke="#06b6d4" strokeWidth={3} dot={{ fill: '#06b6d4', r: 4 }} />
                  </LineChart>
                </ResponsiveContainer>
              </div>

              {/* Detailed Stats Grid */}
              <div className="grid grid-cols-2 gap-4 mb-4">
                <div className="bg-gradient-to-br from-green-500/10 to-emerald-500/10 border border-green-500/20 rounded-lg p-3">
                  <div className="text-gray-400 text-xs font-mono mb-1">Best Buy Price</div>
                  <div className="text-green-400 font-black text-xl">${selectedOpp.buyPrice.toFixed(4)}</div>
                  <div className="text-xs text-gray-500 font-mono">{selectedOpp.buyExchange}</div>
                </div>
                <div className="bg-gradient-to-br from-red-500/10 to-rose-500/10 border border-red-500/20 rounded-lg p-3">
                  <div className="text-gray-400 text-xs font-mono mb-1">Best Sell Price</div>
                  <div className="text-red-400 font-black text-xl">${selectedOpp.sellPrice.toFixed(4)}</div>
                  <div className="text-xs text-gray-500 font-mono">{selectedOpp.sellExchange}</div>
                </div>
              </div>

              {/* Execution Metrics */}
              <div className="space-y-2 bg-gray-900/50 rounded-lg p-4">
                <div className="flex justify-between text-sm">
                  <span className="text-gray-400">Expected Profit:</span>
                  <span className="text-green-400 font-bold">${selectedOpp.profit.toFixed(2)}</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-gray-400">Gas Cost:</span>
                  <span className="text-yellow-400 font-bold">${selectedOpp.gasEstimate.toFixed(2)}</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-gray-400">Slippage (0.5%):</span>
                  <span className="text-orange-400 font-bold">${(selectedOpp.profit * 0.05).toFixed(2)}</span>
                </div>
                <div className="border-t border-gray-700 pt-2 flex justify-between text-sm">
                  <span className="text-gray-300 font-bold">Net Profit:</span>
                  <span className="text-cyan-400 font-black text-lg">${selectedOpp.netProfit.toFixed(2)}</span>
                </div>
              </div>
            </div>

            {/* Chain Network Status */}
            <div className="bg-black/40 backdrop-blur-sm rounded-xl border border-gray-700/50 p-6 shadow-2xl">
              <h3 className="text-xl font-black text-blue-400 mb-4 flex items-center space-x-2">
                <Layers className="w-6 h-6" />
                <span>NETWORK STATUS</span>
              </h3>
              <div className="space-y-3">
                {chains.map((chain, idx) => {
                  const data = chainData[idx] || { trades: 0, value: 0 };
                  return (
                    <div key={chain} className="bg-gray-900/50 rounded-lg p-3 border border-gray-700/30 hover:border-gray-600/50 transition-all">
                      <div className="flex items-center justify-between mb-2">
                        <div className="flex items-center space-x-2">
                          <div className={`w-3 h-3 rounded-full bg-gradient-to-r ${getChainColor(chain)} animate-pulse`} />
                          <span className="font-bold text-white">{chain}</span>
                        </div>
                        <span className="text-green-400 text-xs font-bold">ONLINE</span>
                      </div>
                      <div className="grid grid-cols-3 gap-2 text-xs">
                        <div>
                          <div className="text-gray-400 font-mono">Trades</div>
                          <div className="text-cyan-400 font-bold">{data.trades || Math.floor(Math.random() * 400)}</div>
                        </div>
                        <div>
                          <div className="text-gray-400 font-mono">Gas</div>
                          <div className="text-yellow-400 font-bold">{Math.floor(Math.random() * 100)}gwei</div>
                        </div>
                        <div>
                          <div className="text-gray-400 font-mono">Latency</div>
                          <div className="text-green-400 font-bold">{Math.floor(Math.random() * 50)}ms</div>
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>

            {/* Alerts & Flash Loan */}
            <div className="space-y-4">
              {/* Alerts Panel */}
              <div className="bg-black/40 backdrop-blur-sm rounded-xl border border-gray-700/50 p-6 shadow-2xl">
                <h3 className="text-xl font-black text-yellow-400 mb-4 flex items-center space-x-2">
                  <AlertTriangle className="w-6 h-6 animate-pulse" />
                  <span>LIVE ALERTS</span>
                </h3>
                <div className="space-y-2">
                  <div className="bg-gradient-to-r from-red-500/20 to-orange-500/20 border border-red-500/30 rounded-lg p-3 animate-pulse">
                    <div className="flex items-center space-x-2">
                      <Flame className="w-4 h-4 text-red-400" />
                      <div className="text-red-400 font-bold text-sm">High Gas Alert</div>
                    </div>
                    <div className="text-gray-300 text-xs mt-1">Ethereum gas &gt; 100 gwei</div>
                  </div>
                  <div className="bg-gradient-to-r from-green-500/20 to-emerald-500/20 border border-green-500/30 rounded-lg p-3">
                    <div className="flex items-center space-x-2">
                      <TrendingUp className="w-4 h-4 text-green-400" />
                      <div className="text-green-400 font-bold text-sm">New Opportunity</div>
                    </div>
                    <div className="text-gray-300 text-xs mt-1">AVAX/USDT 0.23% spread detected</div>
                  </div>
                  <div className="bg-gradient-to-r from-purple-500/20 to-pink-500/20 border border-purple-500/30 rounded-lg p-3">
                    <div className="flex items-center space-x-2">
                      <Zap className="w-4 h-4 text-purple-400" />
                      <div className="text-purple-400 font-bold text-sm">Flash Loan Ready</div>
                    </div>
                    <div className="text-gray-300 text-xs mt-1">Aave pool liquidity optimal</div>
                  </div>
                </div>
              </div>

              {/* Flash Loan Panel */}
              <div className="bg-black/40 backdrop-blur-sm rounded-xl border border-gray-700/50 p-6 shadow-2xl">
                <h3 className="text-xl font-black text-purple-400 mb-4 flex items-center space-x-2">
                  <Database className="w-6 h-6" />
                  <span>FLASH LOANS</span>
                </h3>
                <div className="space-y-3">
                  <div className="bg-gray-900/50 rounded-lg p-3">
                    <div className="flex justify-between items-center mb-2">
                      <span className="text-gray-400 text-sm font-mono">Aave Protocol</span>
                      <span className="text-green-400 text-xs font-bold flex items-center space-x-1">
                        <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse" />
                        <span>ONLINE</span>
                      </span>
                    </div>
                    <div className="grid grid-cols-2 gap-2 text-xs">
                      <div>
                        <div className="text-gray-500">Available</div>
                        <div className="text-cyan-400 font-bold">$2.5M</div>
                      </div>
                      <div>
                        <div className="text-gray-500">Fee</div>
                        <div className="text-yellow-400 font-bold">0.09%</div>
                      </div>
                    </div>
                  </div>
                  
                  <div className="bg-gray-900/50 rounded-lg p-3">
                    <div className="flex justify-between items-center mb-2">
                      <span className="text-gray-400 text-sm font-mono">dYdX Protocol</span>
                      <span className="text-green-400 text-xs font-bold flex items-center space-x-1">
                        <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse" />
                        <span>ONLINE</span>
                      </span>
                    </div>
                    <div className="grid grid-cols-2 gap-2 text-xs">
                      <div>
                        <div className="text-gray-500">Available</div>
                        <div className="text-cyan-400 font-bold">$1.8M</div>
                      </div>
                      <div>
                        <div className="text-gray-500">Fee</div>
                        <div className="text-green-400 font-bold">0.00%</div>
                      </div>
                    </div>
                  </div>

                  <button className="w-full bg-gradient-to-r from-purple-500 to-pink-500 hover:from-purple-400 hover:to-pink-400 text-white py-3 rounded-lg font-black transition-all transform hover:scale-105 shadow-lg shadow-purple-500/30">
                    EXECUTE FLASH LOAN
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ArbitrageDashboard;