from fastapi import APIRouter
from datetime import datetime, timezone, timedelta
from database import prediction_collection

router = APIRouter(prefix="/stats", tags=["Statistics"])

CRITICAL_DISEASES = {
    "Late_blight",
    "Tomato_Yellow_Leaf_Curl_Virus",
}


def serialize_scan(scan: dict) -> dict:
    """Convert MongoDB document to JSON-serializable dict."""
    scan["_id"] = str(scan["_id"])
    if "timestamp" in scan:
        scan["timestamp"] = scan["timestamp"].isoformat()
    return scan


@router.get("/dashboard")
async def get_dashboard_stats():
    """
    Full dashboard statistics:
    - total scans, today, this week
    - healthy vs diseased counts and percentages
    - critical disease count
    - most common disease
    - disease breakdown with percentages
    - 7-day scan trend
    """
    now         = datetime.now(timezone.utc)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    week_start  = now - timedelta(days=6)

    total_scans = prediction_collection.count_documents({})


    if total_scans == 0:
        return {
            "total_scans"    : 0,
            "today_scans"    : 0,
            "weekly_scans"   : 0,
            "healthy_count"  : 0,
            "diseased_count" : 0,
            "healthy_pct"    : 0,
            "diseased_pct"   : 0,
            "critical_count" : 0,
            "most_common"    : None,
            "disease_counts" : [],
            "weekly_trend"   : _empty_weekly_trend(now),
        }


    today_scans  = prediction_collection.count_documents({"timestamp": {"$gte": today_start}})
    weekly_scans = prediction_collection.count_documents({"timestamp": {"$gte": week_start}})
    critical_count = prediction_collection.count_documents({
        "prediction": {"$in": list(CRITICAL_DISEASES)}
    })

    #
    disease_raw = list(prediction_collection.aggregate([
        {"$group": {"_id": "$prediction", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
    ]))

    disease_counts = [
        {
            "disease"    : d["_id"],
            "count"      : d["count"],
            "percentage" : round((d["count"] / total_scans) * 100, 1),
            "is_critical": d["_id"] in CRITICAL_DISEASES,
        }
        for d in disease_raw
    ]


    healthy_count  = next((d["count"] for d in disease_raw if d["_id"] == "Healthy"), 0)
    diseased_count = total_scans - healthy_count

    
    trend_raw = list(prediction_collection.aggregate([
        {"$match": {"timestamp": {"$gte": week_start}}},
        {
            "$group": {
                "_id": {
                    "year" : {"$year"       : "$timestamp"},
                    "month": {"$month"      : "$timestamp"},
                    "day"  : {"$dayOfMonth" : "$timestamp"},
                },
                "count": {"$sum": 1},
            }
        },
        {"$sort": {"_id.year": 1, "_id.month": 1, "_id.day": 1}},
    ]))

    trend_map = {
        f"{t['_id']['year']}-{t['_id']['month']:02d}-{t['_id']['day']:02d}": t["count"]
        for t in trend_raw
    }

    weekly_trend = [
        {
            "date"  : (now - timedelta(days=i)).strftime("%Y-%m-%d"),
            "label" : (now - timedelta(days=i)).strftime("%a"),
            "count" : trend_map.get((now - timedelta(days=i)).strftime("%Y-%m-%d"), 0),
        }
        for i in range(6, -1, -1)
    ]

    return {
        "total_scans"    : total_scans,
        "today_scans"    : today_scans,
        "weekly_scans"   : weekly_scans,
        "healthy_count"  : healthy_count,
        "diseased_count" : diseased_count,
        "healthy_pct"    : round((healthy_count  / total_scans) * 100, 1),
        "diseased_pct"   : round((diseased_count / total_scans) * 100, 1),
        "critical_count" : critical_count,
        "most_common"    : disease_raw[0]["_id"] if disease_raw else None,
        "disease_counts" : disease_counts,
        "weekly_trend"   : weekly_trend,
    }


@router.get("/recent")
async def get_recent_scans(limit: int = 10):
    """Returns the most recent N predictions."""
    scans = list(
        prediction_collection
        .find({}, {"image_path": 0})
        .sort("timestamp", -1)
        .limit(limit)
    )
    return {"scans": [serialize_scan(s) for s in scans], "count": len(scans)}


@router.get("/trend")
async def get_disease_trend():
    """
    Compares this week vs last week per disease.
    Shows which diseases are rising, falling or stable.
    """
    now       = datetime.now(timezone.utc)
    this_week = now - timedelta(days=7)
    last_week = now - timedelta(days=14)

    def get_counts(start, end):
        pipeline = [
            {"$match": {"timestamp": {"$gte": start, "$lt": end}}},
            {"$group": {"_id": "$prediction", "count": {"$sum": 1}}},
        ]
        return {r["_id"]: r["count"] for r in prediction_collection.aggregate(pipeline)}

    this_counts = get_counts(this_week, now)
    last_counts = get_counts(last_week, this_week)
    all_diseases = set(this_counts) | set(last_counts)

    trends = []
    for disease in all_diseases:
        this  = this_counts.get(disease, 0)
        last  = last_counts.get(disease, 0)
        delta = this - last

        change_pct = (
            100 if last == 0 and this > 0
            else 0 if last == 0
            else round(((this - last) / last) * 100, 1)
        )

        trends.append({
            "disease"    : disease,
            "this_week"  : this,
            "last_week"  : last,
            "delta"      : delta,
            "change_pct" : change_pct,
            "direction"  : "up" if delta > 0 else "down" if delta < 0 else "stable",
            "is_critical": disease in CRITICAL_DISEASES,
        })

    trends.sort(key=lambda x: abs(x["delta"]), reverse=True)
    return {"trends": trends}


@router.get("/summary")
async def get_summary():
    """
    Lightweight summary for quick status cards.
    Faster than /dashboard — only fetches counts, no aggregation pipeline.
    """
    now         = datetime.now(timezone.utc)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    week_start  = now - timedelta(days=7)

    total   = prediction_collection.count_documents({})
    today   = prediction_collection.count_documents({"timestamp": {"$gte": today_start}})
    weekly  = prediction_collection.count_documents({"timestamp": {"$gte": week_start}})
    healthy = prediction_collection.count_documents({"prediction": "Healthy"})
    critical = prediction_collection.count_documents({
        "prediction": {"$in": list(CRITICAL_DISEASES)}
    })

    return {
        "total"         : total,
        "today"         : today,
        "this_week"     : weekly,
        "healthy"       : healthy,
        "diseased"      : total - healthy,
        "critical"      : critical,
    }



def _empty_weekly_trend(now: datetime) -> list:
    """Returns 7 days of zero counts when there is no data yet."""
    return [
        {
            "date"  : (now - timedelta(days=i)).strftime("%Y-%m-%d"),
            "label" : (now - timedelta(days=i)).strftime("%a"),
            "count" : 0,
        }
        for i in range(6, -1, -1)
    ]