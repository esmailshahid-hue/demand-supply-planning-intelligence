import { type ForecastResult, number, shortDate } from './api';

export default function ForecastChart({ result }: { result: ForecastResult }) {
  const history = result.history;
  const all = [...history.map(p => p.observed_sales), ...result.forecast.map(p => p.forecast_units)];
  const max = Math.max(1, ...all.filter((v): v is number => v !== null)) * 1.15;
  const x = (i: number) => 45 + i / 111 * 830;
  const y = (value: number) => 200 - value / max * 165;
  const forecastPoints = (start: number, end: number) => result.forecast.slice(start, end).map((p, i) => p.forecast_units === null ? null : `${x(56 + start + i)},${y(p.forecast_units)}`);
  const segments = (points: (string | null)[]) => points.reduce<string[][]>((acc, point) => {
    if (point === null) acc.push([]); else acc[acc.length - 1].push(point);
    return acc;
  }, [[]]).filter(s => s.length);
  return <div className="chart-wrap">
    <svg className="chart" viewBox="0 0 900 240" role="img" aria-labelledby="chart-title chart-desc">
      <title id="chart-title">Observed sales and selected forecast for {result.product_name}</title>
      <desc id="chart-desc">Last 56 historical days and next 56 forecast days. Amber circles are censored sales, which are lower bounds. Missing observations break the line. Forecast days 29 to 56 are provisional. A daily data table follows below.</desc>
      <rect x={x(56)} y="20" width={x(84) - x(56)} height="180" fill="#edf4ee" />
      <rect x={x(84)} y="20" width={875 - x(84)} height="180" fill="#f5f2eb" />
      {[0, .25, .5, .75, 1].map(r => <g key={r}><line x1="45" x2="875" y1={y(max * r)} y2={y(max * r)} stroke="#e5e8e2"/><text x="35" y={y(max * r) + 4} textAnchor="end">{number(max * r, 0)}</text></g>)}
      <text x="52" y="16">Observed sales · units / day</text><text x={x(56) + 8} y="16">28-day forecast</text><text x={x(84) + 8} y="16">Provisional tail</text>
      {segments(history.map((p, i) => p.status === 'observed' && p.observed_sales !== null ? `${x(i)},${y(p.observed_sales)}` : null)).map((s, i) => <polyline key={i} points={s.join(' ')} fill="none" stroke="#86958d" strokeWidth="2" />)}
      {history.map((p, i) => p.status === 'censored' && p.observed_sales !== null ? <circle key={p.day} cx={x(i)} cy={y(p.observed_sales)} r="3" fill="#a36722"><title>{p.day}: censored sales {number(p.observed_sales)}</title></circle> : null)}
      {segments(forecastPoints(0, 29)).map((s, i) => <polyline key={i} points={s.join(' ')} fill="none" stroke="#1b6853" strokeWidth="2.5"/>)}
      {segments(forecastPoints(28, 56)).map((s, i) => <polyline key={i} points={s.join(' ')} fill="none" stroke="#1b6853" strokeWidth="2" strokeDasharray="5 4"/>)}
      {[0, 28, 56, 84, 111].map(i => <text key={i} x={x(i)} y="225" textAnchor={i === 111 ? 'end' : 'middle'}>{shortDate(i < 56 ? history[i].day : result.forecast[i - 56].day)}</text>)}
    </svg>
    <div className="legend"><span><i className="dot observed"/>Observed sales</span><span><i className="dot forecast"/>Expected demand</span><span><i className="dot censored"/>Censored lower bound</span><span>Gaps = unknown or ineligible days</span></div>
  </div>;
}
