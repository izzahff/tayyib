import { DEBT_LIMIT, INCOME_LIMIT } from "@/lib/constants";

export default function Methodology() {
  return (
    <>
      <h1 className="title">How a stock passes or fails</h1>
      <p className="lede">
        Tayyib applies a deliberately simplified version of AAOIFI Shariah Standard No. 21. The
        full standard uses three ratios measured against market capitalisation. Tayyib uses two
        ratios measured against total assets and revenue, because market capitalisation is
        unreliable on the free data plan this project runs on.
      </p>

      <div className="prose">
        <table className="ratio-table">
          <thead>
            <tr>
              <th>Ratio</th>
              <th>Formula</th>
              <th>Limit</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td>Debt to assets</td>
              <td>total liabilities divided by total assets</td>
              <td>{DEBT_LIMIT * 100}%</td>
            </tr>
            <tr>
              <td>Non-permissible income</td>
              <td>(interest income plus other non-operating income) divided by revenue</td>
              <td>{INCOME_LIMIT * 100}%</td>
            </tr>
          </tbody>
        </table>

        <h2>Three outcomes, never a guess</h2>
        <p>
          A stock is compliant, not compliant, or not screened. When a figure is missing, Tayyib
          marks the stock as not screened and says which figure was missing. It never turns a gap
          into a pass or a fail.
        </p>

        <h2>The boundary rule</h2>
        <p>A value exactly equal to the limit passes. Only a value above the limit fails.</p>

        <h2>Ranking</h2>
        <p>
          Compliant stocks are ranked by their return on dividend-adjusted closing price over the
          last 126 trading days. The top ten share the list equally. A stock with too little price
          history is left out and the reason is recorded.
        </p>

        <h2>No AI in the decision</h2>
        <p>
          The same input always gives the same output. Every verdict can be traced to the figures
          and the fixed reason strings that produced it.
        </p>

        <h2>Where the specs live</h2>
        <p>
          Each capability was specified before it was built, using OpenSpec. The specs and the
          review history are in the{" "}
          <a href="https://github.com/izzahff/tayyib/tree/main/openspec">project repository</a>.
        </p>
      </div>
    </>
  );
}
