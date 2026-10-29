import { NextResponse } from 'next/server';
import { createClient } from '@supabase/supabase-js';

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL;
const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY;

export async function GET() {
  if (!supabaseUrl || !supabaseAnonKey) {
    return NextResponse.json(
      { error: "Supabase environment variables are missing." },
      { status: 500 }
    );
  }

  const supabase = createClient(supabaseUrl, supabaseAnonKey);

  try {
    const { data, error } = await supabase
      .from("review_intelligence_public")
      .select("review_id, restaurant_name, review_text, stars, published_at, review_url, sentiment_label, sentiment_score, analyzed_at")
      .order("published_at", { ascending: false })
      .limit(500);

    if (error) {
      console.error("Supabase query failed:", error.message);
      return NextResponse.json(
        { error: "Failed to load review data." },
        { status: 500 }
      );
    }

    const reviews = data ?? [];
    const sentimentCounts = { positive: 0, neutral: 0, negative: 0 };
    let ratingsSum = 0;
    let ratingCount = 0;

    for (const review of reviews) {
      const label = String(review.sentiment_label ?? "").toLowerCase();
      if (label in sentimentCounts) sentimentCounts[label] += 1;

      const rating = Number(review.stars);
      if (Number.isFinite(rating)) {
        ratingsSum += rating;
        ratingCount += 1;
      }
    }

    const averageRating = ratingCount > 0 ? ratingsSum / ratingCount : 0;

    return NextResponse.json({
      totalReviews: reviews.length,
      averageRating,
      sentimentCounts,
      reviews,
    });
  } catch (err) {
    console.error("API error:", err);
    return NextResponse.json(
      { error: "Internal server error." },
      { status: 500 }
    );
  }
}
