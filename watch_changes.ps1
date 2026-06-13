# watch_changes.ps1
# 파일 변경 사항을 감시하여 변경 발생 시 자동으로 git add 및 git commit을 수행합니다.
# 커밋 직후에는 .git/hooks/post-commit 훅이 자동으로 실행되어 원격 저장소에 push합니다.

Write-Host "=== Git 자동 커밋 및 푸시 감시 도구 시작됨 ===" -ForegroundColor Green
Write-Host "감시 경로: $PSScriptRoot"
Write-Host "프로그램을 종료하려면 Ctrl+C를 누르세요."

# 감시 주기 (초)
$Interval = 5

while ($true) {
    # git status --porcelain 명령으로 스테이징되지 않았거나 새로 추가된 변경사항 확인
    $status = git status --porcelain
    
    if ($status) {
        Write-Host ""
        $currentTime = Get-Date -Format "HH:mm:ss"
        Write-Host "[$currentTime] 변경사항 감지!" -ForegroundColor Yellow
        Write-Host $status
        
        Write-Host "1. 변경사항 스테이징 중 (git add .)..."
        git add .
        
        # 커밋 메시지 구성
        $commitMessage = "auto: 파일 변경 자동 커밋 ($currentTime)"
        Write-Host "2. 자동 커밋 실행 중 (git commit)..."
        git commit -m $commitMessage
        
        # git commit 실행 시 .git/hooks/post-commit 훅이 자동으로 트리거되어 push를 처리합니다.
    }
    
    Start-Sleep -Seconds $Interval
}
