import type { NextConfig } from "next";
import createNextIntlPlugin from "next-intl/plugin";

const withNextIntl = createNextIntlPlugin("./i18n/request.ts");

const nextConfig: NextConfig = {
  reactStrictMode: true,
  output: "standalone",
  // Backend calls use a runtime-configurable proxy (app/api/v1/[...path]/route.ts)
  // driven by the API_URL env var, so no build-time destination is baked here.
};

export default withNextIntl(nextConfig);