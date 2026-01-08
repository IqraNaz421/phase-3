import { createAuthClient } from 'better-auth/react';

// Initialize Better Auth client
export const authClient = createAuthClient({
  // baseURL: 'http://localhost:8000',
  baseURL: process.env.NEXT_PUBLIC_API_URL || 'https://iqoonaz4321-phase-3.hf.space',
  fetchOptions: {
    credentials: 'include', // Include cookies in requests
  }
});






// import { createAuthClient } from 'better-auth/react';

// export const authClient = createAuthClient({
//   baseURL: 'https://iqoonaz4321-taskneon-app.hf.space',
//   fetchOptions: {
//     credentials: 'include',
//   },
//   // --- YE ADD KAREIN ---
//   cookieOptions: {
//     sideEffect: true, // Frontend par session update karne ke liye
//     domain: ".vercel.app", // Ya apni specific domain
//     secure: true,
//     sameSite: "none", // Cross-site cookies ke liye ye "none" hona lazmi hai
//   }
// });

// export default authClient;