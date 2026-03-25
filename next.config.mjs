/** @type {import('next').NextConfig} */
const nextConfig = {
  typescript: {
    ignoreBuildErrors: true,
  },
  images: {
    unoptimized: true,
  },
  // Turbopack configuration (empty to silence warnings)
  turbopack: {},
  // Webpack fallback for compatibility
  webpack: (config) => {
    return config;
  },
}

export default nextConfig
