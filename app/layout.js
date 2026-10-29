import React from 'react';

export const metadata = {
  title: 'Review Intelligence Dashboard',
  description: 'Dashboard analisis sentimen ulasan restoran',
};

export default function RootLayout({ children }) {
  return (
    <html lang="id">
      <body>{children}</body>
    </html>
  );
}
