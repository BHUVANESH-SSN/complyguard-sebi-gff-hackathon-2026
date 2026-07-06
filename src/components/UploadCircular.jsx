import { useState, useRef } from "react";
import { CIRCULAR } from "../data/mockData";

const PROCESSING_STEPS = [
  "Parsing PDF text...",
  "Chunking + generating embeddings...",
  "Retrieving relevant clauses...",
  "Extracting structured obligations...",
];

export default function UploadCircular({ onComplete }) {
  const [fileName, setFileName] = useState(null);
  const [dragOver, setDragOver] = useState(false);
  const [processing, setProcessing] = useState(false);
  const [stepIndex, setStepIndex] = useState(0);
  const [showSampleNotice, setShowSampleNotice] = useState(false);
  const timeouts = useRef([]);

  function startProcessing(name) {
    setShowSampleNotice(false);
    setFileName(name);
    setProcessing(true);
    setStepIndex(0);
    PROCESSING_STEPS.forEach((_, i) => {
      const t = setTimeout(() => setStepIndex(i), (i + 1) * 550);
      timeouts.current.push(t);
    });
    const done = setTimeout(() => onComplete(), PROCESSING_STEPS.length * 550 + 450);
    timeouts.current.push(done);
  }

  function useSample() {
    startProcessing(`${CIRCULAR.name}.pdf`);
  }

  function handleDrop(e) {
    e.preventDefault();
    setDragOver(false);
    if (e.dataTransfer.files?.[0]) {
      setShowSampleNotice(true);
    }
  }

  function handlePick(e) {
    if (e.target.files?.[0]) {
      setShowSampleNotice(true);
    }
    e.target.value = "";
  }

  return (
    <div className="flex-1">
      <h2 className="text-2xl font-bold tracking-tight text-neutral-900">
        Upload a circular
      </h2>
      <p className="mt-2 text-sm text-neutral-500">
        This prototype is wired up end-to-end for one document only.
      </p>

      {!processing && (
        <>
          <div className="mt-8 rounded-2xl border border-violet-200 bg-violet-50/40 p-8 text-center">
            <p className="font-mono text-xs font-medium tracking-wide text-violet-700">
              SAMPLE CIRCULAR
            </p>
            <p className="mt-1.5 text-lg font-semibold text-neutral-900">
              {CIRCULAR.name}
            </p>
            <p className="mt-1 text-sm text-neutral-500">
              {CIRCULAR.pages} pages · {CIRCULAR.intermediary}
            </p>
            <button
              onClick={useSample}
              className="mt-6 rounded-full bg-emerald-300 px-8 py-3.5 text-base font-semibold text-emerald-950 transition-colors hover:bg-emerald-400"
            >
              Run the pipeline on this circular →
            </button>
          </div>

          <div
            onDragOver={(e) => {
              e.preventDefault();
              setDragOver(true);
            }}
            onDragLeave={() => setDragOver(false)}
            onDrop={handleDrop}
            className={`mt-4 flex flex-col items-center justify-center rounded-2xl border-2 border-dashed px-6 py-10 text-center transition-colors ${
              dragOver ? "border-violet-400 bg-violet-50/40" : "border-neutral-200"
            }`}
          >
            <p className="text-sm text-neutral-400">
              Or drag and drop your own circular PDF, or{" "}
              <label className="cursor-pointer text-violet-700 underline underline-offset-2 hover:text-violet-900">
                choose a file
                <input type="file" accept="application/pdf" className="hidden" onChange={handlePick} />
              </label>
            </p>

            {showSampleNotice && (
              <p className="mt-4 max-w-sm rounded-xl bg-amber-50 px-4 py-3 text-sm text-amber-800">
                This prototype only has the sample circular wired up — real
                PDF ingestion isn't connected yet. Use the sample above to see
                the pipeline run.
              </p>
            )}
          </div>
        </>
      )}

      {processing && (
        <div className="mt-8 rounded-2xl border border-neutral-200 p-8">
          <p className="font-mono text-sm font-medium text-neutral-900">{fileName}</p>
          <div className="mt-6 space-y-3">
            {PROCESSING_STEPS.map((label, i) => {
              const active = i === stepIndex;
              return (
                <div key={label} className="flex items-center gap-3">
                  <div
                    className={`h-2 w-2 flex-shrink-0 rounded-full ${
                      i <= stepIndex ? "bg-violet-600" : "bg-neutral-200"
                    } ${active ? "animate-pulse" : ""}`}
                  />
                  <p
                    className={`font-mono text-sm ${
                      i <= stepIndex ? "text-neutral-900" : "text-neutral-300"
                    }`}
                  >
                    {label}
                  </p>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}
