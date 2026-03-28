import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Legend,
  Line,
  LineChart,
  Pie,
  PieChart,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';
import { useLiveStream } from '../hooks/useLiveStream';

function StatCard({ title, value, tone }: { title: string; value: string; tone?: 'default' | 'success' | 'danger' }) {
  return (
    <div className={`stat-card ${tone ?? 'default'}`}>
      <p>{title}</p>
      <h3>{value}</h3>
    </div>
  );
}

const PIE_COLORS = ['#0056D2', '#D64545', '#0E9F6E', '#F59E0B', '#3B82F6'];

export function DashboardPage() {
  const {
    points,
    alerts,
    connected,
    totalAnalyzed,
    attacksDetected,
    detectionRate,
    threshold,
    scoreDistribution,
    attackBreakdown,
  } = useLiveStream();

  return (
    <div className="dashboard-grid">
      <section className="hero-row">
        <StatCard title="Total Analyzed" value={totalAnalyzed.toLocaleString()} />
        <StatCard title="Attacks Detected" value={attacksDetected.toLocaleString()} tone={attacksDetected > 0 ? 'danger' : 'default'} />
        <StatCard title="Detection Rate" value={`${detectionRate.toFixed(2)}%`} />
        <StatCard title="System Status" value={connected ? 'Live' : 'Disconnected'} tone={connected ? 'success' : 'danger'} />
      </section>

      <section className="chart-panel large">
        <div className="panel-head">
          <h2>Live Anomaly Scores</h2>
          <span>Threshold: {threshold.toFixed(4)}</span>
        </div>
        <ResponsiveContainer width="100%" height={360}>
          <LineChart data={points}>
            <CartesianGrid strokeDasharray="3 3" stroke="#E5EAF5" />
            <XAxis dataKey="time" minTickGap={28} stroke="#64748B" />
            <YAxis stroke="#64748B" domain={['auto', 'auto']} />
            <Tooltip />
            <ReferenceLine y={threshold} stroke="#F97316" strokeDasharray="6 4" label="Threshold" />
            <Line
              type="monotone"
              dataKey="score"
              stroke="#0056D2"
              strokeWidth={2.5}
              dot={false}
              isAnimationActive
            />
            <Line
              type="monotone"
              dataKey="attackScore"
              stroke="transparent"
              dot={{ fill: '#D64545', stroke: '#D64545', r: 4 }}
              connectNulls={false}
            />
          </LineChart>
        </ResponsiveContainer>
      </section>

      <aside className="alerts-panel">
        <div className="panel-head">
          <h2>Recent Alerts</h2>
          <span>Last 10 detections</span>
        </div>
        <div className="alerts-list">
          {alerts.length === 0 ? (
            <p className="empty-state">No attacks detected in current stream.</p>
          ) : (
            alerts.map((alert) => (
              <article key={alert.id} className="alert-item">
                <div>
                  <h4>{alert.attackType}</h4>
                  <p>{alert.time}</p>
                </div>
                <div className="alert-meta">
                  <span>{alert.score.toFixed(4)}</span>
                  <small>{(alert.confidence * 100).toFixed(1)}%</small>
                </div>
              </article>
            ))
          )}
        </div>
      </aside>

      <section className="chart-panel">
        <div className="panel-head">
          <h2>Score Distribution</h2>
        </div>
        <ResponsiveContainer width="100%" height={280}>
          <BarChart data={scoreDistribution}>
            <CartesianGrid strokeDasharray="3 3" stroke="#E5EAF5" />
            <XAxis dataKey="bin" interval={1} angle={-15} textAnchor="end" height={48} stroke="#64748B" />
            <YAxis stroke="#64748B" />
            <Tooltip />
            <Bar dataKey="count" fill="#0056D2" radius={[6, 6, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </section>

      <section className="chart-panel">
        <div className="panel-head">
          <h2>Attack Type Breakdown</h2>
        </div>
        <ResponsiveContainer width="100%" height={280}>
          <PieChart>
            <Pie data={attackBreakdown} dataKey="value" nameKey="name" outerRadius={95} label>
              {attackBreakdown.map((entry, index) => (
                <Cell key={entry.name} fill={PIE_COLORS[index % PIE_COLORS.length]} />
              ))}
            </Pie>
            <Tooltip />
            <Legend />
          </PieChart>
        </ResponsiveContainer>
      </section>
    </div>
  );
}
