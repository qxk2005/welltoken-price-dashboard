#!/usr/bin/env python3
"""
导出官方快照元数据种子与全量多版本定价模型种子
"""
import sys
import os
import json
import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "data" / "welltoken.db"
SNAPSHOTS_SEED_PATH = BASE_DIR / "data" / "official_snapshots_seed.json"
PRICES_SEED_PATH = BASE_DIR / "data" / "official_prices_seed.json"

def export_seeds():
    if not DB_PATH.exists():
        print(f"Error: {DB_PATH} not found!")
        sys.exit(1)

    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    # 1. 导出快照表
    c.execute("""
        SELECT id, provider, source_url, page_title, local_file_path, file_size_bytes, models_count, captured_at
        FROM official_snapshots
        ORDER BY captured_at ASC, id ASC
    """)
    snapshots = [dict(r) for r in c.fetchall()]
    print(f"Exporting {len(snapshots)} snapshots...")

    # 对 local_file_path 统一为相对路径格式 "data/official_snapshots/xxx.html"
    for s in snapshots:
        raw_p = Path(s["local_file_path"])
        s["local_file_path"] = f"data/official_snapshots/{raw_p.name}"

    with open(SNAPSHOTS_SEED_PATH, "w", encoding="utf-8") as f:
        json.dump(snapshots, f, ensure_ascii=False, indent=2)
    print(f"Saved snapshots seed to {SNAPSHOTS_SEED_PATH}")

    # 2. 导出所有官方模型价格（含 is_current=1 与 is_current=0 的所有有效规格）
    c.execute("""
        SELECT 
            p.provider, p.provider_name, p.series, p.model_name, p.raw_model_id,
            p.billing_mode, p.tier_range, p.currency, p.input_price, p.output_price,
            p.cache_read_price, p.cache_write_price, p.remarks, p.custom_notes,
            p.user_tags, p.price_date, p.source_page_url, p.source_anchor,
            p.is_current, p.is_active, p.snapshot_id,
            s.provider as snap_provider, s.captured_at as snap_captured_at
        FROM official_model_prices p
        LEFT JOIN official_snapshots s ON p.snapshot_id = s.id
        ORDER BY p.is_current DESC, p.provider ASC, p.model_name ASC
    """)
    prices = [dict(r) for r in c.fetchall()]
    print(f"Exporting {len(prices)} model prices...")

    # 格式化模型，包含快照关联的外部引用键（snap_provider 与 snap_captured_at）
    clean_prices = []
    for p in prices:
        snap_ref = None
        if p["snap_provider"] and p["snap_captured_at"]:
            snap_ref = {
                "provider": p["snap_provider"],
                "captured_at": str(p["snap_captured_at"])
            }
        
        item = {
            "provider": p["provider"],
            "provider_name": p["provider_name"],
            "series": p["series"],
            "model_name": p["model_name"],
            "raw_model_id": p["raw_model_id"],
            "billing_mode": p["billing_mode"],
            "tier_range": p["tier_range"],
            "currency": p["currency"],
            "input_price": p["input_price"],
            "output_price": p["output_price"],
            "cache_read_price": p["cache_read_price"],
            "cache_write_price": p["cache_write_price"],
            "remarks": p["remarks"],
            "custom_notes": p["custom_notes"],
            "user_tags": p["user_tags"],
            "price_date": p["price_date"],
            "source_page_url": p["source_page_url"],
            "source_anchor": p["source_anchor"],
            "is_current": bool(p["is_current"]),
            "is_active": bool(p["is_active"]),
            "snapshot_ref": snap_ref
        }
        clean_prices.append(item)

    with open(PRICES_SEED_PATH, "w", encoding="utf-8") as f:
        json.dump(clean_prices, f, ensure_ascii=False, indent=2)
    print(f"Saved model prices seed to {PRICES_SEED_PATH}")

if __name__ == "__main__":
    export_seeds()
