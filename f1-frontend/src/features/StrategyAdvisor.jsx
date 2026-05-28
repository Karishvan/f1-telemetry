import { TIRE_COLORS } from "../utils/constants";

const TIRE_ABBREV = {
  SOFT: "S",
  MEDIUM: "M",
  HARD: "H",
  INTERMEDIATE: "I",
  WET: "W",
};

const StintTimeline = ({ stints, totalLaps }) => (
  <div>
    <div className="flex w-full h-9 rounded-lg overflow-hidden gap-px">
      {stints.map((s, i) => (
        <div
          key={i}
          style={{
            width: `${(s.laps / totalLaps) * 100}%`,
            backgroundColor: TIRE_COLORS[s.compound] ?? "#6b7280",
          }}
          className="flex items-center justify-center text-xs font-black text-black min-w-0 overflow-hidden"
          title={`${s.compound}: Laps ${s.start_lap}–${s.end_lap} (${s.laps} laps)`}
        >
          <span className="truncate px-1">{TIRE_ABBREV[s.compound] ?? s.compound[0]}</span>
        </div>
      ))}
    </div>
    <div className="flex w-full mt-1 relative h-4">
      <span className="text-[10px] text-gray-500 absolute left-0">L1</span>
      {stints.slice(0, -1).map((s, i) => (
        <span
          key={i}
          className="text-[10px] text-red-400 font-bold absolute"
          style={{
            left: `${(s.end_lap / totalLaps) * 100}%`,
            transform: "translateX(-50%)",
          }}
        >
          L{s.end_lap}
        </span>
      ))}
      <span className="text-[10px] text-gray-500 absolute right-0">L{totalLaps}</span>
    </div>
  </div>
);

const StintDetails = ({ stints }) => (
  <div className="mt-3 flex flex-wrap gap-3">
    {stints.map((s, i) => (
      <span key={i} className="text-xs text-gray-300">
        <span className="font-bold" style={{ color: TIRE_COLORS[s.compound] }}>
          {s.compound}
        </span>{" "}
        L{s.start_lap}–L{s.end_lap} ({s.laps} laps)
      </span>
    ))}
  </div>
);

const PitLabels = ({ pitLaps }) =>
  pitLaps.length > 0 ? (
    <div className="mt-2 flex flex-wrap gap-2">
      {pitLaps.map((lap, i) => (
        <span
          key={i}
          className="text-xs bg-red-900/60 text-red-300 px-2 py-0.5 rounded"
        >
          BOX Lap {lap}
        </span>
      ))}
    </div>
  ) : null;

const StrategyAdvisor = ({ data }) => {
  if (!data) return null;

  const { total_laps, actual_strategy, recommended_strategies, compounds_analyzed } =
    data;

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap gap-2 items-center">
        {compounds_analyzed.map((c) => (
          <span
            key={c}
            className="text-xs px-2 py-1 rounded font-semibold text-black"
            style={{ backgroundColor: TIRE_COLORS[c] ?? "#6b7280" }}
          >
            {c}
          </span>
        ))}
        <span className="text-xs text-gray-500 ml-1">
          {total_laps} laps · 22s pit loss assumed
        </span>
      </div>

      {/* Actual strategy */}
      <div className="bg-gray-800 rounded-xl p-4">
        <div className="flex items-center justify-between mb-3">
          <h3 className="text-sm font-semibold text-gray-300">Actual Strategy</h3>
          <span className="text-xs text-gray-500">
            {actual_strategy.num_pit_stops} pit stop
            {actual_strategy.num_pit_stops !== 1 ? "s" : ""}
          </span>
        </div>
        <StintTimeline stints={actual_strategy.stints} totalLaps={total_laps} />
        <StintDetails stints={actual_strategy.stints} />
        <PitLabels pitLaps={actual_strategy.pit_stop_laps} />
      </div>

      {/* Recommended strategies */}
      <div>
        <h3 className="text-sm font-semibold text-gray-400 uppercase mb-3">
          Optimal Strategies
        </h3>

        {recommended_strategies.length === 0 ? (
          <div className="flex h-32 items-center justify-center border-2 border-dashed border-gray-700 rounded-xl">
            <p className="text-gray-500 text-sm">
              No alternative strategies found with available data.
            </p>
          </div>
        ) : (
          <div className="space-y-3">
            {recommended_strategies.map((strat, i) => (
              <div
                key={i}
                className={`rounded-xl p-4 border ${
                  strat.delta_s < 0
                    ? "bg-green-950 border-green-700"
                    : "bg-gray-800 border-gray-700"
                }`}
              >
                <div className="flex items-center justify-between mb-3">
                  <div className="flex items-center gap-3">
                    <span className="text-sm font-semibold text-white">
                      {i === 0 && strat.delta_s < 0 ? (
                        <span className="text-xs bg-green-700 text-white px-2 py-0.5 rounded mr-2">
                          BEST
                        </span>
                      ) : null}
                      #{i + 1}
                    </span>
                    <span className="text-xs text-gray-400">
                      {strat.num_pit_stops} stop
                      {strat.num_pit_stops !== 1 ? "s" : ""}
                    </span>
                  </div>
                  <span
                    className={`text-sm font-bold ${
                      strat.delta_s < 0
                        ? "text-green-400"
                        : strat.delta_s === 0
                        ? "text-gray-400"
                        : "text-red-400"
                    }`}
                  >
                    {strat.delta_s < 0
                      ? `${Math.abs(strat.delta_s)}s faster`
                      : strat.delta_s === 0
                      ? "Same pace"
                      : `${strat.delta_s}s slower`}
                  </span>
                </div>
                <StintTimeline stints={strat.stints} totalLaps={total_laps} />
                <StintDetails stints={strat.stints} />
                <PitLabels pitLaps={strat.pit_stop_laps} />
              </div>
            ))}
          </div>
        )}
      </div>

      <p className="text-xs text-gray-600">
        Estimates based on tire degradation model. Actual performance may vary.
      </p>
    </div>
  );
};

export default StrategyAdvisor;
