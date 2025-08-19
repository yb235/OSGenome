import React, { useState } from "react";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Upload, Sparkles, BrainCircuit, Trophy, BarChart3, Rocket, Users } from "lucide-react";
import { motion } from "framer-motion";

const mockStonkScore = {
  riskApeIndex: 97,
  disciplineFactor: 62,
  diamondHandsDNA: 88,
  panicSellPropensity: 11,
  valueVersusMomentum: "Momentum YOLO Ape",
};

const leaderboard = [
  { name: "DiamondDave69", score: 99, title: "King of YOLOs" },
  { name: "TendieTycoon", score: 95, title: "Degen Day Trader" },
  { name: "BuffetDNA", score: 92, title: "Value Mutant" },
  { name: "MemeETF", score: 89, title: "ETF YOLOer" },
  { name: "HODLchimp", score: 87, title: "Monkey Monk" },
];

export default function GeneticYOLOPage() {
  const [uploaded, setUploaded] = useState(false);
  const [showReport, setShowReport] = useState(false);

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
            <Button
              onClick={() => {
                setUploaded(true);
                setTimeout(() => setShowReport(true), 2000);
              }}
              className="bg-yellow-500 hover:bg-yellow-400 text-black font-bold py-2 px-6 rounded-xl text-lg"
            >
              Upload & Analyze 🔍
            </Button>
            {uploaded && !showReport && (
              <motion.div
                initial={{ opacity: 0, y: -10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5 }}
                className="bg-green-900 text-green-300 p-4 mt-4 rounded-xl shadow-lg"
              >
                🧬 Stonk DNA Uploaded. Analysis in Progress... Welcome to the Stonkiverse.
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
              <strong>Risk Ape Index:</strong> {mockStonkScore.riskApeIndex}%
            </li>
            <li>
              <BarChart3 className="inline-block mr-2 text-yellow-300" />
              <strong>Discipline Factor:</strong> {mockStonkScore.disciplineFactor}%
            </li>
            <li>
              <BarChart3 className="inline-block mr-2 text-yellow-300" />
              <strong>Diamond Hands DNA:</strong> {mockStonkScore.diamondHandsDNA}%
            </li>
            <li>
              <BarChart3 className="inline-block mr-2 text-yellow-300" />
              <strong>Panic Sell Propensity:</strong> {mockStonkScore.panicSellPropensity}%
            </li>
            <li>
              <Trophy className="inline-block mr-2 text-green-400" />
              <strong>Strategy Fit:</strong> {mockStonkScore.valueVersusMomentum}
            </li>
          </ul>
          <div className="mt-6 flex justify-center animate-bounce">
            <Rocket className="w-10 h-10 text-pink-400" />
          </div>
          <p className="text-center text-pink-300 mt-4 text-xl">
            🚀 Confirmed YOLO Ape. Tendies inbound. 🍗📈
          </p>
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
