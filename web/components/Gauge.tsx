import { gaugeFill, passesLimit, percent } from "@/lib/format";

type Props = {
  label: string;
  value: number | null;
  limit: number;
};

export function Gauge({ label, value, limit }: Props) {
  const passes = passesLimit(value, limit);
  const description =
    value === null
      ? `${label} has no data`
      : `${label} is ${percent(value)}, the limit is ${percent(limit, 0)}`;

  return (
    <div className="gauge-cell">
      <div className="gauge-label">
        <span>{label}</span>
        <b>
          {value === null ? (
            <>no data <span style={{ fontWeight: 400 }}>(limit {percent(limit, 0)})</span></>
          ) : (
            <>{percent(value)} <span style={{ fontWeight: 400 }}>of {percent(limit, 0)} limit</span></>
          )}
        </b>
      </div>
      <div className="gauge" role="img" aria-label={description}>
        {value === null ? (
          <div className="gauge-fill gauge-missing" />
        ) : (
          <div
            className={`gauge-fill ${passes ? "gauge-pass" : "gauge-fail"}`}
            style={{ width: `${gaugeFill(value, limit) * 100}%` }}
          />
        )}
        <div className="gauge-limit" />
      </div>
    </div>
  );
}
