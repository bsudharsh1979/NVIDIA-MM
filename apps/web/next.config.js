/** @type {import('next').NextConfig} */
const apiBase = process.env.NEXT_PUBLIC_API_BASE || process.env.API_PROXY_URL || "http://127.0.0.1:8000";
const nextConfig = {
  output: "standalone",
  env: {
    NEXT_PUBLIC_API_BASE: process.env.NEXT_PUBLIC_API_BASE || "",
  },
  async rewrites() {
    return [
      { source: "/api/:path*", destination: `${apiBase.replace(/\/$/, "")}/api/:path*` },
      { source: "/health", destination: `${apiBase.replace(/\/$/, "")}/health` },
    ];
  },
};
module.exports = nextConfig;
