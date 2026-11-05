from fastapi import FastAPI, HTTPException
from garminconnect import Garmin

app = FastAPI()

GARMIN_EMAIL = "on-the-move@krd.biglobe.ne.jp"
GARMIN_PASSWORD = "Haruto2700"

# ログイン済みクライアントを保持するグローバル変数
_garmin_client = None

def get_garmin_client():
    global _garmin_client
    if _garmin_client is None:
        try:
            client = Garmin(GARMIN_EMAIL, GARMIN_PASSWORD)
            client.login()
            _garmin_client = client
        except Exception as e:
            raise RuntimeError(f"Garminログイン失敗: {e}")
    return _garmin_client

@app.get("/garmin/recent-activities")
def get_recent_activities(limit: int = 5):
    global _garmin_client
    try:
        client = get_garmin_client()
        
        # 直近のアクティビティを取得
        activities = client.get_activities(0, limit)
        
        result = []
        for act in activities:
            result.append({
                "activityId": act.get("activityId"),
                "name": act.get("activityName"),
                "startTime": act.get("startTimeLocal"),
                "distance_km": round(act.get("distance", 0) / 1000, 2),
                "duration_min": round(act.get("duration", 0) / 60, 1),
                "averageHeartRate": act.get("averageHR"),
                "calories": act.get("calories")
            })
        return {"status": "success", "data": result}
        
    except Exception as e:
        # セッション切れなどの場合は一度クライアントを破棄して再試行できるようにする
        _garmin_client = None
        raise HTTPException(status_code=500, detail=str(e))

# 【追記】特定のアクティビティ詳細（ラップや1kmごとのスプリット等）を取得するエンドポイント
@app.get("/garmin/activity-details/{activity_id}")
def get_activity_details(activity_id: str):
    global _garmin_client
    try:
        client = get_garmin_client()
        
        # garminconnect ライブラリを使用してラップ・スプリットデータを取得
        splits = client.get_activity_splits(activity_id)
        return {"status": "success", "data": splits}
        
    except Exception as e:
        # セッション切れなどの場合は一度クライアントを破棄
        _garmin_client = None
        raise HTTPException(status_code=500, detail=str(e))