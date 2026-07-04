/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  // Output standalone for minimal Docker images if ever needed.
  output: process.env.BUILD_STANDALONE === "1" ? "standalone" : undefined,
  // Image allowlist for future enhancement (logos, etc.)
  images: {
    remotePatterns: [],
  },
};

export default nextConfig;