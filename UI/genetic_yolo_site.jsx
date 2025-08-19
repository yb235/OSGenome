import React, { useState, useRef } from "react";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Upload, Sparkles, BrainCircuit, Trophy, BarChart3, Rocket, Users, AlertCircle, CheckCircle, Download } from "lucide-react";
import { motion } from "framer-motion";

// API configuration
const API_BASE_URL = 'http://localhost:5000/api';

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
  { name: "DiamondDave69", score: 99, title: "King of YOLOs" },
  { name: "TendieTycoon", score: 95, title: "Degen Day Trader" },
  { name: "BuffetDNA", score: 92, title: "Value Mutant" },
  { name: "MemeETF", score: 89, title: "ETF YOLOer" },
  { name: "HODLchimp", score: 87, title: "Monkey Monk" },
];

export default function GeneticYOLOPage() {
  const [sessionId, setSessionId] = useState(null);
  const [analysisStatus, setAnalysisStatus] = useState('idle'); // idle, uploading, analyzing, completed, error
  const [yoloMetrics, setYoloMetrics] = useState(defaultYoloMetrics);
  const [topFindings, setTopFindings] = useState([]);
  const [error, setError] = useState(null);
  const [fileName, setFileName] = useState('');
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
      
      // Update state with results
      setYoloMetrics(analysisResult.yolo_metrics);
      setTopFindings(analysisResult.top_findings || []);
      setAnalysisStatus('completed');

    } catch (err) {
      setError(err.message);
      setAnalysisStatus('error');
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
    <div className="min-h-screen bg-black text-white p-6 font-mono">
      <motion.h1
        initial={{ y: -50, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        transition={{ duration: 0.6 }}
        className="text-4xl md:text-6xl font-bold text-center text-yellow-400 mb-8"
      >
        YOLOING INTO GENETICS, BOYS — GME FOR YOUR GENES 🔬🚀
      </motion.h1>

      <motion.p
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.3, duration: 0.6 }}
        className="text-center text-lg md:text-2xl max-w-3xl mx-auto mb-10"
      >
        Alright listen up you smooth-brained apes 🧠🦍 — what if I told you there’s a way to upload your DNA and figure out if you’re a paper-handed pansy or a giga-chad with diamond hands 💎🙌 coded into your chromosomes?
      </motion.p>

      <motion.p
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.5, duration: 0.6 }}
        className="text-center text-lg md:text-xl max-w-3xl mx-auto mb-10 text-green-400"
      >
        🚨 THE ULTIMATE GENETIC YOLO PLATFORM 🚨
      </motion.p>

      <motion.p
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.7, duration: 0.6 }}
        className="text-center text-base md:text-lg max-w-3xl mx-auto mb-10"
      >
        You just drop your <span className="text-pink-400">23andMe</span> file or whatever science juice you've got 🧬, and our offline black-box quantum ape brain runs it through an alpha-seeking database from the fifth dimension (probably trained on Buffet’s toenail clippings or some shit).
      </motion.p>

      <Card className="max-w-xl mx-auto bg-zinc-900 border-yellow-500 border-2">
        <CardContent className="p-6">
          <div className="flex flex-col items-center gap-4">
            <Upload className="w-12 h-12 text-green-400 animate-bounce" />
            <p className="text-center text-white text-xl">
              Drop your <span className="text-pink-400">DNA file</span> and let's get freaky with the genome
            </p>
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
              className="bg-yellow-500 hover:bg-yellow-400 text-black font-bold py-2 px-6 rounded-xl text-lg disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isLoading ? 'Processing...' : 'Upload & Analyze'} 🔍
            </Button>
            {/* Status Messages */}
            {analysisStatus === 'uploading' && (
              <motion.div
                initial={{ opacity: 0, y: -10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5 }}
                className="bg-blue-900 text-blue-300 p-4 mt-4 rounded-xl shadow-lg flex items-center gap-2"
              >
                <Upload className="w-5 h-5 animate-bounce" />
                📁 Uploading {fileName}... Preparing for genetic YOLO analysis.
              </motion.div>
            )}
            
            {analysisStatus === 'analyzing' && (
              <motion.div
                initial={{ opacity: 0, y: -10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5 }}
                className="bg-green-900 text-green-300 p-4 mt-4 rounded-xl shadow-lg flex items-center gap-2"
              >
                <BrainCircuit className="w-5 h-5 animate-spin" />
                🧬 Analyzing your genetic YOLO potential... Checking for diamond hands DNA.
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
          className="max-w-2xl mx-auto mt-12 p-6 bg-zinc-800 rounded-xl border border-purple-500"
        >
          <h2 className="text-3xl font-bold text-purple-400 text-center mb-6">
            🧬 Genetic YOLO Report 📊
          </h2>
          <ul className="space-y-3 text-lg text-white">
            <li>
              <BarChart3 className="inline-block mr-2 text-yellow-300" />
              <strong>Risk Ape Index:</strong> {yoloMetrics.riskApeIndex}%
            </li>
            <li>
              <BarChart3 className="inline-block mr-2 text-yellow-300" />
              <strong>Discipline Factor:</strong> {yoloMetrics.disciplineFactor}%
            </li>
            <li>
              <BarChart3 className="inline-block mr-2 text-yellow-300" />
              <strong>Diamond Hands DNA:</strong> {yoloMetrics.diamondHandsDNA}%
            </li>
            <li>
              <BarChart3 className="inline-block mr-2 text-yellow-300" />
              <strong>Panic Sell Propensity:</strong> {yoloMetrics.panicSellPropensity}%
            </li>
            <li>
              <Trophy className="inline-block mr-2 text-green-400" />
              <strong>Strategy Fit:</strong> {yoloMetrics.valueVersusMomentum}
            </li>
          </ul>
          <div className="mt-6 flex justify-center animate-bounce">
            <Rocket className="w-10 h-10 text-pink-400" />
          </div>
          <div className="mt-6 text-center">
            <p className="text-pink-300 text-lg mb-2">
              📊 Analyzed {yoloMetrics.totalSnpsAnalyzed.toLocaleString()} SNPs
            </p>
            <p className="text-green-300 text-lg mb-2">
              🔬 Found {yoloMetrics.significantFindings} significant genetic markers
            </p>
            <p className="text-pink-300 text-xl font-bold">
              🚀 Confirmed YOLO Ape. Tendies inbound. 🍗📈
            </p>
            
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
          className="max-w-3xl mx-auto mt-16 p-6 bg-zinc-900 border border-yellow-500 rounded-xl"
        >
          <h3 className="text-2xl text-yellow-300 font-bold text-center mb-4">
            🏆 Stonk Ape Leaderboard
          </h3>
          <ul className="space-y-3 text-white text-lg">
            {leaderboard.map((ape, idx) => (
              <li key={idx} className="flex items-center justify-between">
                <span>
                  <Users className="inline-block w-5 h-5 mr-2 text-blue-300" />
                  <strong>{ape.name}</strong> — <em>{ape.title}</em>
                </span>
                <span className="text-green-400 font-bold">{ape.score}</span>
              </li>
            ))}
          </ul>
        </motion.div>
      )}

      {/* Top Genetic Findings */}
      {showReport && topFindings.length > 0 && (
        <motion.div
          initial={{ y: 50, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          transition={{ duration: 0.8, delay: 0.5 }}
          className="max-w-4xl mx-auto mt-12 p-6 bg-zinc-800 rounded-xl border border-green-500"
        >
          <h2 className="text-2xl font-bold text-green-400 text-center mb-6 flex items-center justify-center gap-2">
            <BrainCircuit className="w-6 h-6" />
            🧬 Top Genetic Alpha Signals 📊
          </h2>
          <div className="grid gap-4 md:grid-cols-2">
            {topFindings.slice(0, 6).map((finding, idx) => (
              <div key={idx} className="bg-zinc-900 p-4 rounded-lg border border-purple-500">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-purple-400 font-bold text-lg">{finding.rsid}</span>
                  <span className="text-yellow-300 font-bold">
                    Mag: {finding.magnitude?.toFixed(1)}
                  </span>
                </div>
                <div className="mb-2">
                  <span className="text-white">Your DNA: </span>
                  <span className="text-pink-400 font-mono">{finding.genotype}</span>
                </div>
                {finding.repute && (
                  <div className="mb-2">
                    <span className={`px-2 py-1 rounded text-xs font-bold ${
                      finding.repute.toLowerCase().includes('good') 
                        ? 'bg-green-900 text-green-300' 
                        : finding.repute.toLowerCase().includes('bad')
                        ? 'bg-red-900 text-red-300'
                        : 'bg-yellow-900 text-yellow-300'
                    }`}>
                      {finding.repute}
                    </span>
                  </div>
                )}
                <p className="text-gray-300 text-sm">
                  {finding.summary && finding.summary.length > 100 
                    ? `${finding.summary.substring(0, 100)}...` 
                    : finding.summary}
                </p>
                {finding.interpretation && (
                  <p className="text-blue-300 text-sm mt-2 italic">
                    Your genotype: {finding.interpretation.length > 80 
                      ? `${finding.interpretation.substring(0, 80)}...` 
                      : finding.interpretation}
                  </p>
                )}
              </div>
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
        className="text-center mt-16 text-xl text-pink-300"
      >
        <p>Upload. Analyze. Ascend. No hedge fund can stop your DNA-coded tendies now. 🍗📈</p>
        <div className="mt-6 flex justify-center items-center gap-4">
          <Sparkles className="w-8 h-8 text-yellow-400 animate-pulse" />
          <BrainCircuit className="w-8 h-8 text-purple-400 animate-spin" />
          <Sparkles className="w-8 h-8 text-yellow-400 animate-pulse" />
        </div>
      </motion.div>
    </div>
  );
}
