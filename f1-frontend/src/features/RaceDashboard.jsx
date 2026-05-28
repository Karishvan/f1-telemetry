import React, { useState, useEffect } from "react";
import api from "../services/api";
import LapChart from "./LapChart";
import StrategyAdvisor from "./StrategyAdvisor";

const TABS = [
  { id: "chart", label: "Lap Chart" },
  { id: "strategy", label: "Strategy Advisor" },
];

const RaceDashboard = () => {
  const [year, setYear] = useState("");
  const [gp, setGp] = useState("");
  const [driver, setDriver] = useState("");
  const [activeTab, setActiveTab] = useState("chart");

  const [lapData, setLapData] = useState([]);
  const [strategyData, setStrategyData] = useState(null);
  const [loading, setLoading] = useState(false);

  const [years, setAvailableYears] = useState([]);
  const [gps, setAvailableGps] = useState([]);
  const [drivers, setAvailableDrivers] = useState([]);

  useEffect(() => {
    const fetchMetadata = async () => {
      try {
        const [gpRes, driverRes, yearRes] = await Promise.all([
          api.get("/lap/grand_prixs"),
          api.get("/lap/drivers"),
          api.get("/lap/years"),
        ]);
        setAvailableGps(gpRes.data);
        setAvailableDrivers(driverRes.data);
        setAvailableYears(yearRes.data);
        setYear(yearRes.data[0]);
        setGp(gpRes.data[0]);
        setDriver(driverRes.data[0]);
      } catch (err) {
        console.error("Failed to load metadata", err);
      }
    };
    fetchMetadata();
  }, []);

  // Reset strategy cache when selection changes
  useEffect(() => {
    setStrategyData(null);
  }, [year, gp, driver]);

  useEffect(() => {
    if (!year || !gp || !driver || activeTab !== "chart") return;
    const fetchData = async () => {
      setLoading(true);
      try {
        const response = await api.get("/analytics/lap-chart/", {
          params: { year, grand_prix: gp, driver },
        });
        setLapData(response.data);
      } catch (error) {
        console.error("Error fetching lap data:", error);
        setLapData([]);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, [year, gp, driver, activeTab]);

  useEffect(() => {
    if (!year || !gp || !driver || activeTab !== "strategy") return;
    if (strategyData !== null) return;
    const fetchStrategy = async () => {
      setLoading(true);
      try {
        const response = await api.get("/analytics/strategy", {
          params: { year, grand_prix: gp, driver },
        });
        setStrategyData(response.data);
      } catch (error) {
        console.error("Error fetching strategy:", error);
        setStrategyData(null);
      } finally {
        setLoading(false);
      }
    };
    fetchStrategy();
  }, [year, gp, driver, activeTab, strategyData]);

  return (
    <div className="p-8 bg-gray-900 min-h-screen text-white">
      <header className="mb-6">
        <h1 className="text-3xl font-bold mb-6">F1 Strategy Analytics</h1>

        <div className="flex flex-wrap gap-4 bg-gray-800 p-4 rounded-lg shadow-md mb-4">
          <div className="flex flex-col">
            <label className="text-xs text-gray-400 mb-1 ml-1">Season</label>
            <select
              value={year}
              onChange={(e) => setYear(e.target.value)}
              className="bg-gray-700 border border-gray-600 rounded px-3 py-2 focus:outline-none focus:ring-2 focus:ring-red-500"
            >
              {years.map((y) => (
                <option key={y} value={y}>
                  {y}
                </option>
              ))}
            </select>
          </div>

          <div className="flex flex-col">
            <label className="text-xs text-gray-400 mb-1 ml-1">Grand Prix</label>
            <select
              value={gp}
              onChange={(e) => setGp(e.target.value)}
              className="bg-gray-700 border border-gray-600 rounded px-3 py-2 focus:outline-none focus:ring-2 focus:ring-red-500"
            >
              {gps.map((g) => (
                <option key={g} value={g}>
                  {g}
                </option>
              ))}
            </select>
          </div>

          <div className="flex flex-col">
            <label className="text-xs text-gray-400 mb-1 ml-1">Driver</label>
            <select
              value={driver}
              onChange={(e) => setDriver(e.target.value)}
              className="bg-gray-700 border border-gray-600 rounded px-3 py-2 focus:outline-none focus:ring-2 focus:ring-red-500"
            >
              {drivers.map((d) => (
                <option key={d} value={d}>
                  {d}
                </option>
              ))}
            </select>
          </div>
        </div>

        <div className="flex gap-1 border-b border-gray-700">
          {TABS.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`px-4 py-2 text-sm font-medium transition-colors ${
                activeTab === tab.id
                  ? "text-white border-b-2 border-red-500"
                  : "text-gray-400 hover:text-gray-200"
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>
      </header>

      <main className="relative">
        {loading && (
          <div className="absolute inset-0 flex items-center justify-center bg-gray-900 bg-opacity-50 z-10">
            <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-red-500"></div>
          </div>
        )}

        <div
          className={`${loading ? "opacity-30" : "opacity-100"} transition-opacity duration-300`}
        >
          {activeTab === "chart" &&
            (lapData.length > 0 ? (
              <LapChart data={lapData} driver={driver} />
            ) : (
              <div className="flex h-64 items-center justify-center border-2 border-dashed border-gray-700 rounded-xl">
                <p className="text-gray-500">
                  No telemetry data available for this selection.
                </p>
              </div>
            ))}

          {activeTab === "strategy" &&
            (strategyData ? (
              <StrategyAdvisor data={strategyData} />
            ) : (
              <div className="flex h-64 items-center justify-center border-2 border-dashed border-gray-700 rounded-xl">
                <p className="text-gray-500">
                  {loading
                    ? "Computing strategy..."
                    : "No strategy data available for this selection."}
                </p>
              </div>
            ))}
        </div>
      </main>
    </div>
  );
};

export default RaceDashboard;
