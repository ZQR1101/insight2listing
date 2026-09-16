import type { NextConfig } from "next";
import createNextIntlPlugin from "next-intl/plugin";

const withNextIntl = createNextIntlPlugin("./i18n/request.ts");

// Backend base URL used by the server-side API proxy. In production point this
// at the API service (e.g. http://api:8000); in dev it is the local uvicorn.
const API_URL = process.env.API_URL || "http://localhost:8000";

const nextConfig: NextConfig = {
  reactStrictMode: true,
  output: "standalone",
  async rewrites() {
    // Forward all backend calls through Next's server so the browser never
    // talks to the API cross-origin (no CORS needed) and keys stay server-side.
    return [
      {
        source: "/api/v1/:path*",
        destination: `${API_URL}/api/v1/:path*`,
      },
    ];
  },
};

export default withNextIntl(nextConfig);