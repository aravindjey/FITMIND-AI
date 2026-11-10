/** @type {import('next').NextConfig} */
const nextConfig = (phase) => ({
  reactStrictMode: true,
  distDir: phase === 'phase-development-server' ? '.next' : '.next-build',
});

export default nextConfig;
