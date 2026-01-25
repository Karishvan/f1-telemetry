export const formatLapTime = (ms) => {
  if (!ms) return "-";

  const totalSeconds = ms;
  const minutes = Math.floor(totalSeconds / 60);
  const seconds = Math.floor(totalSeconds % 60);
  const milliseconds = Math.floor((ms * 1000) % 1000);

  const paddedSeconds = String(seconds).padStart(2, "0");
  const paddedMs = String(milliseconds).padStart(3, "0");

  return `${minutes}:${paddedSeconds}.${paddedMs}`;
};
