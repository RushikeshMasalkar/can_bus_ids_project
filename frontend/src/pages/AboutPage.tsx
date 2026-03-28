export function AboutPage() {
  const stack = [
    { name: 'Python', desc: 'Data processing, training, and inference orchestration.' },
    { name: 'PyTorch', desc: 'DistilBERT training and masked-loss anomaly scoring.' },
    { name: 'HuggingFace', desc: 'Transformer architecture primitives and tokenizer workflow.' },
    { name: 'FastAPI', desc: 'Low-latency inference APIs and real-time WebSocket streaming.' },
    { name: 'React', desc: 'Interactive enterprise monitoring and analysis UI.' },
    { name: 'Docker', desc: 'Portable deployment target for backend and frontend services.' },
  ];

  return (
    <div className="about-layout">
      <section className="card">
        <div className="panel-head">
          <h2>Project Overview</h2>
        </div>
        <p>
          CAN-IDS is a transformer-based intrusion detection platform that learns normal vehicular communication patterns
          and flags deviations in real time. The model is trained on high-volume CAN traffic and deployed with a
          production API and enterprise-grade monitoring interface.
        </p>
      </section>

      <section className="card">
        <div className="panel-head">
          <h2>Architecture Flow</h2>
        </div>
        <div className="architecture-wrap">
          <svg viewBox="0 0 960 190" className="architecture-svg" role="img" aria-label="CAN IDS architecture flow">
            <defs>
              <marker id="arrow" markerWidth="10" markerHeight="10" refX="8" refY="3" orient="auto" markerUnits="strokeWidth">
                <path d="M0,0 L0,6 L9,3 z" fill="#0056D2" />
              </marker>
            </defs>

            <rect x="20" y="60" width="150" height="64" rx="14" />
            <text x="95" y="97" textAnchor="middle">CAN Bus Data</text>

            <line x1="170" y1="92" x2="230" y2="92" markerEnd="url(#arrow)" />
            <rect x="230" y="60" width="150" height="64" rx="14" />
            <text x="305" y="97" textAnchor="middle">Tokenizer</text>

            <line x1="380" y1="92" x2="440" y2="92" markerEnd="url(#arrow)" />
            <rect x="440" y="60" width="160" height="64" rx="14" />
            <text x="520" y="97" textAnchor="middle">DistilBERT</text>

            <line x1="600" y1="92" x2="660" y2="92" markerEnd="url(#arrow)" />
            <rect x="660" y="60" width="160" height="64" rx="14" />
            <text x="740" y="97" textAnchor="middle">Anomaly Score</text>

            <line x1="820" y1="92" x2="880" y2="92" markerEnd="url(#arrow)" />
            <rect x="880" y="60" width="140" height="64" rx="14" />
            <text x="950" y="84" textAnchor="middle">Threshold</text>
            <text x="950" y="107" textAnchor="middle">and Alert</text>
          </svg>
        </div>
      </section>

      <section className="card">
        <div className="panel-head">
          <h2>Technology Stack</h2>
        </div>
        <div className="stack-grid">
          {stack.map((item) => (
            <article key={item.name}>
              <h4>{item.name}</h4>
              <p>{item.desc}</p>
            </article>
          ))}
        </div>
      </section>
    </div>
  );
}
