import { ConsoleLayout } from '../layout/ConsoleLayout';

export function AboutPage() {
  return (
    <ConsoleLayout activeNav="security">
      <main className="mx-auto max-w-7xl px-6 pb-12 pt-24 md:px-12">
        <header className="mb-16">
          <h1 className="mb-4 font-headline text-5xl font-bold tracking-tight text-primary">Precision Integrity</h1>
          <p className="max-w-2xl text-lg text-on-surface-variant">
            Ensuring the cryptographic and physical safety of automotive networks through advanced intrusion detection and hardened system architecture.
          </p>
        </header>

        <section className="mb-24 grid grid-cols-1 gap-8 lg:grid-cols-12">
          <div className="lg:col-span-7">
            <div className="mb-6 flex items-center gap-2">
              <span className="material-symbols-outlined text-secondary">security</span>
              <h2 className="font-headline text-2xl font-bold">Threat Model</h2>
            </div>
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
              <div className="rounded-xl border border-outline-variant/10 bg-surface-container-lowest p-6 shadow-sm">
                <span className="material-symbols-outlined mb-4 text-error">car_crash</span>
                <h3 className="mb-2 font-headline text-lg font-bold">Injection Attacks</h3>
                <p className="text-sm text-on-surface-variant">Mitigating unauthorized CAN message injection that could manipulate ECU behavior or bypass safety protocols.</p>
              </div>
              <div className="rounded-xl border border-outline-variant/10 bg-surface-container-lowest p-6 shadow-sm">
                <span className="material-symbols-outlined mb-4 text-secondary">sensors_off</span>
                <h3 className="mb-2 font-headline text-lg font-bold">DoS Mitigation</h3>
                <p className="text-sm text-on-surface-variant">Preventing high-priority message flooding designed to saturate bus capacity and delay critical safety frames.</p>
              </div>
              <div className="rounded-xl border border-outline-variant/10 bg-surface-container-lowest p-6 shadow-sm">
                <span className="material-symbols-outlined mb-4 text-secondary">key</span>
                <h3 className="mb-2 font-headline text-lg font-bold">ECU Impersonation</h3>
                <p className="text-sm text-on-surface-variant">Deep packet inspection to verify frame origins and prevent spoofing of legitimate Electronic Control Units.</p>
              </div>
              <div className="rounded-xl border border-outline-variant/10 bg-surface-container-lowest p-6 shadow-sm">
                <span className="material-symbols-outlined mb-4 text-secondary">memory</span>
                <h3 className="mb-2 font-headline text-lg font-bold">Bus-Off Exploits</h3>
                <p className="text-sm text-on-surface-variant">Monitoring error frame counters to detect forced bus-off states used to silence diagnostic and safety systems.</p>
              </div>
            </div>
          </div>

          <div className="rounded-xl bg-surface-container-low p-8 lg:col-span-5">
            <h3 className="mb-6 flex items-center gap-2 font-headline text-xl font-bold">
              <span className="material-symbols-outlined text-primary">verified</span>
              Hardening Checklist
            </h3>
            <ul className="space-y-6">
              {[
                ['TLS 1.3 Transport', 'All telemetry and API calls are wrapped in modern cryptographic envelopes.'],
                ['JWT Authentication', 'Stateless, cryptographically signed tokens for secure session management.'],
                ['CORS & Security Headers', 'Strict origin policy and CSP to mitigate cross-site scripting and framing.'],
                ['Dynamic Rate Limiting', 'Sliding-window rate limiters prevent brute-force and API exhaustion.'],
              ].map(([title, desc]) => (
                <li key={title} className="flex gap-4">
                  <span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-tertiary-container/20 text-tertiary-fixed-dim">
                    <span className="material-symbols-outlined text-sm" style={{ fontVariationSettings: "'FILL' 1" }}>
                      check
                    </span>
                  </span>
                  <div>
                    <span className="block font-headline font-bold text-primary">{title}</span>
                    <p className="text-xs text-on-surface-variant">{desc}</p>
                  </div>
                </li>
              ))}
            </ul>
          </div>
        </section>

        <section className="mb-24">
          <div className="glass-panel relative overflow-hidden rounded-[2rem] bg-gradient-to-br from-surface-container-lowest to-surface-container-low p-10 md:p-16">
            <div className="relative z-10 max-w-3xl">
              <span className="mb-6 inline-block rounded-full bg-secondary-container px-3 py-1 text-xs font-bold text-on-secondary-container">PRIVACY FIRST</span>
              <h2 className="mb-6 font-headline text-4xl font-bold leading-tight text-primary">Data Handling &amp; Provenance</h2>
              <div className="space-y-6 text-on-surface-variant">
                <p>
                  We treat vehicle data with the same sensitivity as financial records. Our <strong>Data Minimization Policy</strong> ensures that only essential CAN message IDs and payloads required for anomaly detection are transmitted.
                </p>
                <div className="mt-10 grid grid-cols-1 gap-8 md:grid-cols-2">
                  <div>
                    <h4 className="mb-2 font-headline font-bold text-primary">Anonymization</h4>
                    <p className="text-sm">VIN and GPS coordinates are masked at the edge before analysis, ensuring data remains non-identifiable during processing.</p>
                  </div>
                  <div>
                    <h4 className="mb-2 font-headline font-bold text-primary">Provenance</h4>
                    <p className="text-sm">We utilize public research datasets and verified OEM captures with documented lineage.</p>
                  </div>
                </div>
              </div>
            </div>
            <div className="absolute -right-20 -top-20 h-80 w-80 rounded-full bg-secondary-container/10 blur-3xl" />
          </div>
        </section>

        <section className="mb-24">
          <div className="mb-8 flex items-center justify-between">
            <h2 className="font-headline text-3xl font-bold">Project &amp; Roadmap</h2>
            <div className="mx-8 h-px flex-1 bg-outline-variant/20" />
          </div>
          <div className="grid grid-cols-1 gap-6 md:grid-cols-3">
            <div className="relative col-span-2 flex flex-col justify-between overflow-hidden rounded-[1.5rem] bg-primary p-10 text-on-primary">
              <div className="relative z-10">
                <h3 className="mb-4 font-headline text-2xl font-bold">Our Mission</h3>
                <p className="text-lg leading-relaxed opacity-80">
                  To democratize automotive security by providing open, high-precision detection models that protect the vehicles of tomorrow from the cyber threats of today.
                </p>
              </div>
              <div className="relative z-10 mt-12 flex gap-4">
                <div className="flex -space-x-3">
                  <img
                    className="h-10 w-10 rounded-full border-2 border-primary object-cover"
                    src="https://lh3.googleusercontent.com/aida-public/AB6AXuCHRX4e5LgRRiuV3Fd19GhNYf2I4d4jNxO8QMHIqoEj2GEX0Eva_pKvov2IawW_HVXDJwmrXuntYh6XO9cz9pqwkovfB9qpE4BTuiV8uuUtOrtT6mKEGJ5_Y3qMWQnMcREsR3v_wp6C_SeREsNxSyqrCBOjCPQLjDG5okBnHV89P2TTw0VT0u800vW9ydsecnig3evyLprLTFp9yWA32ai9BK2lHGOR2aH4zUTuvdXkljaB3Hj25IKceIjvTFH9uJSmfcfsRXtHsJ0"
                    alt="Engineer"
                  />
                  <img
                    className="h-10 w-10 rounded-full border-2 border-primary object-cover"
                    src="https://lh3.googleusercontent.com/aida-public/AB6AXuC1D1VCW7Jg1UFde3B4CafCH0ecmA5av7hELRKFANILa40AWRwUJBCIlWLvqbnHuetcMs7PUcySm2dcqJxbflZ1smKA0libAgSXBGZHYW4EOVYeqOpq-KylhRgdRfLCV0tZc1rXIQPBJoYtCZdbfIX7G0CDXLNSbM-c_P-neVdhLJbHKIirvDsq0SqpMjt3bfOVi_PCuCkXAUUW0AKZX4to4OzptqJplqJM0S9Zc8wEOHZMiQmShxjnAc282Fe8VUO4xCuQ6J1OSFM"
                    alt="Engineer"
                  />
                  <div className="flex h-10 w-10 items-center justify-center rounded-full border-2 border-primary bg-primary-container text-xs font-bold">+12</div>
                </div>
                <p className="self-center text-sm opacity-60">Contributors from 4 global teams</p>
              </div>
              <div className="absolute bottom-[-10%] right-[-5%] opacity-10">
                <span className="material-symbols-outlined text-[160px]">shield_with_heart</span>
              </div>
            </div>

            <div className="rounded-[1.5rem] bg-surface-container-high p-8">
              <h3 className="mb-6 font-headline text-xl font-bold">Roadmap</h3>
              <div className="space-y-6">
                <div className="flex gap-4">
                  <span className="pt-1 font-label text-xs font-bold text-secondary">Q3 24</span>
                  <p className="text-sm font-medium">Edge deployment for embedded ARM Cortex-M7 platforms.</p>
                </div>
                <div className="flex gap-4">
                  <span className="pt-1 font-label text-xs font-bold text-on-surface-variant">Q4 24</span>
                  <p className="text-sm font-medium opacity-60">Full CAN-FD support for higher data rates.</p>
                </div>
                <div className="flex gap-4">
                  <span className="pt-1 font-label text-xs font-bold text-on-surface-variant">Q1 25</span>
                  <p className="text-sm font-medium opacity-60">SHAP-based explainability for detected anomalies.</p>
                </div>
              </div>
            </div>
          </div>
        </section>

        <section className="mb-24">
          <h2 className="mb-8 text-center font-headline text-2xl font-bold">Engineered For Performance</h2>
          <div className="grid grid-cols-1 gap-8 md:grid-cols-3">
            <div className="p-6">
              <div className="mb-6 flex items-center gap-3">
                <span className="material-symbols-outlined text-secondary">psychology</span>
                <h4 className="font-headline text-lg font-bold">Machine Learning</h4>
              </div>
              <div className="flex flex-wrap gap-2">
                {['PyTorch', 'Transformers', 'Scikit-learn', 'NumPy'].map((item) => (
                  <span key={item} className="rounded-full bg-surface-container px-3 py-1 font-label text-xs text-on-surface-variant">
                    {item}
                  </span>
                ))}
              </div>
            </div>

            <div className="p-6">
              <div className="mb-6 flex items-center gap-3">
                <span className="material-symbols-outlined text-secondary">terminal</span>
                <h4 className="font-headline text-lg font-bold">Backend Engine</h4>
              </div>
              <div className="flex flex-wrap gap-2">
                {['FastAPI', 'WebSockets', 'Pydantic', 'Uvicorn'].map((item) => (
                  <span key={item} className="rounded-full bg-surface-container px-3 py-1 font-label text-xs text-on-surface-variant">
                    {item}
                  </span>
                ))}
              </div>
            </div>

            <div className="p-6">
              <div className="mb-6 flex items-center gap-3">
                <span className="material-symbols-outlined text-secondary">layers</span>
                <h4 className="font-headline text-lg font-bold">Interface</h4>
              </div>
              <div className="flex flex-wrap gap-2">
                {['React', 'Tailwind CSS', 'Recharts', 'TypeScript'].map((item) => (
                  <span key={item} className="rounded-full bg-surface-container px-3 py-1 font-label text-xs text-on-surface-variant">
                    {item}
                  </span>
                ))}
              </div>
            </div>
          </div>
        </section>

        <section className="mx-auto mb-24 max-w-4xl">
          <div className="rounded-[1.5rem] bg-surface-container-low p-8 text-center md:p-12">
            <h2 className="mb-4 font-headline text-3xl font-bold">Connect with Our Engineers</h2>
            <p className="mb-10 text-on-surface-variant">Have questions about deployment or contribution? We are here to help.</p>
            <form className="grid grid-cols-1 gap-4 text-left md:grid-cols-2">
              <div className="space-y-2">
                <label className="px-1 text-xs font-bold text-primary">Name</label>
                <input className="w-full rounded-xl border-none bg-surface-container-lowest p-3 focus:ring-1 focus:ring-secondary" placeholder="Your Name" type="text" />
              </div>
              <div className="space-y-2">
                <label className="px-1 text-xs font-bold text-primary">Email</label>
                <input className="w-full rounded-xl border-none bg-surface-container-lowest p-3 focus:ring-1 focus:ring-secondary" placeholder="email@organization.com" type="email" />
              </div>
              <div className="space-y-2 md:col-span-2">
                <label className="px-1 text-xs font-bold text-primary">Message</label>
                <textarea className="w-full rounded-xl border-none bg-surface-container-lowest p-3 focus:ring-1 focus:ring-secondary" placeholder="How can we assist your security journey?" rows={4} />
              </div>
              <div className="mt-4 md:col-span-2">
                <button className="w-full rounded-xl bg-primary py-4 font-bold text-on-primary transition-opacity hover:opacity-90" type="button">
                  Send Secure Message
                </button>
              </div>
            </form>
          </div>
        </section>
      </main>
    </ConsoleLayout>
  );
}
