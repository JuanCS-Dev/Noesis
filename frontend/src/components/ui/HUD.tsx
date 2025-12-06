"use client";

import { motion } from "framer-motion";
import { Activity, ShieldCheck, Cpu, Brain } from "lucide-react";

export default function HUD({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex flex-col h-full w-full p-6 pointer-events-auto">
      {/* Top Bar - Metrics */}
      <header className="flex justify-between items-center mb-6">
        <div className="flex items-center gap-4">
          <Metric label="INTEGRITY" value="99.9%" icon={<ShieldCheck className="w-4 h-4 text-green-400" />} color="border-green-500/30" />
          <Metric label="COGNITION" value="ACTIVE" icon={<Brain className="w-4 h-4 text-purple-400" />} color="border-purple-500/30" />
        </div>
        
        <div className="flex items-center gap-4">
           <Metric label="CPU LOAD" value="12%" icon={<Cpu className="w-4 h-4 text-cyan-400" />} color="border-cyan-500/30" />
           <div className="text-xs text-slate-500 font-mono">v4.0.1-alpha</div>
        </div>
      </header>

      {/* Main Content Area (Graph + Chat) */}
      <div className="flex-1 relative flex gap-6 overflow-hidden">
        {children}
      </div>
    </div>
  );
}

function Metric({ label, value, icon, color }: { label: string, value: string, icon: any, color: string }) {
  return (
    <motion.div 
      initial={{ opacity: 0, y: -20 }}
      animate={{ opacity: 1, y: 0 }}
      className={`glass-panel px-4 py-2 rounded-sm flex items-center gap-3 border-l-2 ${color}`}
    >
      {icon}
      <div className="flex flex-col leading-none">
        <span className="text-[10px] text-slate-400 tracking-wider">{label}</span>
        <span className="text-sm font-bold text-slate-100">{value}</span>
      </div>
    </motion.div>
  );
}
