'use client';

import React, { useEffect, useState } from 'react';
import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, CartesianGrid } from 'recharts';

export default function Dashboard() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetch('/api/review-intelligence')
      .then((res) => {
        if (!res.ok) throw new Error('Gagal mengambil data dari API');
        return res.json();
      })
      .then((data) => {
        setData(data);
        setLoading(false);
      })
      .catch((err) => {
        setError(err.message);
        setLoading(false);
      });
  }, []);

  if (loading) return <div className=\"p-8 text-center\">Memuat dashboard...</div>;
  if (error) return <div className=\"p-8 text-center text-red-500\">Error: {error}</div>;

  const sentimentData = [
    { name: 'Positif', count: data.sentimentCounts.positive },
    { name: 'Netral', count: data.sentimentCounts.neutral },
    { name: 'Negatif', count: data.sentimentCounts.negative },
  ];

  return (
    <main className=\"min-h-screen bg-gray-50 p-6 md:p-12\">
      <div className=\"max-w-6xl mx-auto space-y-8\">
        <header>
          <h1 className=\"text-3xl font-bold text-gray-900\">Review Intelligence Dashboard</h1>
          <p className=\"text-gray-600 mt-1\">Analisis sentimen ulasan restoran secara real-time</p>
        </header>

        {/* Ringkasan Statistik */}
        <div className=\"grid grid-cols-1 md:grid-cols-2 gap-6\">
          <div className=\"bg-white p-6 rounded-xl shadow-sm border border-gray-100\">
            <h3 className=\"text-sm font-medium text-gray-500\">Total Ulasan</h3>
            <p className=\"text-3xl font-bold text-gray-900 mt-2\">{data.totalReviews}</p>
          </div>
          <div className=\"bg-white p-6 rounded-xl shadow-sm border border-gray-100\">
            <h3 className=\"text-sm font-medium text-gray-500\">Rata-rata Rating</h3>
            <p className=\"text-3xl font-bold text-gray-900 mt-2\">
              {data.averageRating ? data.averageRating.toFixed(2) : 'N/A'} / 5.0
            </p>
          </div>
        </div>

        {/* Grafik Distribusi Sentimen */}
        <div className=\"bg-white p-6 rounded-xl shadow-sm border border-gray-100\">
          <h3 className=\"text-lg font-semibold text-gray-900 mb-4\">Distribusi Sentimen Ulasan</h3>
          <div className=\"h-72 w-full\">
            <ResponsiveContainer width=\"100%\" height=\"100%\">
              <BarChart data={sentimentData}>
                <CartesianGrid strokeDasharray=\"3 3\" />
                <XAxis dataKey=\"name\" />
                <YAxis />
                <Tooltip />
                <Bar dataKey=\"count\" fill=\"#2563eb\" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>
    </main>
  );
}
