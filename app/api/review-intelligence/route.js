import { createClient } from "@supabase/supabase-js";
import { NextResponse } from "next/server";

export const dynamic = "force-dynamic";

export async function GET() {
  try {
    const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL;
    const supabaseKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY;

    if (!supabaseUrl || !supabaseKey) {
      return NextResponse.json(
        { error: "Supabase environment variables are missing." },
        { status: 500 }
      );
    }

    const supabase = createClient(supabaseUrl, supabaseKey);

    // Menarik data dari view/tabel sesuai panduan
    const { data, error } = await supabase
      .from("review_intelligence_public")
      .select(
        "review_id, restaurant_name, review_text, stars, published_at, review_url, sentiment_label, sentiment_score, analyzed_at"
      )
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
    let ratingSum = 0;
    let ratingCount = 0;

    for (const review of reviews) {
      const label = String(review.sentiment_label ?? "").toLowerCase();
      if (label in sentimentCounts) sentimentCounts[label] += 1;

      const rating = Number(review.stars);
      if (Number.isFinite(rating)) {
        ratingSum += rating;
        ratingCount += 1;
      }
    }

    return NextResponse.json({
      totalReviews: reviews.length,
      averageRating: ratingCount ? ratingSum / ratingCount : null,
      sentimentCounts,
      reviews,
    });
  } catch (error) {
    console.error("Review Intelligence API error:", error);
    return NextResponse.json(
      { error: "Unexpected server error." },
      { status: 500 }
    );
  }
}
