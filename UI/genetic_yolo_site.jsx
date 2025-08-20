import React, { useState, useRef } from "react";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Upload, Sparkles, BrainCircuit, Trophy, BarChart3, Rocket, Users, AlertCircle, CheckCircle, Download, FileText, TrendingUp, Zap, Activity, Database, Star, Crown, Gem, Link } from "lucide-react";
import { motion } from "framer-motion";

// API configuration
const API_BASE_URL = 'http://localhost:5001/api';

// Default YOLO metrics for demo purposes
const defaultYoloMetrics = {
  riskApeIndex: 50,
  disciplineFactor: 50,
  diamondHandsDNA: 50,
  panicSellPropensity: 50,
  valueVersusMomentum: "Balanced Ape",
  totalSnpsAnalyzed: 0,
  significantFindings: 0
};

const leaderboard = [
  { name: "GoldenGenes99", score: 99, title: "👑 Golden Emperor", snps: 687234 },
  { name: "MidasDNA", score: 95, title: "⛏️ Premium Prospector", snps: 623451 },
  { name: "DiamondBuffett", score: 92, title: "💎 Legendary Luminary", snps: 598677 },
  { name: "CrownChain", score: 89, title: "🏆 Golden Gladiator", snps: 545332 },
  { name: "AurumsApe", score: 87, title: "⚡ Golden God", snps: 512998 },
];

export default function GeneticYOLOPage() {
  const [sessionId, setSessionId] = useState(null);
  const [analysisStatus, setAnalysisStatus] = useState('idle'); // idle, uploading, analyzing, completed, error
  const [yoloMetrics, setYoloMetrics] = useState(defaultYoloMetrics);
  const [topFindings, setTopFindings] = useState([]);
  const [error, setError] = useState(null);
  const [fileName, setFileName] = useState('');
  const [analysisProgress, setAnalysisProgress] = useState(0);
  const [currentStep, setCurrentStep] = useState('');
  const fileInputRef = useRef(null);
  
  const showReport = analysisStatus === 'completed';
  const isLoading = analysisStatus === 'uploading' || analysisStatus === 'analyzing';

  // API integration functions
  const handleFileSelect = async (event) => {
    const file = event.target.files[0];
    if (!file) return;

    setFileName(file.name);
    setAnalysisStatus('uploading');
    setError(null);

    try {
      // Upload file
      const formData = new FormData();
      formData.append('file', file);

      const uploadResponse = await fetch(`${API_BASE_URL}/upload`, {
        method: 'POST',
        body: formData,
      });

      if (!uploadResponse.ok) {
        const errorData = await uploadResponse.json();
        throw new Error(errorData.error || 'Upload failed');
      }

      const uploadResult = await uploadResponse.json();
      setSessionId(uploadResult.session_id);
      
      // Start analysis
      setAnalysisStatus('analyzing');
      setAnalysisProgress(25);
      setCurrentStep('Initializing analysis engine...');
      
      const analysisResponse = await fetch(`${API_BASE_URL}/analyze/${uploadResult.session_id}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          magnitude_threshold: 0.0,
          // Uncomment the line below to limit analysis for testing
          // limit: 1000
        }),
      });

      if (!analysisResponse.ok) {
        const errorData = await analysisResponse.json();
        throw new Error(errorData.error || 'Analysis failed');
      }

      const analysisResult = await analysisResponse.json();
      
      // Simulate progressive analysis steps
      setAnalysisProgress(75);
      setCurrentStep('Processing genetic markers...');
      await new Promise(resolve => setTimeout(resolve, 500));
      
      setAnalysisProgress(90);
      setCurrentStep('Calculating YOLO scores...');
      await new Promise(resolve => setTimeout(resolve, 500));
      
      setAnalysisProgress(100);
      setCurrentStep('Analysis complete!');
      
      // Update state with results
      setYoloMetrics(analysisResult.yolo_metrics);
      setTopFindings(analysisResult.top_findings || []);
      setAnalysisStatus('completed');

    } catch (err) {
      setError(err.message);
      setAnalysisStatus('error');
      setAnalysisProgress(0);
      setCurrentStep('');
    }
  };

  const downloadResults = async () => {
    if (!sessionId) return;

    try {
      const response = await fetch(`${API_BASE_URL}/export/${sessionId}`);
      if (!response.ok) {
        throw new Error('Download failed');
      }

      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.style.display = 'none';
      a.href = url;
      a.download = `genetic_yolo_analysis_${sessionId}.json`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (err) {
      setError(`Download failed: ${err.message}`);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-yellow-900 via-amber-900 to-yellow-800 text-white p-4 sm:p-6 font-mono relative overflow-x-hidden">
      {/* Golden Chain Background Effects */}
      <div className="fixed inset-0 pointer-events-none">
        <div className="absolute inset-0 bg-gradient-to-r from-yellow-800/20 via-amber-600/10 to-yellow-800/20 animate-pulse"></div>
        <div className="absolute top-0 left-1/4 w-96 h-96 bg-yellow-400/10 rounded-full blur-3xl animate-pulse"></div>
        <div className="absolute bottom-0 right-1/4 w-96 h-96 bg-amber-400/10 rounded-full blur-3xl animate-pulse"></div>
        {/* Golden Chain Pattern */}
        <div className="absolute inset-0 opacity-5">
          <div className="absolute top-10 left-10 transform rotate-45">
            <div className="flex space-x-4">
              <Link className="w-8 h-8 text-yellow-400" />
              <Link className="w-8 h-8 text-amber-400" />
              <Link className="w-8 h-8 text-yellow-400" />
            </div>
          </div>
          <div className="absolute bottom-20 right-20 transform -rotate-45">
            <div className="flex space-x-4">
              <Link className="w-6 h-6 text-amber-400" />
              <Link className="w-6 h-6 text-yellow-400" />
              <Link className="w-6 h-6 text-amber-400" />
            </div>
          </div>
        </div>
      </div>
      <motion.h1
        initial={{ y: -50, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        transition={{ duration: 0.6 }}
        className="text-3xl sm:text-4xl md:text-5xl lg:text-6xl font-bold text-center bg-gradient-to-r from-yellow-300 via-amber-200 to-yellow-300 bg-clip-text text-transparent drop-shadow-2xl mb-6 sm:mb-8 relative z-10"
      >
🔥 GENETIC GOLD RUSH — STRIKE PREMIUM DNA! ⛏️✨
      </motion.h1>

      <motion.p
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.3, duration: 0.6 }}
        className="text-center text-base sm:text-lg md:text-xl lg:text-2xl max-w-3xl mx-auto mb-6 sm:mb-10 px-4 relative z-10"
      >
        🚀 Welcome to the most LUXURIOUS genetic experience on Earth! 🌟 What if we told you there's a way to discover if you have GOLDEN GENES 🧬✨ — the premium DNA that separates diamond-handed legends from paper-handed peasants? 💎🙌
      </motion.p>

      <motion.p
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.5, duration: 0.6 }}
        className="text-center text-base sm:text-lg md:text-xl max-w-3xl mx-auto mb-6 sm:mb-10 text-yellow-300 px-4 relative z-10"
      >
        👑 THE MOST PREMIUM GENETIC GOLDMINE EVER CREATED 👑
      </motion.p>

      <motion.p
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.7, duration: 0.6 }}
        className="text-center text-sm sm:text-base md:text-lg max-w-3xl mx-auto mb-6 sm:mb-10 px-4 relative z-10"
      >
        ✨ Simply upload your <span className="text-amber-300 font-bold">premium genetic data</span> 🧬 and watch our LEGENDARY AI engine analyze your DNA through the most exclusive database in the universe! 🌟 We're talking Warren Buffett's secret genetic formula meets Midas touch technology! 💰⚡
      </motion.p>

      <Card className="max-w-xl mx-auto bg-gradient-to-br from-yellow-900/90 to-amber-900/90 backdrop-blur-sm border-yellow-400 border-4 shadow-2xl shadow-yellow-400/40 relative z-10 ring-2 ring-yellow-300/30">
        <CardContent className="p-6">
          <div className="flex flex-col items-center gap-4">
            <div className="relative">
              <Upload className="w-12 h-12 text-yellow-300 animate-bounce" />
              <Crown className="w-6 h-6 text-amber-300 absolute -top-2 -right-2 animate-pulse" />
            </div>
            <div className="text-center space-y-3">
              <p className="text-white text-xl font-bold">
                🌟 Drop your <span className="text-yellow-300 font-extrabold bg-gradient-to-r from-yellow-400 to-amber-400 bg-clip-text text-transparent">PREMIUM DNA</span> and let's strike GENETIC GOLD! ⛏️💎
              </p>
              <div className="flex flex-wrap items-center justify-center gap-2 sm:gap-4 text-xs sm:text-sm text-gray-300">
                <div className="flex items-center gap-1">
                  <FileText className="w-4 h-4" />
                  23andMe (.txt)
                </div>
                <div className="flex items-center gap-1">
                  <Database className="w-4 h-4" />
                  AncestryDNA (.txt)
                </div>
                <div className="flex items-center gap-1">
                  <Activity className="w-4 h-4" />
                  Raw data files
                </div>
              </div>
            </div>
            <input
              ref={fileInputRef}
              type="file"
              accept=".txt,.gz"
              onChange={handleFileSelect}
              className="hidden"
            />
            <Button
              onClick={() => fileInputRef.current?.click()}
              disabled={isLoading}
              className="bg-gradient-to-r from-yellow-400 via-yellow-300 to-amber-400 hover:from-yellow-300 hover:via-amber-300 hover:to-yellow-400 text-black font-extrabold py-3 px-4 sm:px-6 rounded-xl text-sm sm:text-lg disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-300 hover:scale-105 hover:shadow-2xl hover:shadow-yellow-400/60 border-2 border-yellow-300 ring-2 ring-yellow-400/30"
            >
              {isLoading ? '⚡ Striking Gold...' : '💎 Discover Your Golden Genes'} ⛏️
            </Button>
            {/* Status Messages */}
            {analysisStatus === 'uploading' && (
              <motion.div
                initial={{ opacity: 0, y: -10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5 }}
                className="bg-gradient-to-r from-yellow-900/80 to-amber-900/80 text-yellow-200 p-4 mt-4 rounded-xl shadow-lg border border-yellow-400/50 flex items-center gap-2"
              >
                <Upload className="w-5 h-5 animate-bounce" />
                ⛏️ Uploading {fileName}... Preparing to STRIKE GENETIC GOLD! ✨💰
              </motion.div>
            )}
            
            {analysisStatus === 'analyzing' && (
              <motion.div
                initial={{ opacity: 0, y: -10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5 }}
                className="bg-gradient-to-br from-yellow-900/90 to-amber-900/90 text-yellow-200 p-6 mt-4 rounded-xl shadow-lg border-2 border-yellow-400/60"
              >
                <div className="flex items-center gap-3 mb-4">
                  <BrainCircuit className="w-6 h-6 animate-spin" />
                  <span className="font-bold text-lg">💎 Mining your PREMIUM genetic gold deposits... ⛏️✨</span>
                </div>
                <div className="space-y-4">
                  <div className="text-center">
                    <p className="text-yellow-200 font-medium">{currentStep || '🌟 Processing your LEGENDARY genetic data...'}</p>
                  </div>
                  <div className="w-full bg-yellow-800 rounded-full h-3 overflow-hidden border border-yellow-400/50">
                    <div 
                      className="h-full bg-gradient-to-r from-yellow-300 via-amber-300 to-yellow-400 rounded-full transition-all duration-500 ease-out shadow-lg shadow-yellow-400/50"
                      style={{width: `${analysisProgress}%`}}
                    ></div>
                  </div>
                  <div className="text-center text-sm text-yellow-300 font-bold">
                    {analysisProgress}% Complete
                  </div>
                  <div className="grid grid-cols-2 gap-3 text-sm">
                    <div className="flex items-center gap-2">
                      <Zap className="w-4 h-4" />
                      <span>⛏️ Reading golden markers</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <Database className="w-4 h-4" />
                      <span>📚 Premium database scan</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <TrendingUp className="w-4 h-4" />
                      <span>💰 Golden ratio calculation</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <Sparkles className="w-4 h-4 animate-pulse" />
                      <span>💎 Diamond hands verification</span>
                    </div>
                  </div>
                </div>
              </motion.div>
            )}
            
            {error && (
              <motion.div
                initial={{ opacity: 0, y: -10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5 }}
                className="bg-red-900 text-red-300 p-4 mt-4 rounded-xl shadow-lg flex items-center gap-2"
              >
                <AlertCircle className="w-5 h-5" />
                💥 Error: {error}
              </motion.div>
            )}
          </div>
        </CardContent>
      </Card>

      {showReport && (
        <motion.div
          initial={{ y: 50, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          transition={{ duration: 0.8 }}
          className="max-w-2xl mx-auto mt-8 sm:mt-12 p-4 sm:p-6 bg-gradient-to-br from-yellow-900/90 to-amber-900/90 backdrop-blur-sm rounded-xl border-2 border-yellow-400 shadow-2xl shadow-yellow-400/40 relative z-10"
        >
          <h2 className="text-3xl font-bold bg-gradient-to-r from-yellow-300 to-amber-300 bg-clip-text text-transparent text-center mb-6 flex items-center justify-center gap-3">
            <Crown className="w-8 h-8 text-yellow-400" />
            💎 PREMIUM GENETIC GOLD REPORT 📊
            <Gem className="w-8 h-8 text-amber-400" />
          </h2>
          <div className="space-y-4">
            <div className="flex items-center justify-between p-3 bg-gradient-to-r from-yellow-900/70 to-amber-900/70 rounded-lg border-2 border-yellow-400/50 shadow-lg">
              <div className="flex items-center gap-3">
                <Star className="w-5 h-5 text-yellow-300" />
                <span className="text-white font-bold">🔥 Golden Risk Appetite</span>
              </div>
              <div className="flex items-center gap-3">
                <div className="w-32 h-2 bg-yellow-800 rounded-full overflow-hidden border border-yellow-400/50">
                  <div 
                    className="h-full bg-gradient-to-r from-yellow-400 to-amber-400 transition-all duration-1000 shadow-lg"
                    style={{ width: `${yoloMetrics.riskApeIndex}%` }}
                  ></div>
                </div>
                <span className="text-yellow-300 font-bold min-w-[3rem]">{yoloMetrics.riskApeIndex}%</span>
              </div>
            </div>
            
            <div className="flex items-center justify-between p-3 bg-gradient-to-r from-amber-900/70 to-yellow-900/70 rounded-lg border-2 border-amber-400/50 shadow-lg">
              <div className="flex items-center gap-3">
                <Crown className="w-5 h-5 text-amber-300" />
                <span className="text-white font-bold">👑 Royal Discipline Power</span>
              </div>
              <div className="flex items-center gap-3">
                <div className="w-32 h-2 bg-yellow-800 rounded-full overflow-hidden border border-yellow-400/50">
                  <div 
                    className="h-full bg-gradient-to-r from-amber-400 to-yellow-400 transition-all duration-1000 shadow-lg"
                    style={{ width: `${yoloMetrics.disciplineFactor}%` }}
                  ></div>
                </div>
                <span className="text-amber-300 font-bold min-w-[3rem]">{yoloMetrics.disciplineFactor}%</span>
              </div>
            </div>
            
            <div className="flex items-center justify-between p-3 bg-gradient-to-r from-yellow-900/70 to-amber-900/70 rounded-lg border-2 border-yellow-400/50 shadow-lg">
              <div className="flex items-center gap-3">
                <Gem className="w-5 h-5 text-yellow-300" />
                <span className="text-white font-bold">💎 Legendary Diamond Hands DNA</span>
              </div>
              <div className="flex items-center gap-3">
                <div className="w-32 h-2 bg-yellow-800 rounded-full overflow-hidden border border-yellow-400/50">
                  <div 
                    className="h-full bg-gradient-to-r from-yellow-400 to-amber-300 transition-all duration-1000 shadow-lg"
                    style={{ width: `${yoloMetrics.diamondHandsDNA}%` }}
                  ></div>
                </div>
                <span className="text-yellow-300 font-bold min-w-[3rem]">{yoloMetrics.diamondHandsDNA}%</span>
              </div>
            </div>
            
            <div className="flex items-center justify-between p-3 bg-gradient-to-r from-amber-900/70 to-yellow-900/70 rounded-lg border-2 border-amber-400/50 shadow-lg">
              <div className="flex items-center gap-3">
                <AlertCircle className="w-5 h-5 text-amber-300" />
                <span className="text-white font-bold">⚠️ Golden Panic Resistance</span>
              </div>
              <div className="flex items-center gap-3">
                <div className="w-32 h-2 bg-yellow-800 rounded-full overflow-hidden border border-yellow-400/50">
                  <div 
                    className="h-full bg-gradient-to-r from-amber-400 to-yellow-400 transition-all duration-1000 shadow-lg"
                    style={{ width: `${yoloMetrics.panicSellPropensity}%` }}
                  ></div>
                </div>
                <span className="text-amber-300 font-bold min-w-[3rem]">{yoloMetrics.panicSellPropensity}%</span>
              </div>
            </div>
            
            <div className="flex items-center justify-center p-4 bg-gradient-to-r from-yellow-900/70 to-amber-900/70 rounded-lg border-2 border-yellow-400 shadow-lg">
              <Trophy className="w-6 h-6 text-yellow-400 mr-3" />
              <span className="text-yellow-400 font-bold text-lg">🏆 Premium Strategy Fit: {yoloMetrics.valueVersusMomentum}</span>
            </div>
          </div>
          <div className="mt-6 flex justify-center animate-bounce">
            <Gem className="w-10 h-10 text-yellow-400 animate-pulse" />
          </div>
          <div className="mt-6 text-center space-y-4">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 sm:gap-4 max-w-md mx-auto">
              <div className="bg-gradient-to-br from-yellow-900/70 to-amber-900/70 p-3 rounded-lg border-2 border-yellow-400/50 shadow-lg">
                <div className="text-yellow-300 text-sm">⛏️ Golden Markers Analyzed</div>
                <div className="text-white font-bold text-xl">{yoloMetrics.totalSnpsAnalyzed.toLocaleString()}</div>
              </div>
              <div className="bg-gradient-to-br from-amber-900/70 to-yellow-900/70 p-3 rounded-lg border-2 border-amber-400/50 shadow-lg">
                <div className="text-amber-300 text-sm">💎 Premium Discoveries</div>
                <div className="text-white font-bold text-xl">{yoloMetrics.significantFindings}</div>
              </div>
            </div>
            <div className="bg-gradient-to-r from-yellow-900/70 to-amber-900/70 p-4 rounded-lg border-2 border-yellow-400 shadow-lg">
              <p className="text-yellow-300 text-xl font-bold">
                💰 CONFIRMED GOLDEN GENES! Premium tendies incoming! 🏆✨
              </p>
            </div>
            
            {sessionId && (
              <Button
                onClick={downloadResults}
                className="mt-4 bg-purple-600 hover:bg-purple-500 text-white font-bold py-2 px-4 rounded-lg flex items-center gap-2 mx-auto"
              >
                <Download className="w-4 h-4" />
                Download Full Report
              </Button>
            )}
          </div>
        </motion.div>
      )}

      {showReport && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 1, duration: 0.6 }}
          className="max-w-4xl mx-auto mt-8 sm:mt-16 p-4 sm:p-6 bg-gradient-to-br from-yellow-900/90 to-amber-900/90 backdrop-blur-sm border-2 border-yellow-400 rounded-xl shadow-2xl shadow-yellow-400/40 relative z-10"
        >
          <h3 className="text-2xl bg-gradient-to-r from-yellow-300 to-amber-300 bg-clip-text text-transparent font-bold text-center mb-4 flex items-center justify-center gap-3">
            <Crown className="w-7 h-7 text-yellow-400" />
            👑 GOLDEN LEGENDS LEADERBOARD
            <Gem className="w-7 h-7 text-amber-400" />
          </h3>
          <div className="space-y-3">
            {leaderboard.map((ape, idx) => (
              <div key={idx} className="flex items-center justify-between p-4 bg-gradient-to-r from-yellow-900/80 to-amber-900/80 rounded-lg border-2 border-yellow-400/50 hover:border-yellow-400/80 transition-all duration-300 shadow-lg hover:shadow-yellow-400/30">
                <div className="flex items-center gap-3">
                  <div className="flex items-center justify-center w-8 h-8 bg-gradient-to-r from-yellow-400 to-amber-400 text-black font-bold rounded-full text-sm border-2 border-yellow-300 shadow-lg">
                    #{idx + 1}
                  </div>
                  <div>
                    <div className="flex items-center gap-2">
                      <Crown className="w-4 h-4 text-yellow-300" />
                      <span className="text-white font-bold">{ape.name}</span>
                    </div>
                    <div className="text-amber-300 text-sm font-semibold">{ape.title}</div>
                    <div className="text-yellow-300 text-xs">⛏️ {ape.snps?.toLocaleString()} golden markers analyzed</div>
                  </div>
                </div>
                <div className="text-right">
                  <div className="text-yellow-400 font-bold text-xl">{ape.score}%</div>
                  <div className="text-amber-300 text-sm font-semibold">💰 Golden Score</div>
                </div>
              </div>
            ))}
          </div>
        </motion.div>
      )}

      {/* Top Genetic Findings */}
      {showReport && topFindings.length > 0 && (
        <motion.div
          initial={{ y: 50, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          transition={{ duration: 0.8, delay: 0.5 }}
          className="max-w-6xl mx-auto mt-8 sm:mt-12 p-4 sm:p-6 bg-zinc-800/90 backdrop-blur-sm rounded-xl border border-green-500 shadow-2xl shadow-green-500/20 relative z-10"
        >
          <div className="text-center mb-8">
            <h2 className="text-3xl font-bold text-green-400 mb-2 flex items-center justify-center gap-3">
              <BrainCircuit className="w-7 h-7" />
              🧬 Top Genetic Alpha Signals 📊
            </h2>
            <p className="text-gray-300 text-lg">Your most significant genetic markers for trading behavior</p>
          </div>
          <div className="grid gap-4 sm:gap-6 md:grid-cols-2 lg:grid-cols-3">
            {topFindings.slice(0, 6).map((finding, idx) => (
              <motion.div 
                key={idx} 
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: idx * 0.1, duration: 0.5 }}
                className="bg-zinc-900 p-5 rounded-lg border border-purple-500/50 hover:border-purple-500 transition-all duration-300 hover:shadow-lg hover:shadow-purple-500/20"
              >
                <div className="flex items-center justify-between mb-3">
                  <div className="flex items-center gap-2">
                    <Activity className="w-4 h-4 text-purple-400" />
                    <span className="text-purple-400 font-bold text-lg">{finding.rsid}</span>
                  </div>
                  <div className="bg-yellow-900/50 px-2 py-1 rounded border border-yellow-500/30">
                    <span className="text-yellow-300 font-bold text-sm">
                      Mag: {finding.magnitude?.toFixed(1)}
                    </span>
                  </div>
                </div>
                <div className="mb-3 p-2 bg-zinc-800 rounded border border-pink-500/30">
                  <span className="text-gray-300 text-sm">Your DNA: </span>
                  <span className="text-pink-400 font-mono font-bold text-lg">{finding.genotype}</span>
                </div>
                {finding.repute && (
                  <div className="mb-3">
                    <span className={`px-3 py-1 rounded-full text-xs font-bold ${
                      finding.repute.toLowerCase().includes('good') 
                        ? 'bg-green-900/70 text-green-300 border border-green-500/50' 
                        : finding.repute.toLowerCase().includes('bad')
                        ? 'bg-red-900/70 text-red-300 border border-red-500/50'
                        : 'bg-yellow-900/70 text-yellow-300 border border-yellow-500/50'
                    }`}>
                      {finding.repute}
                    </span>
                  </div>
                )}
                <p className="text-gray-300 text-sm leading-relaxed mb-3">
                  {finding.summary && finding.summary.length > 120 
                    ? `${finding.summary.substring(0, 120)}...` 
                    : finding.summary}
                </p>
                {finding.interpretation && (
                  <div className="p-3 bg-blue-900/30 rounded border border-blue-500/30">
                    <p className="text-blue-300 text-sm italic">
                      <strong>Your genotype:</strong> {finding.interpretation.length > 100 
                        ? `${finding.interpretation.substring(0, 100)}...` 
                        : finding.interpretation}
                    </p>
                  </div>
                )}
              </motion.div>
            ))}
          </div>
          {topFindings.length > 6 && (
            <p className="text-center text-gray-400 mt-4">
              And {topFindings.length - 6} more significant findings in your full report...
            </p>
          )}
        </motion.div>
      )}

      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 1.2, duration: 0.6 }}
        className="text-center mt-8 sm:mt-16 text-lg sm:text-xl text-yellow-300 px-4 relative z-10"
      >
        <p className="text-2xl font-bold bg-gradient-to-r from-yellow-300 to-amber-300 bg-clip-text text-transparent">⛏️ Mine. Analyze. Ascend to Golden Glory. 👑</p>
        <p className="text-lg mt-2">🌟 Your PREMIUM genetic gold deposits have been discovered! No force on Earth can stop your DNA-coded golden tendies now! 💰✨</p>
        <div className="mt-4 p-4 bg-gradient-to-r from-yellow-900/70 to-amber-900/70 rounded-lg border-2 border-yellow-400/50 max-w-2xl mx-auto shadow-lg">
          <p className="text-yellow-300 text-sm">💎 <strong>Golden Tip:</strong> Your LEGENDARY genetic analysis reveals premium behavioral tendencies. This luxurious experience is for entertainment purposes only - trade responsibly, golden legend! 👑</p>
        </div>
        <div className="mt-6 flex justify-center items-center gap-4">
          <Crown className="w-8 h-8 text-yellow-400 animate-pulse" />
          <Gem className="w-8 h-8 text-amber-400 animate-bounce" />
          <Star className="w-8 h-8 text-yellow-300 animate-pulse" />
        </div>
      </motion.div>
    </div>
  );
}
