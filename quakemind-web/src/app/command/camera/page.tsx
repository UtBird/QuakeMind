"use client";

import React, { useState, useRef, useEffect } from "react";
import Sidebar from "@/components/layout/Sidebar";
import { Camera, Video, AlertCircle, CheckCircle2, Play, Square, Layers, Zap, RefreshCw, AlertTriangle, ShieldAlert, Upload, Image as ImageIcon } from "lucide-react";
import { analyzeCameraFrame, CameraAnalysisResponse } from "@/lib/api";
import { getCurrentCoords } from "@/lib/geolocation";

export default function CameraDetectionPage() {
  const videoRef = useRef<HTMLVideoElement | null>(null);
  const galleryInputRef = useRef<HTMLInputElement | null>(null);

  const [inputMode, setInputMode] = useState<"camera" | "upload">("camera");
  const [stream, setStream] = useState<MediaStream | null>(null);
  const [selectedModel, setSelectedModel] = useState<"catlak" | "bina" | "hybrid">("hybrid");

  const [capturedPhotoB64, setCapturedPhotoB64] = useState<string | null>(null);
  const [uploadedImageB64, setUploadedImageB64] = useState<string | null>(null);

  const [analyzing, setAnalyzing] = useState(false);
  const [result, setResult] = useState<CameraAnalysisResponse | null>(null);
  // J-168: API'ye ulasilamazsa sonuc UYDURULMAZ; hata yazilir.
  const [analizHatasi, setAnalizHatasi] = useState<string | null>(null);

  useEffect(() => {
    if (inputMode === "camera") {
      startCamera();
    } else {
      stopCamera();
    }
    return () => {
      stopCamera();
    };
  }, [inputMode]);

  useEffect(() => {
    if (inputMode === "camera" && stream && videoRef.current) {
      videoRef.current.srcObject = stream;
      videoRef.current.play().catch((err) => console.warn("Video play error:", err));
    }
  }, [stream, result, inputMode]);

  const [cameraError, setCameraError] = useState<string | null>(null);

  const startCamera = async () => {
    setCameraError(null);
    try {
      let mediaStream: MediaStream | null = null;
      try {
        mediaStream = await navigator.mediaDevices.getUserMedia({
          video: { facingMode: "environment", width: { ideal: 1280 }, height: { ideal: 720 } },
        });
      } catch (e1) {
        console.warn("Rear environment camera not found, falling back to standard video device:", e1);
        mediaStream = await navigator.mediaDevices.getUserMedia({
          video: true,
        });
      }

      setStream(mediaStream);
      if (videoRef.current && mediaStream) {
        videoRef.current.srcObject = mediaStream;
        videoRef.current.play().catch((pErr) => console.warn("Auto video play error:", pErr));
      }
    } catch (err) {
      console.warn("Kamera erişim hatası:", err);
      setCameraError("Kamera açılamadı veya cihazda aktif webcam bulunamadı. 'Galeriden Yükle' sekmesini kullanabilirsiniz.");
    }
  };

  const stopCamera = () => {
    if (stream) {
      stream.getTracks().forEach((track) => track.stop());
      setStream(null);
    }
  };

  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = () => {
      setUploadedImageB64(reader.result as string);
      setResult(null);
    };
    reader.readAsDataURL(file);
  };

  const captureFrameFromVideo = (): string | null => {
    if (!videoRef.current) return null;
    const canvas = document.createElement("canvas");
    canvas.width = videoRef.current.videoWidth || 640;
    canvas.height = videoRef.current.videoHeight || 480;
    const ctx = canvas.getContext("2d");
    if (!ctx) return null;
    ctx.drawImage(videoRef.current, 0, 0, canvas.width, canvas.height);
    const dataUrl = canvas.toDataURL("image/jpeg", 0.85);
    setCapturedPhotoB64(dataUrl);
    return dataUrl;
  };

  const handleRunAnalysis = async () => {
    setAnalyzing(true);
    setAnalizHatasi(null);
    let imagePayload: string | undefined = undefined;

    if (inputMode === "upload" && uploadedImageB64) {
      imagePayload = uploadedImageB64;
    } else if (inputMode === "camera") {
      imagePayload = captureFrameFromVideo() || capturedPhotoB64 || undefined;
    }

    try {
      const coords = await getCurrentCoords();
      const res = await analyzeCameraFrame(selectedModel, imagePayload, coords?.lat, coords?.lon);
      setResult(res);
    } catch (e) {
      // J-168: Eskiden burada sabit bir sonuc basiliyordu ("BINA AGIR HASARLI",
      // guven %96,2) -- model hic kosmadan gercek olcum gibi gorunuyordu
      // (CLAUDE.md kural 1). Artik sonuc yok, hata yazilir.
      console.warn("Kamera analizi yapilamadi:", e);
      setResult(null);
      setAnalizHatasi("Sunucuya ulaşılamadı; analiz YAPILMADI. Ekrandaki önceki sonuç silindi. Bağlantıyı kontrol edip yeniden deneyin.");
    } finally {
      setAnalyzing(false);
    }
  };

  const resetCapture = () => {
    setCapturedPhotoB64(null);
    setResult(null);
    setAnalizHatasi(null);
    if (inputMode === "camera") {
      startCamera();
    }
  };

  return (
    <div className="flex-1 flex w-full">
      <Sidebar />

      <main className="flex-1 p-6 space-y-6 overflow-y-auto max-h-[calc(100vh-65px)] bg-[#0b0f17]">
        {/* HEADER */}
        <div className="glass-panel p-6 rounded-3xl border border-emerald-500/30 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2 text-xs font-bold text-emerald-400 uppercase tracking-widest">
              <Camera className="w-4 h-4 text-emerald-500" />
              <span>OPENCV & ULTRALYTICS YOLO MODELİ</span>
            </div>
            <h1 className="text-2xl font-black text-white font-mono mt-1">EKİP CANLI KAMERA & FOTOĞRAF HASAR ANALİZİ</h1>
          </div>
        </div>

        {/* INPUT MODE TOGGLE & MODEL SELECTOR */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {/* INPUT MODE TOGGLE */}
          <div className="glass-panel p-4 rounded-2xl border border-slate-800 flex items-center justify-between gap-2 bg-slate-900/90">
            <span className="text-xs font-bold text-slate-300 flex items-center gap-2">
              <Layers className="w-4 h-4 text-emerald-400" /> KULLANIM YÖNTEMİ:
            </span>
            <div className="grid grid-cols-2 gap-2">
              <button
                onClick={() => { setInputMode("camera"); resetCapture(); }}
                className={`px-4 py-2 rounded-xl text-xs font-bold transition-all flex items-center gap-1.5 ${
                  inputMode === "camera"
                    ? "bg-emerald-600 text-white border border-emerald-400 shadow-md shadow-emerald-600/30"
                    : "glass-button text-slate-400"
                }`}
              >
                <Camera className="w-4 h-4" /> Canlı Kamera Çekimi
              </button>
              <button
                onClick={() => { setInputMode("upload"); resetCapture(); }}
                className={`px-4 py-2 rounded-xl text-xs font-bold transition-all flex items-center gap-1.5 ${
                  inputMode === "upload"
                    ? "bg-emerald-600 text-white border border-emerald-400 shadow-md shadow-emerald-600/30"
                    : "glass-button text-slate-400"
                }`}
              >
                <ImageIcon className="w-4 h-4" /> Galeriden Yükle
              </button>
            </div>
          </div>

          {/* MODEL SELECTOR BUTTONS */}
          <div className="glass-panel p-4 rounded-2xl border border-slate-800 flex items-center justify-between gap-2 bg-slate-900/90">
            <span className="text-xs font-bold text-slate-300 flex items-center gap-2">
              <Zap className="w-4 h-4 text-emerald-400" /> MODEL SEÇİMİ:
            </span>
            <div className="grid grid-cols-3 gap-1.5">
              <button
                onClick={() => setSelectedModel("catlak")}
                className={`px-3 py-2 rounded-xl text-xs font-bold transition-all border ${
                  selectedModel === "catlak"
                    ? "bg-emerald-600 text-white border-emerald-400"
                    : "glass-button text-slate-400 border-slate-800"
                }`}
              >
                🧱 Çatlak (`catlak.pt`)
              </button>
              <button
                onClick={() => setSelectedModel("bina")}
                className={`px-3 py-2 rounded-xl text-xs font-bold transition-all border ${
                  selectedModel === "bina"
                    ? "bg-red-600 text-white border-red-400"
                    : "glass-button text-slate-400 border-slate-800"
                }`}
              >
                🏢 Bina (`bina.pt`)
              </button>
              <button
                onClick={() => setSelectedModel("hybrid")}
                className={`px-3 py-2 rounded-xl text-xs font-bold transition-all border ${
                  selectedModel === "hybrid"
                    ? "bg-emerald-600 text-white border-emerald-400"
                    : "glass-button text-slate-400 border-slate-800"
                }`}
              >
                ⚡ Hibrit (İkili)
              </button>
            </div>
          </div>
        </div>

        {/* MAIN GRID */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          {/* LEFT COLUMN: CAMERA STREAM OR UPLOAD CANVAS (7 Cols) */}
          <div className="lg:col-span-7 glass-panel p-6 rounded-3xl border border-slate-800 space-y-4 flex flex-col h-[520px]">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <span className="text-xs font-bold text-slate-300 flex items-center gap-2">
                {inputMode === "camera" ? <Camera className="w-4 h-4 text-emerald-400" /> : <ImageIcon className="w-4 h-4 text-emerald-400" />}
                {inputMode === "camera" ? "CANLI WEBCAM & ANINDA FOTOĞRAF ÇEKİMİ" : "GALERİDEN FOTOĞRAF SEÇİMİ"}
              </span>
              <span className="text-[10px] bg-emerald-500/20 text-emerald-300 px-2.5 py-0.5 rounded-full font-bold">
                YOLO INTEGRATED
              </span>
            </div>

            <div className="flex-1 rounded-2xl bg-black border border-slate-800 relative overflow-hidden flex items-center justify-center">
              {/* ANNOTATED IMAGE FROM REAL YOLO INFERENCE */}
              {result?.annotatedImage ? (
                <img src={result.annotatedImage} alt="YOLO Detection Result" className="w-full h-full object-contain" />
              ) : inputMode === "upload" ? (
                uploadedImageB64 ? (
                  <img src={uploadedImageB64} alt="Uploaded Building" className="w-full h-full object-contain" />
                ) : (
                  <div 
                    onClick={() => galleryInputRef.current?.click()}
                    className="w-full h-full flex flex-col items-center justify-center p-6 text-center text-slate-400 space-y-3 cursor-pointer hover:bg-slate-900/60 transition-colors"
                  >
                    <Upload className="w-12 h-12 text-emerald-400 animate-bounce" />
                    <div className="space-y-1">
                      <p className="font-bold text-white text-sm">Galerinizden Fotoğraf Yüklemek İçin Tıklayın</p>
                      <p className="text-xs text-slate-500">Bilgisayar veya telefonunuzdaki JPG, PNG formatındaki fotoğraflar</p>
                    </div>
                  </div>
                )
              ) : cameraError ? (
                <div className="flex flex-col items-center justify-center p-6 text-center text-amber-300 space-y-3">
                  <AlertTriangle className="w-10 h-10 text-amber-400" />
                  <p className="text-xs font-bold">{cameraError}</p>
                  <button onClick={() => setInputMode("upload")} className="px-4 py-2 bg-emerald-600 text-white rounded-xl font-bold text-xs hover:bg-emerald-500 transition-all">
                    📷 Galeriden Fotoğraf Yükle
                  </button>
                </div>
              ) : (
                <video ref={videoRef} autoPlay playsInline muted className="w-full h-full object-cover" />
              )}

              {/* HIDDEN GALLERY FILE INPUT */}
              <input type="file" ref={galleryInputRef} accept="image/*" onChange={handleFileUpload} className="hidden" />
            </div>

            {/* ACTION BUTTONS */}
            <div className="flex items-center gap-3">
              {inputMode === "camera" ? (
                <button
                  onClick={handleRunAnalysis}
                  disabled={analyzing}
                  className="flex-1 py-4 rounded-2xl bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500 text-white font-black text-sm shadow-xl shadow-emerald-600/30 transition-all flex items-center justify-center gap-2 disabled:opacity-50"
                >
                  {analyzing ? (
                    <>
                      <RefreshCw className="w-5 h-5 animate-spin" /> `catlak.pt` & `bina.pt` YOLO Çıkarımı Yapılıyor...
                    </>
                  ) : (
                    <>
                      <Camera className="w-5 h-5" /> 📸 ANINDA FOTOĞRAF ÇEK VE ANALİZ ET
                    </>
                  )}
                </button>
              ) : (
                <div className="flex items-center gap-2 w-full">
                  <button
                    onClick={() => galleryInputRef.current?.click()}
                    className="px-5 py-4 rounded-2xl glass-button text-xs font-bold text-slate-300 hover:bg-slate-800 flex items-center gap-2"
                  >
                    <ImageIcon className="w-4 h-4" /> Galeriden Seç
                  </button>
                  <button
                    onClick={handleRunAnalysis}
                    disabled={analyzing || !uploadedImageB64}
                    className="flex-1 py-4 rounded-2xl bg-emerald-600 hover:bg-emerald-500 text-white font-bold text-sm shadow-xl shadow-emerald-600/30 transition-all flex items-center justify-center gap-2 disabled:opacity-50"
                  >
                    {analyzing ? (
                      <>
                        <RefreshCw className="w-5 h-5 animate-spin" /> Analiz Ediliyor...
                      </>
                    ) : (
                      <>
                        <Zap className="w-5 h-5" /> FOTOĞRAFI YOLO İLE ANALİZ ET
                      </>
                    )}
                  </button>
                </div>
              )}

              {result && (
                <button
                  onClick={resetCapture}
                  className="px-4 py-4 rounded-2xl glass-button text-slate-300 hover:text-white text-xs font-bold"
                  title="Yeni Çekim Yap"
                >
                  <RefreshCw className="w-5 h-5" />
                </button>
              )}
            </div>
          </div>

          {/* RIGHT COLUMN: REAL YOLO RESULTS DISPLAY CARD (5 Cols) */}
          <div className="lg:col-span-5 space-y-6">
            <div className="glass-panel p-6 rounded-3xl border border-slate-800 space-y-6 h-[520px] flex flex-col justify-between bg-slate-900/90">
              <div className="space-y-4">
                <div className="flex items-center justify-between border-b border-slate-800 pb-3">
                  <span className="text-xs font-bold text-slate-300 flex items-center gap-2">
                    <ShieldAlert className="w-4 h-4 text-emerald-400" /> MODEL TESPİT ÇIKTILARI & RAPOR
                  </span>
                  <span className="text-[10px] text-slate-400 font-mono font-bold">REAL YOLO INFERENCE</span>
                </div>

                {result ? (
                  <div className="space-y-4">
                    {/* STATUS BANNER */}
                    <div className={`p-4 rounded-2xl border flex items-start gap-3.5 ${
                      result.status === "CRITICAL_EVACUATE"
                        ? "bg-red-500/10 border-red-500/40 text-red-300"
                        : "bg-emerald-500/10 border-emerald-500/40 text-emerald-300"
                    }`}>
                      {result.status === "CRITICAL_EVACUATE" ? (
                        <AlertTriangle className="w-8 h-8 text-red-500 flex-shrink-0 animate-bounce" />
                      ) : (
                        <CheckCircle2 className="w-8 h-8 text-emerald-400 flex-shrink-0" />
                      )}
                      <div className="space-y-1">
                        <h3 className="font-bold text-white text-sm">{result.advice}</h3>
                        <span className="text-[10px] text-slate-400 block font-mono">
                          Zaman: {new Date(result.timestamp).toLocaleTimeString("tr-TR")}
                        </span>
                      </div>
                    </div>

                    {/* ACTIVE MODELS LIST */}
                    <div className="text-[11px] text-slate-400 space-y-1 font-mono">
                      <span className="font-bold text-slate-300">Aktif Çıkarım Yapan Modeller:</span>
                      <div className="flex flex-wrap gap-1.5 pt-1">
                        {result.activeModels.map((m, idx) => (
                          <span key={idx} className="bg-slate-800 text-emerald-300 px-2 py-0.5 rounded border border-slate-700 font-mono text-[10px]">
                            {m}
                          </span>
                        ))}
                      </div>
                    </div>

                    {/* REAL YOLO DETECTIONS LIST */}
                    <div className="space-y-2 max-h-[180px] overflow-y-auto">
                      <span className="text-[10px] font-bold text-slate-400 uppercase tracking-widest block">
                        Tespit Edilen YOLO Kutuları ({result.detections.length}):
                      </span>
                      {result.detections.map((d, i) => (
                        <div key={i} className="p-3 rounded-xl bg-slate-950 border border-slate-800 flex items-center justify-between">
                          <div>
                            <div className="font-bold text-xs text-slate-200">{d.label}</div>
                            <div className="text-[10px] text-slate-500 font-mono">Model: {d.model} | Box: [{d.box.join(", ")}]</div>
                          </div>
                          <div className="text-right">
                            <span className={`text-xs font-bold px-2.5 py-1 rounded-full ${
                              d.severity === "CRITICAL" ? "bg-red-500/20 text-red-400 border border-red-500/30" : "bg-emerald-500/20 text-emerald-400 border border-emerald-500/30"
                            }`}>
                              %{d.confidence}
                            </span>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                ) : analizHatasi ? (
                  <div role="alert" className="p-4 rounded-2xl border border-slate-700 bg-slate-950 text-slate-200 text-sm space-y-2">
                    <p className="font-bold">Analiz yapılamadı</p>
                    <p>{analizHatasi}</p>
                  </div>
                ) : (
                  <div className="p-8 text-center text-slate-500 space-y-3 font-mono text-xs my-auto">
                    <Camera className="w-12 h-12 text-slate-700 mx-auto animate-pulse" />
                    <p>Canlı kameranız aktif! Duvarı/binayı hizalayıp &quot;📸 ANINDA FOTOĞRAF ÇEK VE ANALİZ ET&quot; butonuna basınız.</p>
                  </div>
                )}
              </div>

              {/* FOOTER INFO */}
              <div className="p-3.5 rounded-2xl bg-slate-950 border border-slate-800 text-[11px] text-slate-400 space-y-1">
                <span className="font-bold text-slate-300 block">ℹ️ PyTorch YOLO Bilgisi:</span>
                <p>`catlak.pt` (`crack`) ve `bina.pt` (`0_NoDamage`, `1_ModerateDamage`, `2_VeryHeavyDamage`) modelleri ile anlık kare dondurularak çıkarım yapılır.</p>
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
