/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  swcMinify: true,
  // Configure environment variables
  env: {
    // Add any environment variables here if needed
  },
  // Configure the server to run on port 3050
  serverOptions: {
    port: 3050,
  },
};

module.exports = nextConfig;
