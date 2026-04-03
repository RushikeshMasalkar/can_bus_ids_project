import { ConsoleLayout } from '../layout/ConsoleLayout';

export function AboutPage() {
  return (
    <ConsoleLayout activeNav="security">
      <main className="mx-auto max-w-7xl px-6 pb-12 pt-24 md:px-12">
        <header className="mb-16">
          <h1 className="mb-4 font-headline text-5xl font-bold tracking-tight text-primary">Security Architecture &amp; Threat Posture</h1>
          <p className="max-w-2xl text-lg text-on-surface-variant">
            A formal specification of the adversarial threat model, platform hardening measures, data governance policies, and report integrity architecture governing the IDS Sentinel intrusion detection framework.
          </p>
        </header>

        <section className="mb-24 grid grid-cols-1 gap-8 lg:grid-cols-12">
          <div className="lg:col-span-7">
            <div className="mb-6 flex items-center gap-2">
              <span className="material-symbols-outlined text-secondary">security</span>
              <h2 className="font-headline text-2xl font-bold">Adversarial Threat Model</h2>
            </div>
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
              <div className="rounded-xl border border-outline-variant/10 bg-surface-container-lowest p-6 shadow-sm">
                <span className="material-symbols-outlined mb-4 text-error">car_crash</span>
                <h3 className="mb-2 font-headline text-lg font-bold">Frame Injection Attacks</h3>
                <p className="text-sm text-on-surface-variant">Unauthorized CAN message injection is mitigated through continuous sequence-level anomaly monitoring. The Transformer-based Stage-1 scorer is designed to detect deviations in arbitration ID ordering and frequency patterns that are characteristic of externally injected frames attempting to manipulate ECU behavior or circumvent safety-critical protocols.</p>
              </div>
              <div className="rounded-xl border border-outline-variant/10 bg-surface-container-lowest p-6 shadow-sm">
                <span className="material-symbols-outlined mb-4 text-secondary">sensors_off</span>
                <h3 className="mb-2 font-headline text-lg font-bold">Denial-of-Service Mitigation</h3>
                <p className="text-sm text-on-surface-variant">High-priority message flooding attacks, designed to saturate bus bandwidth capacity and delay the transmission of safety-critical frames, are identified through anomalous inter-frame arrival time distributions and elevated byte-level delta concentrations (e.g., 0xFF saturation patterns) within the monitored sequence window.</p>
              </div>
              <div className="rounded-xl border border-outline-variant/10 bg-surface-container-lowest p-6 shadow-sm">
                <span className="material-symbols-outlined mb-4 text-secondary">key</span>
                <h3 className="mb-2 font-headline text-lg font-bold">ECU Impersonation Detection</h3>
                <p className="text-sm text-on-surface-variant">Deep sequence analysis is employed to statistically verify frame origin authenticity and detect spoofing of legitimate Electronic Control Unit communication patterns. The learned CAN grammar model captures ECU-specific temporal and sequential signatures that are disrupted during impersonation attempts.</p>
              </div>
              <div className="rounded-xl border border-outline-variant/10 bg-surface-container-lowest p-6 shadow-sm">
                <span className="material-symbols-outlined mb-4 text-secondary">memory</span>
                <h3 className="mb-2 font-headline text-lg font-bold">Bus-Off State Exploitation</h3>
                <p className="text-sm text-on-surface-variant">Error frame counter manipulation attacks, utilized to force targeted ECUs into the CAN bus-off state, are detected through monitoring of anomalous error frame frequency patterns and the resulting disruption to normal arbitration ID sequence grammar.</p>
              </div>
            </div>
          </div>

          <div className="rounded-xl bg-surface-container-low p-8 lg:col-span-5">
            <h3 className="mb-6 flex items-center gap-2 font-headline text-xl font-bold">
              <span className="material-symbols-outlined text-primary">verified</span>
              Platform Hardening Checklist
            </h3>
            <ul className="space-y-6">
              {[
                ['TLS 1.3 Transport Encryption', 'All telemetry data and API communications are encapsulated within TLS 1.3 cryptographic transport envelopes, ensuring confidentiality and integrity of inference payloads in transit.'],
                ['JWT-Based Stateless Authentication', 'Stateless, cryptographically signed JSON Web Tokens (JWT) are employed for secure session management, eliminating server-side session state and reducing the attack surface for session hijacking.'],
                ['CORS Policy & Content Security Headers', 'Strict Cross-Origin Resource Sharing (CORS) policies and Content Security Policy (CSP) headers are enforced to mitigate cross-site scripting (XSS) and clickjacking attack vectors.'],
                ['Sliding-Window Rate Limiting', 'Adaptive rate limiting with sliding-window counters is implemented to prevent brute-force enumeration, API exhaustion attacks, and automated sequence fuzzing attempts against the inference endpoints.'],
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

        {/* HMAC-SHA256 Audit Trail Architecture — NEW SECTION */}
        <section className="mb-24">
          <div className="rounded-[2rem] border border-outline-variant/10 bg-surface-container-lowest p-10 md:p-16">
            <div className="mb-8 flex items-center gap-3">
              <span className="material-symbols-outlined text-3xl text-secondary">fingerprint</span>
              <div>
                <h2 className="font-headline text-3xl font-bold text-primary">IDS Report Integrity &amp; Non-Repudiation Architecture</h2>
                <p className="mt-1 text-sm text-on-surface-variant">Cryptographic audit trail for tamper-evident anomaly detection reporting</p>
              </div>
            </div>

            <div className="mb-8 space-y-4 leading-relaxed text-on-surface-variant">
              <p>
                To ensure the forensic admissibility and chain-of-custody integrity of anomaly detection reports, the IDS Sentinel platform implements a simulated <strong>HMAC-SHA256 Audit Trail</strong> architecture. This mechanism ensures that the final anomaly detection reports generated by the inference pipeline cannot be silently modified, forged, or repudiated by any party in the data processing chain.
              </p>
              <p>
                Each structured JSON report emitted by the inference backend undergoes the following cryptographic integrity workflow:
              </p>
            </div>

            <div className="mb-8 grid grid-cols-1 gap-4 md:grid-cols-4">
              <div className="rounded-xl border border-outline-variant/20 bg-surface-container-low p-6">
                <div className="mb-3 inline-flex h-8 w-8 items-center justify-center rounded-full bg-primary text-sm font-bold text-white">1</div>
                <h4 className="mb-2 font-headline text-sm font-bold text-primary">Report Generation</h4>
                <p className="text-xs text-on-surface-variant">
                  The inference pipeline emits a structured JSON report containing the anomaly score, classification result, confidence metrics, and timestamp for each evaluated sequence.
                </p>
              </div>
              <div className="rounded-xl border border-outline-variant/20 bg-surface-container-low p-6">
                <div className="mb-3 inline-flex h-8 w-8 items-center justify-center rounded-full bg-primary text-sm font-bold text-white">2</div>
                <h4 className="mb-2 font-headline text-sm font-bold text-primary">SHA-256 Content Hash</h4>
                <p className="text-xs text-on-surface-variant">
                  A SHA-256 cryptographic digest is computed over the canonical JSON representation of the report, producing a unique 256-bit fingerprint of the report contents.
                </p>
              </div>
              <div className="rounded-xl border border-outline-variant/20 bg-surface-container-low p-6">
                <div className="mb-3 inline-flex h-8 w-8 items-center justify-center rounded-full bg-primary text-sm font-bold text-white">3</div>
                <h4 className="mb-2 font-headline text-sm font-bold text-primary">HMAC Signature</h4>
                <p className="text-xs text-on-surface-variant">
                  The content hash is signed using HMAC-SHA256 with a station-specific secret key, producing a keyed message authentication code that binds the report to the originating IDS node.
                </p>
              </div>
              <div className="rounded-xl border border-secondary-container bg-secondary-container/20 p-6">
                <div className="mb-3 inline-flex h-8 w-8 items-center justify-center rounded-full bg-secondary text-sm font-bold text-white">✓</div>
                <h4 className="mb-2 font-headline text-sm font-bold text-primary">Tamper-Evident Seal</h4>
                <p className="text-xs text-on-surface-variant">
                  The HMAC signature is appended to the report as a tamper-evident seal. Any modification to the report content invalidates the signature, enabling immediate tampering detection during forensic review.
                </p>
              </div>
            </div>

            <div className="rounded-xl bg-surface-container-low p-6">
              <h4 className="mb-3 font-headline text-sm font-bold text-primary">Non-Repudiation Guarantees</h4>
              <div className="space-y-3 text-sm text-on-surface-variant">
                <p>
                  <strong>Data Integrity:</strong> The SHA-256 content hash ensures that any modification to the report — including alteration of anomaly scores, classification labels, or timestamps — is computationally detectable. The probability of a hash collision is negligible (2⁻²⁵⁶).
                </p>
                <p>
                  <strong>Origin Authentication:</strong> The HMAC-SHA256 signature, computed with a station-specific secret key, cryptographically binds each report to the originating IDS Sentinel node. Reports cannot be forged without possession of the key material.
                </p>
                <p>
                  <strong>Chain-of-Custody:</strong> Sequential HMAC signatures establish a verifiable chain-of-custody for all anomaly detection artifacts, enabling post-incident forensic reconstruction and regulatory compliance auditing.
                </p>
              </div>
            </div>

            <div className="mt-6 rounded-xl bg-surface-container-low p-4">
              <p className="font-mono text-[10px] text-on-surface-variant">
                Note: The HMAC-SHA256 audit trail architecture is described at the design specification level. Cryptographic key management, HSM integration, and certificate rotation protocols are documented in the deployment security guide and are not implemented in the current research prototype.
              </p>
            </div>
          </div>
        </section>

        {/* Data Handling & Provenance */}
        <section className="mb-24">
          <div className="glass-panel relative overflow-hidden rounded-[2rem] bg-gradient-to-br from-surface-container-lowest to-surface-container-low p-10 md:p-16">
            <div className="relative z-10 max-w-3xl">
              <span className="mb-6 inline-block rounded-full bg-secondary-container px-3 py-1 text-xs font-bold text-on-secondary-container">DATA GOVERNANCE</span>
              <h2 className="mb-6 font-headline text-4xl font-bold leading-tight text-primary">Data Handling &amp; Provenance Policy</h2>
              <div className="space-y-6 text-on-surface-variant">
                <p>
                  All vehicle telemetry data is treated with the equivalent sensitivity classification of financial records under the principle of <strong>Data Minimization</strong>. Only the minimum requisite CAN message arbitration identifiers and payload bytes essential for anomaly detection inference are transmitted and processed by the system.
                </p>
                <div className="mt-10 grid grid-cols-1 gap-8 md:grid-cols-2">
                  <div>
                    <h4 className="mb-2 font-headline font-bold text-primary">Anonymization Protocol</h4>
                    <p className="text-sm">Vehicle Identification Numbers (VIN) and GPS coordinate telemetry are cryptographically masked at the edge computing layer prior to analysis, ensuring that all processed data remains non-identifiable throughout the inference pipeline.</p>
                  </div>
                  <div>
                    <h4 className="mb-2 font-headline font-bold text-primary">Dataset Provenance</h4>
                    <p className="text-sm">The system is evaluated exclusively on publicly available research datasets with documented lineage, including the Car-Hacking Dataset (Seo et al., 2018) and verified OEM captures with institutional review board (IRB) approval.</p>
                  </div>
                </div>
              </div>
            </div>
            <div className="absolute -right-20 -top-20 h-80 w-80 rounded-full bg-secondary-container/10 blur-3xl" />
          </div>
        </section>

        {/* Technology Stack */}
        <section className="mb-24">
          <h2 className="mb-8 text-center font-headline text-2xl font-bold">Engineered for Performance</h2>
          <div className="grid grid-cols-1 gap-8 md:grid-cols-3">
            <div className="p-6">
              <div className="mb-6 flex items-center gap-3">
                <span className="material-symbols-outlined text-secondary">psychology</span>
                <h4 className="font-headline text-lg font-bold">Machine Learning Stack</h4>
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
                <h4 className="font-headline text-lg font-bold">Inference Backend</h4>
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
                <h4 className="font-headline text-lg font-bold">Observability Interface</h4>
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

        {/* Contact */}
        <section className="mx-auto mb-24 max-w-4xl">
          <div className="rounded-[1.5rem] bg-surface-container-low p-8 text-center md:p-12">
            <h2 className="mb-4 font-headline text-3xl font-bold">Research Collaboration &amp; Deployment Inquiries</h2>
            <p className="mb-10 text-on-surface-variant">For questions regarding academic collaboration, dataset access, model deployment, or contribution to the IDS Sentinel project, please use the secure contact form below.</p>
            <form className="grid grid-cols-1 gap-4 text-left md:grid-cols-2">
              <div className="space-y-2">
                <label className="px-1 text-xs font-bold text-primary">Name</label>
                <input className="w-full rounded-xl border-none bg-surface-container-lowest p-3 focus:ring-1 focus:ring-secondary" placeholder="Your Name" type="text" />
              </div>
              <div className="space-y-2">
                <label className="px-1 text-xs font-bold text-primary">Institutional Email</label>
                <input className="w-full rounded-xl border-none bg-surface-container-lowest p-3 focus:ring-1 focus:ring-secondary" placeholder="researcher@institution.edu" type="email" />
              </div>
              <div className="space-y-2 md:col-span-2">
                <label className="px-1 text-xs font-bold text-primary">Message</label>
                <textarea className="w-full rounded-xl border-none bg-surface-container-lowest p-3 focus:ring-1 focus:ring-secondary" placeholder="Describe your research interest or deployment requirements..." rows={4} />
              </div>
              <div className="mt-4 md:col-span-2">
                <button className="w-full rounded-xl bg-primary py-4 font-bold text-on-primary transition-opacity hover:opacity-90" type="button">
                  Submit Secure Inquiry
                </button>
              </div>
            </form>
          </div>
        </section>
      </main>
    </ConsoleLayout>
  );
}
