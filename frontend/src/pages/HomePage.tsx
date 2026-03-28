import { Link } from 'react-router-dom';

export function HomePage() {
  return (
    <div className="bg-surface text-on-surface selection:bg-secondary-container selection:text-on-secondary-container">
      <nav className="fixed top-0 z-50 w-full bg-surface-container-low/80 backdrop-blur-md">
        <div className="mx-auto flex h-16 w-full max-w-[1440px] items-center justify-between px-6">
          <div className="flex items-center gap-2">
            <span className="font-headline text-xl font-bold tracking-tighter text-primary">IDS.Sentinel</span>
          </div>
          <div className="hidden items-center gap-8 md:flex">
            <Link className="border-b-2 border-primary pb-1 text-sm font-bold text-primary" to="/">
              Home
            </Link>
            <Link className="text-sm text-on-surface-variant transition-colors hover:text-primary" to="/security">
              About
            </Link>
            <Link className="text-sm text-on-surface-variant transition-colors hover:text-primary" to="/reports">
              Reports
            </Link>
          </div>
          <div className="flex items-center gap-4">
            <button className="rounded-full p-2 transition-all hover:bg-surface-container-highest active:scale-95" type="button">
              <span className="material-symbols-outlined text-on-surface-variant">search</span>
            </button>
            <Link
              className="hidden items-center gap-2 rounded-xl bg-primary px-4 py-2 text-sm font-bold text-on-primary transition-all hover:-translate-y-[1px] active:scale-95 md:flex"
              to="/dashboard"
            >
              Live Dashboard
            </Link>
            <button className="p-2 md:hidden" type="button" aria-label="Open menu">
              <span className="material-symbols-outlined">menu</span>
            </button>
          </div>
        </div>
      </nav>

      <main className="pt-16">
        <section className="relative flex min-h-[870px] flex-col items-center justify-center overflow-hidden px-6">
          <div className="hex-grid absolute inset-0 z-0" />
          <div className="absolute left-1/2 top-1/2 z-0 h-[600px] w-[600px] -translate-x-1/2 -translate-y-1/2 rounded-full bg-secondary/5 blur-[120px]" />
          <div className="relative z-10 max-w-4xl text-center">
            <div className="mb-8 inline-flex items-center gap-2 rounded-full border border-secondary/10 bg-secondary-container/20 px-3 py-1 text-secondary">
              <span className="h-2 w-2 animate-pulse rounded-full bg-secondary" />
              <span className="font-mono text-xs font-bold uppercase tracking-widest">System Status: Active</span>
            </div>
            <h1 className="mb-6 font-headline text-5xl font-bold leading-[1.1] tracking-tight text-primary md:text-7xl">Precision Sentinel</h1>
            <p className="mx-auto mb-10 max-w-2xl text-xl leading-relaxed text-on-surface-variant md:text-2xl">
              Enterprise-Grade Anomaly Detection for Automotive CAN Networks. High-fidelity forensic analysis at the speed of wire.
            </p>
            <div className="flex flex-col items-center justify-center gap-4 md:flex-row">
              <Link
                className="w-full rounded-xl bg-primary px-8 py-4 font-bold text-white shadow-lg shadow-primary/10 transition-all hover:-translate-y-0.5 hover:shadow-primary/20 md:w-auto"
                to="/dashboard"
              >
                View Live Dashboard
              </Link>
              <Link
                className="w-full rounded-xl border-2 border-outline/20 bg-transparent px-8 py-4 font-bold text-primary transition-all hover:bg-surface-container-low md:w-auto"
                to="/integration"
              >
                Try Sequence Analyzer
              </Link>
            </div>
          </div>

          <div className="group relative mt-20 w-full max-w-5xl">
            <div className="overflow-hidden rounded-2xl border border-outline-variant/30 bg-surface-container-lowest shadow-2xl">
              <div className="flex items-center gap-2 bg-surface-container-low px-4 py-3">
                <div className="flex gap-1.5">
                  <div className="h-3 w-3 rounded-full bg-error/20" />
                  <div className="h-3 w-3 rounded-full bg-surface-tint/20" />
                  <div className="h-3 w-3 rounded-full bg-tertiary-container/20" />
                </div>
                <div className="mx-auto font-mono text-[10px] uppercase tracking-widest text-outline">Global Network Integrity Stream</div>
              </div>
              <img
                alt="Dashboard Preview"
                className="h-[400px] w-full object-cover grayscale-[0.5] contrast-[1.1]"
                src="https://lh3.googleusercontent.com/aida-public/AB6AXuDktJ9aS2PRXkXyTTeoe4S-21r0Gfp4Txz-vj8ao5GTtqRAcVdJlet_ATho9eMDV_vfkQd5cvU8KxZyBRTRdSaaXjODjyVQsexF4nxe6KnovuYmto8sJrekIh8OZ07J4nAh_-KCAnUvHgdIjbQGxGIVJqmsDRiZqDiEqY8u7-UXGozin5M0b-_jSsQcgK86uUkUODi7DuUYNDbp1la5Ir7R2YRmg_KKegDzppqRC-1Fn63vNTV3OEv4VinCvc2585X7FuZy6SEdgNg"
              />
            </div>
          </div>
        </section>

        <section className="border-y border-outline-variant/10 bg-surface-container-low py-12">
          <div className="mx-auto max-w-[1440px] px-6">
            <div className="grid grid-cols-1 items-center gap-12 md:grid-cols-2">
              <div className="flex flex-wrap items-center justify-center gap-8 md:justify-start">
                <div className="text-center md:text-left">
                  <div className="font-headline text-3xl font-bold text-primary">97.12%</div>
                  <div className="font-mono text-[10px] uppercase tracking-widest text-outline">Accuracy</div>
                </div>
                <div className="text-center md:text-left">
                  <div className="font-headline text-3xl font-bold text-primary">97.53%</div>
                  <div className="font-mono text-[10px] uppercase tracking-widest text-outline">Precision</div>
                </div>
                <div className="text-center md:text-left">
                  <div className="font-headline text-3xl font-bold text-primary">95.06%</div>
                  <div className="font-mono text-[10px] uppercase tracking-widest text-outline">F1 Score</div>
                </div>
              </div>
              <div className="flex flex-wrap justify-center gap-6 opacity-60 md:justify-end">
                <span className="font-headline font-bold text-on-surface-variant">PyTorch</span>
                <span className="font-headline font-bold text-on-surface-variant">Transformers</span>
                <span className="font-headline font-bold text-on-surface-variant">scikit-learn</span>
                <span className="font-headline font-bold text-on-surface-variant">FastAPI</span>
                <span className="font-headline font-bold text-on-surface-variant">React</span>
              </div>
            </div>
          </div>
        </section>

        <section className="mx-auto max-w-[1440px] overflow-hidden px-6 py-24">
          <div className="grid grid-cols-1 items-center gap-16 lg:grid-cols-2">
            <div className="relative">
              <div className="absolute -left-12 -top-12 h-64 w-64 rounded-full bg-error/5 blur-3xl" />
              <h2 className="relative z-10 mb-8 font-headline text-4xl font-bold text-primary">Unencrypted &amp; Vulnerable</h2>
              <p className="mb-6 text-lg leading-relaxed text-on-surface-variant">
                The Controller Area Network (CAN) is the backbone of modern vehicles, yet it remains fundamentally insecure. Developed in an era before connectivity, it lacks standard authentication or encryption.
              </p>
              <p className="text-lg leading-relaxed text-on-surface-variant">
                Any compromised ECU can broadcast malicious frames, leading to total control over steering, braking, and drivetrain. Traditional firewalls fail to understand the semantic intent of automotive messaging.
              </p>
            </div>
            <div className="relative rounded-2xl border border-outline-variant/20 bg-surface-container-low p-8">
              <div className="mb-4 flex items-center gap-2 font-mono text-xs text-error">
                <span className="material-symbols-outlined text-sm" style={{ fontVariationSettings: "'FILL' 1" }}>
                  warning
                </span>
                ALERT: UNAUTHORIZED FRAME INJECTION
              </div>
              <div className="space-y-2 font-mono text-[13px]">
                <div className="flex justify-between rounded bg-error-container/20 px-2 py-1 text-error">
                  <span>ID: 0x2B0</span>
                  <span>DATA: 01 55 22 00 00 00 00 00</span>
                  <span>[FUZZY ATTACK]</span>
                </div>
                <div className="flex justify-between px-2 py-1 text-outline-variant">
                  <span>ID: 0x18F</span>
                  <span>DATA: 00 00 00 4F 21 00 00 00</span>
                  <span>[NOMINAL]</span>
                </div>
                <div className="flex justify-between px-2 py-1 text-outline-variant">
                  <span>ID: 0x316</span>
                  <span>DATA: 05 21 00 00 00 00 00 00</span>
                  <span>[NOMINAL]</span>
                </div>
                <div className="flex justify-between rounded bg-error-container/20 px-2 py-1 text-error">
                  <span>ID: 0x2B0</span>
                  <span>DATA: FF FF FF FF FF FF FF FF</span>
                  <span>[DoS ATTACK]</span>
                </div>
              </div>
            </div>
          </div>
        </section>

        <section className="relative overflow-hidden bg-primary py-24 text-white">
          <div className="hex-grid absolute inset-0 opacity-10" />
          <div className="relative z-10 mx-auto max-w-[1440px] px-6">
            <div className="mb-20 max-w-3xl">
              <h2 className="mb-8 font-headline text-4xl font-bold">Intelligence at the Edge</h2>
              <p className="text-lg leading-relaxed text-on-primary-container">
                IDS.Sentinel leverages a dual-stage machine learning architecture. Our system utilizes a lightweight DistilBERT encoder to capture sequential temporal dependencies followed by a high-velocity Random Forest classifier for sub-millisecond threat categorization.
              </p>
            </div>

            <div className="relative grid grid-cols-1 items-center gap-4 md:grid-cols-4 md:gap-8">
              <div className="relative rounded-xl border border-white/10 bg-primary-container p-6 text-center">
                <div className="mb-2 font-mono text-[10px] uppercase tracking-widest text-on-primary-container">Input Layer</div>
                <div className="font-headline text-lg font-bold">Raw CAN Bus</div>
                <div className="mt-4 flex justify-center gap-1">
                  <div className="h-4 w-1 bg-secondary" />
                  <div className="h-6 w-1 bg-secondary" />
                  <div className="h-3 w-1 bg-secondary" />
                </div>
              </div>
              <div className="relative rounded-xl border border-white/10 bg-primary-container p-6 text-center">
                <div className="mb-2 font-mono text-[10px] uppercase tracking-widest text-on-primary-container">Stage 1: Encoder</div>
                <div className="font-headline text-lg font-bold">DistilBERT</div>
                <div className="mt-4 text-[10px] text-on-primary-container">Contextual Embedding</div>
              </div>
              <div className="relative rounded-xl border border-white/10 bg-primary-container p-6 text-center">
                <div className="mb-2 font-mono text-[10px] uppercase tracking-widest text-on-primary-container">Stage 2: Classifier</div>
                <div className="font-headline text-lg font-bold">Random Forest</div>
                <div className="mt-4 text-[10px] text-on-primary-container">Categorical Decision</div>
              </div>
              <div className="relative rounded-xl border border-white/10 bg-secondary p-6 text-center">
                <div className="mb-2 font-mono text-[10px] uppercase tracking-widest text-primary">Output</div>
                <div className="font-headline text-lg font-bold text-primary">SOC Alerting</div>
                <div className="mt-4 text-[10px] text-primary">Real-time Mitigation</div>
              </div>
            </div>
          </div>
        </section>

        <section className="mx-auto max-w-[1440px] px-6 py-24">
          <h2 className="mb-16 text-center font-headline text-4xl font-bold text-primary">Precision Infrastructure</h2>
          <div className="grid grid-cols-1 gap-6 md:grid-cols-12">
            <div className="col-span-12 flex flex-col items-center gap-8 rounded-2xl border border-outline-variant/10 bg-surface-container-low p-8 transition-all hover:border-secondary/30 md:col-span-8 md:flex-row">
              <div className="flex-1">
                <div className="mb-6 flex h-12 w-12 items-center justify-center rounded-xl bg-secondary/10 text-secondary">
                  <span className="material-symbols-outlined">bolt</span>
                </div>
                <h3 className="mb-4 font-headline text-2xl font-bold text-primary">Real-time Detection</h3>
                <p className="text-on-surface-variant">
                  Continuous WebSocket streaming ensures anomalies are detected and reported within 12ms of the malicious frame entering the bus. No lag, no compromise.
                </p>
              </div>
              <div className="aspect-video w-full overflow-hidden rounded-xl border border-outline-variant/20 bg-surface-container-lowest md:w-64">
                <img
                  alt="Real-time Stream Visualization"
                  className="h-full w-full object-cover opacity-50 grayscale"
                  src="https://lh3.googleusercontent.com/aida-public/AB6AXuDuj6d9sFrT737plLuS89DSlHImsMxQNZ_bJ98I4U4jhOQLWsei4WAUm1weaJLdSwoJDA52tL6yA8W5Ac0mUqF6uyyApFhqHYMpQn1gu1DBm-MjcZQahBj69BrSZYswk6zhYRVqTKBmzVRO6oh0RshPejSzOeIr5Wg2bUP9aEj-a1nVwQtg1nvdnllfgKHXqyX6W_0DGzzqSKI9aU1h29BPJ-5TGjjqDSyERaThTv6FNqd3x6BoO6-yqQo46bHtAN-pH3Mhqn5PyCE"
                />
              </div>
            </div>

            <div className="col-span-12 rounded-2xl border border-outline-variant/10 bg-surface-container-low p-8 transition-all hover:border-secondary/30 md:col-span-4">
              <div className="mb-6 flex h-12 w-12 items-center justify-center rounded-xl bg-secondary/10 text-secondary">
                <span className="material-symbols-outlined">category</span>
              </div>
              <h3 className="mb-4 font-headline text-2xl font-bold text-primary">Multi-class</h3>
              <p className="mb-6 text-on-surface-variant">Granular classification of attack vectors including DoS, Fuzzy, Gear, and RPM spoofing attempts.</p>
              <div className="space-y-2">
                <div className="flex items-center gap-3">
                  <div className="h-2 w-2 rounded-full bg-secondary" />
                  <span className="font-mono text-xs text-on-surface-variant">Denial of Service</span>
                </div>
                <div className="flex items-center gap-3">
                  <div className="h-2 w-2 rounded-full bg-secondary" />
                  <span className="font-mono text-xs text-on-surface-variant">Fuzzy Injection</span>
                </div>
              </div>
            </div>

            <div className="col-span-12 rounded-2xl border border-outline-variant/10 bg-surface-container-low p-8 transition-all hover:border-secondary/30 md:col-span-4">
              <div className="mb-6 flex h-12 w-12 items-center justify-center rounded-xl bg-secondary/10 text-secondary">
                <span className="material-symbols-outlined">api</span>
              </div>
              <h3 className="mb-4 font-headline text-2xl font-bold text-primary">Production API</h3>
              <p className="text-on-surface-variant">
                Built on FastAPI, our RESTful endpoints provide high-throughput integration for OEM telematics systems and fleet management consoles.
              </p>
            </div>

            <div className="col-span-12 flex flex-col items-center gap-8 rounded-2xl border border-outline-variant/10 bg-surface-container-low p-8 transition-all hover:border-secondary/30 md:col-span-8 md:flex-row-reverse">
              <div className="flex-1">
                <div className="mb-6 flex h-12 w-12 items-center justify-center rounded-xl bg-secondary/10 text-secondary">
                  <span className="material-symbols-outlined">analytics</span>
                </div>
                <h3 className="mb-4 font-headline text-2xl font-bold text-primary">Rich Analytics</h3>
                <p className="text-on-surface-variant">
                  Interactive reports generate deep-dive metrics on network health, anomaly frequency, and predictive maintenance insights for secure automotive operations.
                </p>
              </div>
              <div className="aspect-video w-full overflow-hidden rounded-xl border border-outline-variant/20 bg-surface-container-lowest md:w-64">
                <img
                  alt="Interactive Metrics"
                  className="h-full w-full object-cover opacity-50 grayscale"
                  src="https://lh3.googleusercontent.com/aida-public/AB6AXuCQf3vxjquKSk2gNxUrn-ztY26PNFhRLZ5I0EKquVyYWAsjZ1vxwjwEZ529-4qAUg_vqMAZCfd4IO3ZB7l2Ih-DVRX1FQtOh_jdwV-si9umHc_TLUc-_fjYPal57GiZmdllcwBwgId3g9-xHsexYR1nyIoGS17UHYZ7Z71tcBwjTAkrJZtZKwc4XnatQLOPoWAiSjnLP3AljmyAL5ijEnrJWfBADfB76WLeXPksMdfW_BanHVHlAVODM-A5SyKmK-UYqBG8yrUj_Yg"
                />
              </div>
            </div>
          </div>
        </section>
      </main>

      <footer className="mt-auto w-full bg-surface-container-low">
        <div className="mx-auto flex w-full max-w-[1440px] flex-col items-center justify-between px-8 py-12 md:flex-row">
          <div className="mb-8 md:mb-0">
            <div className="mb-2 font-headline text-xl font-bold text-primary">IDS.Sentinel</div>
            <div className="text-xs text-on-surface-variant">© 2024 IDS.Sentinel Automotive Cyber-Intelligence</div>
          </div>
          <div className="flex gap-12">
            <div className="flex flex-col gap-2">
              <span className="mb-2 font-mono text-[10px] uppercase tracking-widest text-outline">Platform</span>
              <Link className="text-xs text-on-surface-variant transition-colors hover:text-primary" to="/security">
                Mission
              </Link>
              <Link className="text-xs text-on-surface-variant transition-colors hover:text-primary" to="/pipeline">
                Tech Stack
              </Link>
            </div>
            <div className="flex flex-col gap-2">
              <span className="mb-2 font-mono text-[10px] uppercase tracking-widest text-outline">Resources</span>
              <Link className="text-xs text-on-surface-variant underline transition-colors hover:text-primary" to="/integration">
                Documentation
              </Link>
              <Link className="text-xs text-on-surface-variant transition-colors hover:text-primary" to="/security">
                Contact
              </Link>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}
