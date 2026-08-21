import sys
import os
import argparse
from pathlib import Path

# 处理 PyInstaller 打包后的路径与常规开发路径
if getattr(sys, 'frozen', False):
    app_dir = Path(sys._MEIPASS)
    # 确保当前执行目录在 sys.path
    if str(app_dir) not in sys.path:
        sys.path.insert(0, str(app_dir))
else:
    app_dir = Path(__file__).resolve().parent.parent
    if str(app_dir) not in sys.path:
        sys.path.insert(0, str(app_dir))

import uvicorn
from backend.app.config import settings

def main():
    parser = argparse.ArgumentParser(description="WellToken Price Dashboard Backend Server")
    parser.add_argument("--host", type=str, default=settings.SERVER_HOST, help="Server host")
    parser.add_argument("--port", type=int, default=settings.SERVER_PORT, help="Server port")
    parser.add_argument("--reload", action="store_true", help="Enable hot reload (dev only)")
    
    args = parser.parse_args()
    
    # 打包运行模式下禁用 reload
    is_frozen = getattr(sys, 'frozen', False)
    reload_mode = args.reload and not is_frozen

    print(f"Starting WellToken Backend on http://{args.host}:{args.port} (frozen={is_frozen})")
    
    uvicorn.run(
        "backend.app.main:app",
        host=args.host,
        port=args.port,
        reload=reload_mode,
        log_level="info"
    )

if __name__ == "__main__":
    main()
