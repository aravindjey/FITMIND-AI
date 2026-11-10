'use client';
import { useEffect, useState } from 'react';
import { apiClient } from '@/lib/api-client';
import { Camera, Sparkles, ShieldAlert, AlertCircle } from 'lucide-react';

export default function BodyAnalysisPage() {
  const [photos, setPhotos] = useState<any[]>([]);
  const [latestAnalysis, setLatestAnalysis] = useState<any | null>(null);
  const [loading, setLoading] = useState(true);
  const [analyzing, setAnalyzing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [photoType, setPhotoType] = useState('front');
  const [weightAtCapture, setWeightAtCapture] = useState(72);
  const [filename, setFilename] = useState('front_progress_pose.jpg');

  const loadPhotos = async () => {
    setLoading(true);
    try {
      const [pRes, profRes] = await Promise.all([
        apiClient.listProgressPhotos(),
        apiClient.getProfile().catch(() => null),
      ]);
      setPhotos(pRes || []);
      if (pRes?.length > 0 && !latestAnalysis) {
        setLatestAnalysis(pRes[0]);
      }
      if (profRes?.current_weight_kg) {
        setWeightAtCapture(profRes.current_weight_kg);
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadPhotos();
  }, []);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      setFilename(file.name);
    }
  };

  const handleAnalyze = async (e: React.FormEvent) => {
    e.preventDefault();
    setAnalyzing(true);
    setError(null);
    try {
      const res = await apiClient.analyzeProgressPhoto({
        photo_type: photoType,
        weight_at_capture_kg: Number(weightAtCapture),
        filename,
      });
      setLatestAnalysis(res);
      await loadPhotos();
    } catch (err: any) {
      setError(err.message || 'Failed to analyze progress photo');
    } finally {
      setAnalyzing(false);
    }
  };

  if (loading) {
    return <div className="p-12 text-center text-gray-400">Loading Qualitative Body Photo Analyzer...</div>;
  }

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-bold text-white">Qualitative Body Composition & Posture Analysis</h1>
        <p className="text-sm text-gray-400">
          Multimodal progress photo inspection with explicit uncertainty disclaimers and non-diagnostic observations
        </p>
      </div>

      {/* Explicit Uncertainty Banner */}
      <div className="p-4 rounded-2xl bg-amber-500/10 border border-amber-500/30 flex items-start gap-3">
        <ShieldAlert className="w-5 h-5 text-amber-400 flex-shrink-0 mt-0.5" />
        <div className="text-xs text-amber-200 leading-relaxed">
          <span className="font-bold">Mandatory Qualitative & Uncertainty Safeguard:</span> Visual body-composition
          assessments from 2D photographs are strictly qualitative and subject to lighting, camera lens focal length,
          hydration, and glycogen fluctuations (±4–6% variance). They never replace clinical DEXA or 7-site caliper
          assessments.
        </div>
      </div>

      {error && (
        <div className="p-4 rounded-xl bg-red-500/10 border border-red-500/20 text-red-400 text-sm flex items-center gap-3">
          <AlertCircle className="w-5 h-5 flex-shrink-0" />
          <span>{error}</span>
        </div>
      )}

      <div className="grid lg:grid-cols-2 gap-6">
        {/* Upload & Analyze Form */}
        <form onSubmit={handleAnalyze} className="bg-dark-800 border border-gray-800 rounded-2xl p-6 space-y-5">
          <h3 className="text-lg font-bold text-white border-b border-gray-800 pb-3 flex items-center gap-2">
            <Camera className="w-5 h-5 text-brand-400" />
            <span>Submit Progress Photograph for AI Analysis</span>
          </h3>

          <div className="grid sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold text-gray-400 uppercase mb-1.5">Pose / Angle</label>
              <select
                value={photoType}
                onChange={(e) => setPhotoType(e.target.value)}
                className="w-full px-3.5 py-2.5 bg-gray-900 border border-gray-800 rounded-xl text-white text-sm"
              >
                <option value="front">Front Relaxed / Double Biceps</option>
                <option value="side">Side Profile Posture</option>
                <option value="back">Back Lat Spread / Posterior</option>
              </select>
            </div>

            <div>
              <label className="block text-xs font-semibold text-gray-400 uppercase mb-1.5">
                Body Weight at Capture (kg)
              </label>
              <input
                type="number"
                step="0.1"
                value={weightAtCapture}
                onChange={(e) => setWeightAtCapture(Number(e.target.value))}
                className="w-full px-3.5 py-2.5 bg-gray-900 border border-gray-800 rounded-xl text-white text-sm"
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold text-gray-400 uppercase mb-1.5">
              Select Progress Image (JPEG/PNG)
            </label>
            <input
              type="file"
              accept="image/*"
              onChange={handleFileChange}
              className="w-full px-3.5 py-2.5 bg-gray-900 border border-gray-800 rounded-xl text-gray-300 text-xs"
            />
            <div className="text-[11px] text-gray-500 mt-1">Selected file reference: {filename}</div>
          </div>

          <button
            type="submit"
            disabled={analyzing}
            className="w-full py-3 bg-brand-600 hover:bg-brand-500 disabled:opacity-50 text-white font-semibold rounded-xl text-sm flex items-center justify-center gap-2"
          >
            <Sparkles className="w-4 h-4" />
            <span>{analyzing ? 'Running BodyAnalysisAgent...' : 'Run Qualitative Photo Analysis'}</span>
          </button>
        </form>

        {/* Latest Analysis Report */}
        <div className="bg-dark-800 border border-gray-800 rounded-2xl p-6 space-y-4">
          <h3 className="text-lg font-bold text-white border-b border-gray-800 pb-3">
            BodyAnalysisAgent Structured Report
          </h3>

          {latestAnalysis?.analysis ? (
            <div className="space-y-4 text-xs">
              <div className="flex items-center justify-between">
                <span className="px-2.5 py-1 rounded-md bg-brand-500/15 text-brand-400 font-semibold uppercase">
                  Pose: {latestAnalysis.photo_type}
                </span>
                <span className="text-gray-400">
                  Confidence: {latestAnalysis.analysis.confidence_level} •{' '}
                  {latestAnalysis.analysis.qualitative_body_composition_range}
                </span>
              </div>

              <div className="p-3.5 rounded-xl bg-gray-900 border border-gray-800 space-y-2">
                <div className="font-semibold text-white">Qualitative Muscular & Symmetry Observations</div>
                <ul className="list-disc list-inside text-gray-300 space-y-1">
                  {latestAnalysis.analysis.muscular_development_notes?.map((obs: string, i: number) => (
                    <li key={i}>{obs}</li>
                  ))}
                  {latestAnalysis.analysis.symmetry_notes?.map((obs: string, i: number) => (
                    <li key={`sym-${i}`}>{obs}</li>
                  ))}
                </ul>
              </div>

              {latestAnalysis.analysis.posture_observations && (
                <div className="p-3.5 rounded-xl bg-gray-900 border border-gray-800 space-y-1">
                  <div className="font-semibold text-white">Posture & Alignment Notes</div>
                  {latestAnalysis.analysis.posture_observations.map((n: string, i: number) => (
                    <p key={i} className="text-gray-300">
                      {n}
                    </p>
                  ))}
                </div>
              )}

              {latestAnalysis.analysis.weight_comparison_note && (
                <div className="text-emerald-400 font-medium">{latestAnalysis.analysis.weight_comparison_note}</div>
              )}

              <div className="p-3 rounded-xl bg-amber-500/10 border border-amber-500/20 text-amber-200 text-[11px]">
                {latestAnalysis.analysis.uncertainty_disclaimer}
              </div>
            </div>
          ) : (
            <p className="text-xs text-gray-400 py-8 text-center">
              Submit a progress photo on the left to generate a qualitative posture and physique assessment.
            </p>
          )}
        </div>
      </div>

      {/* Historical Photo Log */}
      {photos.length > 0 && (
        <div className="bg-dark-800 border border-gray-800 rounded-2xl p-6 space-y-4">
          <h3 className="font-bold text-white text-sm uppercase tracking-wider text-gray-400">
            Historical Progress Photo Records ({photos.length})
          </h3>
          <div className="grid sm:grid-cols-3 gap-4">
            {photos.map((p) => (
              <div
                key={p.id}
                onClick={() => setLatestAnalysis(p)}
                className="p-4 rounded-xl bg-gray-900 border border-gray-800 hover:border-brand-500 cursor-pointer space-y-1 text-xs"
              >
                <div className="flex justify-between font-semibold text-white capitalize">
                  <span>{p.photo_type} Pose</span>
                  <span className="text-brand-400">{p.weight_at_capture_kg} kg</span>
                </div>
                <div className="text-gray-500">{p.taken_at}</div>
                <div className="text-gray-400 truncate">
                  {p.analysis?.qualitative_body_composition_range || 'Qualitative Record'}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
