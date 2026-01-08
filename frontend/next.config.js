// /** @type {import('next').NextConfig} */
// const nextConfig = {
//   env: {
//     NEXT_PUBLIC_BACKEND_URL: process.env.NEXT_PUBLIC_BACKEND_URL || 'https://iqoonaz4321-taskneon-app.hf.space',
//   },
// }

// module.exports = nextConfig






/** @type {import('next').NextConfig} */
const nextConfig = {
  env: {
    // Isay NEXT_PUBLIC_API_URL kar dein taake ye Vercel ki key se match kare
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL || 'https://iqoonaz4321-phase-3.hf.space',
  },
  typescript: {
    ignoreBuildErrors: true,
  },
  eslint: {
    ignoreDuringBuilds: true,
  },
}

export default nextConfig;