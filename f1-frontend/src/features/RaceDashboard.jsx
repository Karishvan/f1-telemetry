import React, { useState, useEffect } from "react";
import api from "../services/api";
import LapChart from "./LapChart";

const RaceDashboard = () => {
  const [year, setYear] = useState("");
  const [gp, setGp] = useState("");
  const [driver, setDriver] = useState("");

  const [lapData, setLapData] = useState([]);
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

  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      try {
        const encodedGP = encodeURIComponent(gp);
        const response = await api.get(
          `/analytics/lap-chart/${year}/${encodedGP}/${driver}`,
        );
        setLapData(response.data);
      } catch (error) {
        console.error("Error fetching F1 data:", error);
        setLapData([]);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [year, gp, driver]);

  return (
    <div className="p-8 bg-gray-900 min-h-screen text-white">
      <header className="mb-8">
        <h1 className="text-3xl font-bold mb-6">F1 Strategy Analytics</h1>

        <div className="flex flex-wrap gap-4 bg-gray-800 p-4 rounded-lg shadow-md">
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
            <label className="text-xs text-gray-400 mb-1 ml-1">
              Grand Prix
            </label>
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
          {lapData.length > 0 ? (
            <LapChart data={lapData} driver={driver} />
          ) : (
            <div className="flex h-64 items-center justify-center border-2 border-dashed border-gray-700 rounded-xl">
              <p className="text-gray-500">
                No telemetry data available for this selection.
              </p>
            </div>
          )}
        </div>
      </main>
    </div>
  );
};

export default RaceDashboard;
