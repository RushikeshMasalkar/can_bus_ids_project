import { ConsoleLayout } from '../layout/ConsoleLayout';

export function PipelinePage() {
  return (
    <ConsoleLayout activeNav="pipeline">
      <main className="min-h-screen p-8">
        <header className="mb-12 max-w-4xl">
          <h1 className="mb-2 font-headline text-4xl font-bold tracking-tight text-primary">Model &amp; Pipeline Architecture</h1>
          <p className="text-lg text-on-surface-variant">Detailed forensic visualization of the IDS Sentinel inference flow and artifact lineage.</p>
        </header>

        <section className="mb-16">
          <div className="flex flex-col gap-6">
            <div className="mb-2 flex items-center justify-between px-4">
              <h3 className="font-headline text-xl font-bold">Inference Pipeline Flow</h3>
              <span className="rounded-full bg-tertiary-container px-3 py-1 font-label text-xs text-tertiary-fixed-dim">STATUS: ACTIVE</span>
            </div>

            <div className="grid grid-cols-1 gap-4 md:grid-cols-5">
              <div className="group relative flex flex-col items-center overflow-hidden rounded-xl bg-surface-container-low p-6 text-center">
                <div className="absolute left-0 top-0 h-full w-1 bg-secondary" />
                <span className="material-symbols-outlined mb-3 text-3xl text-secondary">settings_input_component</span>
                <h4 className="mb-1 font-headline text-sm font-bold">Data Preprocessing</h4>
                <p className="text-xs text-on-surface-variant">CAN frame normalization</p>
              </div>

              <div className="relative flex flex-col items-center overflow-hidden rounded-xl bg-surface-container-low p-6 text-center">
                <div className="absolute left-0 top-0 h-full w-1 bg-secondary" />
                <span className="material-symbols-outlined mb-3 text-3xl text-secondary">view_column</span>
                <h4 className="mb-1 font-headline text-sm font-bold">Tokenization</h4>
                <p className="text-xs text-on-surface-variant">
                  Window: <span className="font-label">64</span> sequence
                </p>
              </div>

              <div className="relative flex flex-col items-center rounded-xl bg-primary-container p-6 text-center text-on-primary-container">
                <div className="absolute -right-2 -top-2 rounded-full bg-secondary-container px-2 py-0.5 text-[10px] font-bold text-on-secondary-container">STAGE 1</div>
                <span className="material-symbols-outlined mb-3 text-3xl text-secondary-container">psychology</span>
                <h4 className="mb-1 font-headline text-sm font-bold">Scoring Engine</h4>
                <p className="text-xs opacity-80">Anomaly Probability</p>
              </div>

              <div className="relative flex flex-col items-center rounded-xl bg-surface-container-low p-6 text-center">
                <span className="material-symbols-outlined mb-3 text-3xl text-on-surface-variant">door_front</span>
                <h4 className="mb-1 font-headline text-sm font-bold">Threshold Gate</h4>
                <p className="text-xs text-on-surface-variant">Conditional logic</p>
              </div>

              <div className="relative flex flex-col items-center rounded-xl bg-primary p-6 text-center text-on-primary">
                <div className="absolute -right-2 -top-2 rounded-full bg-secondary-container px-2 py-0.5 text-[10px] font-bold text-on-secondary-container">STAGE 2</div>
                <span className="material-symbols-outlined mb-3 text-3xl text-secondary-fixed-dim">hub</span>
                <h4 className="mb-1 font-headline text-sm font-bold text-white">Classifier</h4>
                <p className="text-xs opacity-70">Multiclass Identification</p>
              </div>
            </div>
          </div>
        </section>

        <section className="mb-16 grid grid-cols-1 gap-8 lg:grid-cols-2">
          <div className="group relative flex flex-col gap-6 overflow-hidden rounded-xl bg-surface-container-lowest p-8">
            <div className="flex items-start justify-between">
              <div>
                <div className="mb-2 text-xs uppercase tracking-widest text-secondary">Core Scoring Unit</div>
                <h3 className="font-headline text-2xl font-bold text-primary">DistilBERT Anomaly Scorer</h3>
              </div>
              <span className="material-symbols-outlined text-4xl text-primary/10 transition-colors group-hover:text-primary/20">memory</span>
            </div>
            <div className="space-y-4">
              <p className="leading-relaxed text-on-surface-variant">
                A specialized transformer-based architecture optimized for sequential automotive bus protocols. It monitors the statistical deviation of message arrivals.
              </p>
              <div className="grid grid-cols-2 gap-4">
                <div className="rounded-lg bg-surface-container-low p-3">
                  <div className="mb-1 text-[10px] text-on-surface-variant">ARCH</div>
                  <div className="text-sm font-bold">Transformer-based</div>
                </div>
                <div className="rounded-lg bg-surface-container-low p-3">
                  <div className="mb-1 text-[10px] text-on-surface-variant">TRAINING</div>
                  <div className="text-sm font-bold">Masked Language Modeling</div>
                </div>
                <div className="rounded-lg bg-surface-container-low p-3">
                  <div className="mb-1 text-[10px] text-on-surface-variant">INPUT</div>
                  <div className="text-sm font-bold">64-ID sequence window</div>
                </div>
                <div className="rounded-lg bg-surface-container-low p-3">
                  <div className="mb-1 text-[10px] text-on-surface-variant">LATENCY</div>
                  <div className="text-sm font-bold">&lt; 12ms / inference</div>
                </div>
              </div>
            </div>
          </div>

          <div className="group relative flex flex-col gap-6 overflow-hidden rounded-xl bg-surface-container-lowest p-8">
            <div className="flex items-start justify-between">
              <div>
                <div className="mb-2 text-xs uppercase tracking-widest text-secondary">Identification Unit</div>
                <h3 className="font-headline text-2xl font-bold text-primary">Random Forest Classifier</h3>
              </div>
              <span className="material-symbols-outlined text-4xl text-primary/10 transition-colors group-hover:text-primary/20">account_tree</span>
            </div>
            <div className="space-y-4">
              <p className="leading-relaxed text-on-surface-variant">
                The secondary stage triggered by high anomaly scores. It provides high-granularity classification of the specific attack vector detected.
              </p>
              <div className="grid grid-cols-2 gap-4">
                <div className="rounded-lg bg-surface-container-low p-3">
                  <div className="mb-1 text-[10px] text-on-surface-variant">FEATURES</div>
                  <div className="text-sm font-bold">TF-IDF + Numeric Seq</div>
                </div>
                <div className="rounded-lg bg-surface-container-low p-3">
                  <div className="mb-1 text-[10px] text-on-surface-variant">OUTPUT</div>
                  <div className="text-sm font-bold">Multiclass (4 types)</div>
                </div>
                <div className="rounded-lg bg-surface-container-low p-3">
                  <div className="mb-1 text-[10px] text-on-surface-variant">ESTIMATORS</div>
                  <div className="text-sm font-bold">128 Decision Trees</div>
                </div>
                <div className="rounded-lg bg-surface-container-low p-3">
                  <div className="mb-1 text-[10px] text-on-surface-variant">ACCURACY</div>
                  <div className="text-sm font-bold">99.2% F1-Score</div>
                </div>
              </div>
            </div>
          </div>
        </section>

        <section className="mb-16 rounded-2xl border border-outline-variant/10 bg-surface-container-low p-10">
          <h3 className="mb-8 flex items-center gap-3 font-headline text-2xl font-bold">
            <span className="material-symbols-outlined text-secondary">alt_route</span>
            Decision Logic
          </h3>

          <div className="flex flex-col items-center justify-between gap-8 md:flex-row">
            <div className="flex-1 space-y-4">
              <div className="flex items-center gap-4">
                <div className="flex h-12 w-12 items-center justify-center rounded-full bg-primary font-label text-white">S1</div>
                <div className="flex-1 rounded-xl bg-surface-container-lowest p-4">
                  <span className="text-xs opacity-60">DISTILBERT SCORE (ρ)</span>
                  <div className="font-bold">ρ = 0.88 (Potential Intrusion)</div>
                </div>
              </div>
              <div className="flex h-12 justify-center">
                <div className="w-px border-l border-dashed border-outline bg-outline-variant" />
              </div>
              <div className="flex items-center gap-4">
                <div className="flex h-12 w-12 items-center justify-center rounded-full border-2 border-secondary text-secondary">
                  <span className="material-symbols-outlined">priority_high</span>
                </div>
                <div className="flex-1 rounded-xl bg-secondary-container p-4">
                  <span className="text-xs text-on-secondary-container/60">THRESHOLD CHECK (τ)</span>
                  <div className="font-bold text-on-secondary-container">If ρ &gt; 0.75 → Trigger Stage 2</div>
                </div>
              </div>
            </div>

            <div className="hidden md:block">
              <span className="material-symbols-outlined text-5xl text-outline-variant">trending_flat</span>
            </div>

            <div className="flex-1 space-y-4">
              <div className="rounded-2xl border-l-4 border-error bg-surface-container-lowest p-6 shadow-sm">
                <h4 className="mb-4 font-headline text-sm font-bold">Stage 2: Threat Analysis</h4>
                <div className="space-y-2">
                  <div className="flex items-center justify-between text-xs">
                    <span>DoS Attack</span>
                    <span className="font-label font-bold text-error">88%</span>
                  </div>
                  <div className="h-1.5 w-full overflow-hidden rounded-full bg-surface-container-high">
                    <div className="h-full bg-error" style={{ width: '88%' }} />
                  </div>
                  <div className="flex items-center justify-between text-xs opacity-50">
                    <span>Replay Attack</span>
                    <span className="font-label">7%</span>
                  </div>
                  <div className="flex items-center justify-between text-xs opacity-50">
                    <span>Fuzzing</span>
                    <span className="font-label">5%</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </section>

        <section className="mb-16">
          <h3 className="mb-8 font-headline text-2xl font-bold">Artifact Registry</h3>
          <div className="grid grid-cols-2 gap-4 md:grid-cols-3 lg:grid-cols-5">
            {[
              ['book_4', 'Vocabulary', 'HEX_CORPUS_V3.JSON'],
              ['layers', 'Sequence Tensors', 'TENSOR_BUFF_64.NPZ'],
              ['database', 'Model Weights', 'IDS_BERT_CORE.PT'],
              ['tune', 'Threshold Config', 'CONFIG_PRODUCTION.YAML'],
              ['data_object', 'Vectorizer', 'TFIDF_CAN_MAP.PKL'],
            ].map(([icon, title, file]) => (
              <div key={title} className="group flex flex-col gap-3 rounded-xl bg-surface-container-lowest p-5 transition-colors hover:bg-surface-container-high">
                <span className="material-symbols-outlined text-secondary">{icon}</span>
                <div>
                  <h5 className="text-sm font-bold">{title}</h5>
                  <p className="font-label text-[10px] text-on-surface-variant">{file}</p>
                </div>
              </div>
            ))}
          </div>
        </section>

        <section className="mb-16">
          <h3 className="mb-10 font-headline text-2xl font-bold">Training Lifecycle</h3>
          <div className="relative">
            <div className="absolute left-0 top-1/2 hidden h-0.5 w-full -translate-y-1/2 bg-outline-variant md:block" />
            <div className="relative z-10 grid grid-cols-1 gap-8 md:grid-cols-4">
              {[
                ['1', 'Data Collection', 'Logging RAW CAN Bus telemetry'],
                ['2', 'Offline Training', 'MLM pre-training + classification tuning'],
                ['3', 'Edge Quantization', 'Optimization for vehicle ECUs'],
                ['check', 'Deployment', 'OTA rollout to Sentinel fleet'],
              ].map(([step, title, desc], index) => (
                <div key={title} className="flex flex-col items-center">
                  {index === 3 ? (
                    <div className="mb-4 flex h-8 w-8 items-center justify-center rounded-full bg-secondary-container text-on-secondary-container">
                      <span className="material-symbols-outlined text-lg">{step}</span>
                    </div>
                  ) : (
                    <div className="mb-4 flex h-8 w-8 items-center justify-center rounded-full bg-primary font-bold text-white">{step}</div>
                  )}
                  <div className={`w-full rounded-xl p-5 text-center ${index === 3 ? 'border border-secondary-container bg-surface-container-lowest' : 'bg-surface-container-lowest'}`}>
                    <h6 className="mb-1 text-sm font-bold">{title}</h6>
                    <p className="text-xs text-on-surface-variant">{desc}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </section>
      </main>
    </ConsoleLayout>
  );
}
