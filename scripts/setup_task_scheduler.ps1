<#
.SYNOPSIS
    fx-metal-report의 run_report.py를 Windows 작업 스케줄러에 "평일(월~금)"마다 자동 실행되도록 등록합니다.

.DESCRIPTION
    등록 전 venv의 python.exe와 run_report.py가 실제로 존재하는지 확인하고,
    사용자에게 y/N 확인을 받은 뒤에만 schtasks /Create를 실행합니다.
    이미 같은 이름의 작업이 있으면 덮어씁니다(/F).

.PARAMETER Time
    매일 실행할 시각 (HH:mm, 기본 08:30)

.EXAMPLE
    .\scripts\setup_task_scheduler.ps1
    .\scripts\setup_task_scheduler.ps1 -Time "07:30"
#>
param(
    [string]$Time = "08:30"
)

$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent $PSScriptRoot
$PythonExe = Join-Path $ProjectRoot "venv\Scripts\python.exe"
$ReportScript = Join-Path $ProjectRoot "run_report.py"
$TaskName = "FxMetalReport_DailyEmail"

if (-not (Test-Path $PythonExe)) {
    Write-Error "venv python.exe를 찾을 수 없습니다: $PythonExe`n먼저 'python -m venv venv'와 'pip install -r requirements.txt'를 실행하세요."
    exit 1
}
if (-not (Test-Path $ReportScript)) {
    Write-Error "run_report.py를 찾을 수 없습니다: $ReportScript"
    exit 1
}

Write-Host "다음 작업을 Windows 작업 스케줄러에 등록합니다:"
Write-Host "  작업 이름: $TaskName"
Write-Host "  실행 시각: 매주 월~금 $Time"
Write-Host "  실행 명령: `"$PythonExe`" `"$ReportScript`""
Write-Host ""
$confirm = Read-Host "등록하시겠습니까? (y/N)"
if ($confirm -ne "y" -and $confirm -ne "Y") {
    Write-Host "취소되었습니다."
    exit 0
}

schtasks /Create /F /SC WEEKLY /D MON,TUE,WED,THU,FRI /ST $Time `
    /TN $TaskName `
    /TR "`"$PythonExe`" `"$ReportScript`"" `
    /RL LIMITED

Write-Host ""
Write-Host "등록 완료. 확인: schtasks /Query /TN `"$TaskName`""
Write-Host "삭제:     schtasks /Delete /TN `"$TaskName`" /F"
Write-Host ""
Write-Host "참고: PC가 절전 모드일 때는 예약 실행이 스킵됩니다. 절전 시에도 깨워서 실행하려면"
Write-Host "      작업 스케줄러(taskschd.msc) GUI에서 해당 작업 속성 > 조건 탭에서"
Write-Host "      '이 작업을 실행하기 위해 절전 모드를 해제'를 직접 체크하세요."
