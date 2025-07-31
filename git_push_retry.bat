@echo off
setlocal enabledelayedexpansion

rem 设置最大重试次数
set max_retries=10
rem 设置每次重试间隔（秒）
set retry_interval=5
rem 设置当前重试次数
set current_retry=0

:retry
cls
echo 正在尝试推送代码（第 !current_retry! 次尝试）...
git push

rem 检查命令执行结果
if %ERRORLEVEL% EQU 0 (
    echo 推送成功！
    pause
    exit /b 0
) else (
    echo 推送失败，!retry_interval! 秒后重试...
    timeout /t !retry_interval! /nobreak >nul
    set /a current_retry+=1
    if !current_retry! LSS !max_retries! (
        goto retry
    ) else (
        echo 已达到最大重试次数（!max_retries!），推送失败。
        pause
        exit /b 1
    )
)