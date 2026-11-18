import React from 'react';

export const SystemHealthView: React.FC = () => {
  return (
    <div className="space-y-5">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="text-[#50d5d0] text-[10px] tracking-widest uppercase font-bold">
            Reliability & governance
          </div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-100 mt-1">
            System Health
          </h1>
          <p className="text-xs text-[#91a0b5] mt-0.5">
            Monitor data freshness, pipeline execution, model status and service availability.
          </p>
        </div>
        <button className="border border-[#243247] bg-[#172437] hover:bg-[#1f314a] text-slate-200 px-3 py-1.5 rounded-lg text-xs transition">
          View operational runbook
        </button>
      </div>

      {/* KPIs */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3.5">
        <div className="bg-gradient-to-br from-[#131e2d] to-[#101925] border border-[#243247] rounded-xl p-4 shadow-lg">
          <div className="text-[11px] text-[#91a0b5]">Platform status</div>
          <div className="text-xl font-bold tracking-tight text-[#65d6a4] my-1">
            Operational
          </div>
          <div className="text-[10px] text-[#91a0b5]">All core services healthy</div>
        </div>

        <div className="bg-gradient-to-br from-[#131e2d] to-[#101925] border border-[#243247] rounded-xl p-4 shadow-lg">
          <div className="text-[11px] text-[#91a0b5]">Data pipeline success</div>
          <div className="text-2xl font-bold tracking-tight text-slate-100 my-1">98.6%</div>
          <div className="text-[10px] text-[#91a0b5]">Rolling 30-day pipeline executions</div>
        </div>

        <div className="bg-gradient-to-br from-[#131e2d] to-[#101925] border border-[#243247] rounded-xl p-4 shadow-lg">
          <div className="text-[11px] text-[#91a0b5]">Latest data freshness</div>
          <div className="text-2xl font-bold tracking-tight text-slate-100 my-1">
            4 <small className="text-xs font-normal text-[#91a0b5]">min</small>
          </div>
          <div className="text-[10px] text-[#91a0b5]">Exchange tick ingestion lag</div>
        </div>

        <div className="bg-gradient-to-br from-[#131e2d] to-[#101925] border border-[#243247] rounded-xl p-4 shadow-lg">
          <div className="text-[11px] text-[#91a0b5]">Model version</div>
          <div className="text-xl font-bold tracking-tight text-slate-100 my-1">0.3.1</div>
          <div className="text-[10px] text-[#91a0b5]">Production MLflow model registry</div>
        </div>
      </div>

      {/* Service Components & Pipeline Runs */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-3.5">
        {/* Service Components */}
        <div className="bg-gradient-to-br from-[#131e2d] to-[#101925] border border-[#243247] rounded-xl p-4 shadow-lg">
          <div className="flex justify-between items-center mb-3">
            <h3 className="text-xs font-semibold text-slate-100">Service components</h3>
            <span className="text-[10px] text-[#91a0b5]">Live health telemetry</span>
          </div>

          <div className="divide-y divide-[#243247] text-xs">
            <div className="py-2.5 flex justify-between items-center">
              <span className="flex items-center gap-2 text-slate-300">
                <i className="w-2 h-2 rounded-full bg-[#65d6a4]"></i>
                API service · FastAPI
              </span>
              <b className="text-[#65d6a4] font-semibold">Healthy (127.0.0.1:8000)</b>
            </div>

            <div className="py-2.5 flex justify-between items-center">
              <span className="flex items-center gap-2 text-slate-300">
                <i className="w-2 h-2 rounded-full bg-[#65d6a4]"></i>
                Relational & vector store · PostgreSQL + pgvector
              </span>
              <b className="text-[#65d6a4] font-semibold">Healthy</b>
            </div>

            <div className="py-2.5 flex justify-between items-center">
              <span className="flex items-center gap-2 text-slate-300">
                <i className="w-2 h-2 rounded-full bg-[#65d6a4]"></i>
                Batch orchestration · Apache Airflow
              </span>
              <b className="text-[#65d6a4] font-semibold">Healthy (DAG active)</b>
            </div>

            <div className="py-2.5 flex justify-between items-center">
              <span className="flex items-center gap-2 text-slate-300">
                <i className="w-2 h-2 rounded-full bg-[#f4bd62]"></i>
                Event transport · Redpanda (Streaming)
              </span>
              <b className="text-[#f4bd62] font-semibold">Standby profile</b>
            </div>

            <div className="py-2.5 flex justify-between items-center">
              <span className="flex items-center gap-2 text-slate-300">
                <i className="w-2 h-2 rounded-full bg-[#65d6a4]"></i>
                Model registry · MLflow
              </span>
              <b className="text-[#65d6a4] font-semibold">Healthy (v0.3.1 staged)</b>
            </div>

            <div className="py-2.5 flex justify-between items-center">
              <span className="flex items-center gap-2 text-slate-300">
                <i className="w-2 h-2 rounded-full bg-[#65d6a4]"></i>
                LLM provider adapter · Groq / Offline RAG
              </span>
              <b className="text-[#65d6a4] font-semibold">Configured & Grounded</b>
            </div>
          </div>
        </div>

        {/* Recent Pipeline Runs */}
        <div className="bg-gradient-to-br from-[#131e2d] to-[#101925] border border-[#243247] rounded-xl p-4 shadow-lg">
          <div className="flex justify-between items-center mb-3">
            <h3 className="text-xs font-semibold text-slate-100">Recent pipeline runs</h3>
            <span className="text-[10px] text-[#91a0b5]">Execution history</span>
          </div>

          <div className="divide-y divide-[#243247] text-xs">
            <div className="py-2.5 flex justify-between items-center">
              <span className="text-slate-300">Market data ingestion (Bhavcopy)</span>
              <b className="text-[#65d6a4] font-semibold">Success · 09:05</b>
            </div>

            <div className="py-2.5 flex justify-between items-center">
              <span className="text-slate-300">Data quality validation</span>
              <b className="text-[#65d6a4] font-semibold">Success · 09:08</b>
            </div>

            <div className="py-2.5 flex justify-between items-center">
              <span className="text-slate-300">Feature engineering & rolling z-scores</span>
              <b className="text-[#65d6a4] font-semibold">Success · 09:11</b>
            </div>

            <div className="py-2.5 flex justify-between items-center">
              <span className="text-slate-300">Anomaly scoring (IForest)</span>
              <b className="text-[#65d6a4] font-semibold">Success · 09:13</b>
            </div>

            <div className="py-2.5 flex justify-between items-center">
              <span className="text-slate-300">News enrichment (FinBERT)</span>
              <b className="text-[#65d6a4] font-semibold">Success · 09:16</b>
            </div>

            <div className="py-2.5 flex justify-between items-center">
              <span className="text-slate-300">Alert generation & priority ranking</span>
              <b className="text-[#65d6a4] font-semibold">Success · 09:18</b>
            </div>
          </div>
        </div>
      </div>

      {/* Governance & Operational Safeguards */}
      <div className="bg-gradient-to-br from-[#131e2d] to-[#101925] border border-[#243247] rounded-xl p-4 shadow-lg">
        <h3 className="text-xs font-semibold text-slate-100 mb-3">
          Governance & operational safeguards
        </h3>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 text-xs">
          <div className="border border-[#243247] rounded-lg p-3 bg-[#0d1724]">
            <b className="text-slate-100 block">Data lineage</b>
            <p className="text-[11px] text-[#91a0b5] mt-1 leading-relaxed">
              Source identifiers, timestamps, transformation versions and data-quality outcomes are traceable to disk.
            </p>
          </div>

          <div className="border border-[#243247] rounded-lg p-3 bg-[#0d1724]">
            <b className="text-slate-100 block">Model monitoring</b>
            <p className="text-[11px] text-[#91a0b5] mt-1 leading-relaxed">
              Track Evidently drift metrics, alert volume distributions, false-positive feedback, and model registry changes.
            </p>
          </div>

          <div className="border border-[#243247] rounded-lg p-3 bg-[#0d1724]">
            <b className="text-slate-100 block">LLM governance</b>
            <p className="text-[11px] text-[#91a0b5] mt-1 leading-relaxed">
              Record prompt version, token usage, retrieved evidence, and 100% citation grounding checks. Zero hallucination.
            </p>
          </div>

          <div className="border border-[#243247] rounded-lg p-3 bg-[#0d1724]">
            <b className="text-slate-100 block">Security & RBAC</b>
            <p className="text-[11px] text-[#91a0b5] mt-1 leading-relaxed">
              Protect API credentials, enforce JWT role-based access, and maintain an immutable analyst review trail.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};
