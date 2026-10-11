@echo off
chcp 65001 >nul
REM 关键修复：无论如何先切到本脚本所在目录，避免双击时 cwd 不在仓库里
cd /d "%~dp0"

REM 推送失败不要卡在密码提示，直接报错退出
set GIT_TERMINAL_PROMPT=0

REM ============================================================
REM 麦麦省钱助手 - 一键发布到 GitHub（公开仓库）
REM 用法：双击本文件，按提示输入 GitHub 用户名和 Token。
REM Token 获取：GitHub -> Settings -> Developer settings ->
REM   Personal access tokens -> Fine-grained（勾 public_repo）
REM   或 classic token（勾 repo 全部权限）。
REM Token 即登录凭证，无需另外浏览器登录。
REM ============================================================

echo 当前目录: %cd%
echo.

set /p USER=请输入你的 GitHub 用户名: 
set /p TOKEN=请输入 GitHub Personal Access Token: 
echo.

REM 0) 校验是否在 git 仓库内
git rev-parse --is-inside-work-tree >nul 2>&1
if errorlevel 1 (
  echo [错误] 当前目录不是 git 仓库，脚本未正确定位到 mcoder-mcsaver 文件夹。
  echo 请确认本 .bat 与项目文件在同一目录后重试。
  pause
  exit /b 1
)

REM 1) 用 API 创建公开仓库（已存在会返回 422，可忽略，继续推送即可）
echo [1/3] 正在创建公开仓库 mcoder-mcsaver ...
curl -s -o nul -X POST ^
  -H "Authorization: token %TOKEN%" ^
  -H "Content-Type: application/json" ^
  -d "{\"name\":\"mcoder-mcsaver\",\"description\":\"2026麦当劳程序员创意开发大赛参赛作品 - 麦麦省钱助手 McSaver\",\"public\":true}" ^
  https://api.github.com/user/repos
echo.

REM 2) 关联远程并推送
echo [2/3] 关联远程并推送 main 分支 ...
git remote remove origin 2>nul
git remote add origin https://%USER%:%TOKEN%@github.com/%USER%/mcoder-mcsaver.git
git push -u origin main
if errorlevel 1 (
  echo [失败] 推送出错，常见原因：Token 权限不足 / 用户名拼写错误 / 网络不通。
  echo 请核对后重新运行。远程地址里的 Token 已保留以便重试，成功后会自动清除。
  pause
  exit /b 1
)

REM 3) 推送完成后去掉远程地址里的 Token，避免明文残留
echo [3/3] 清除远程地址中的 Token ...
git remote set-url origin https://github.com/%USER%/mcoder-mcsaver.git

echo.
echo ============================================================
echo 已完成！请打开 https://github.com/%USER%/mcoder-mcsaver 核对文件。
echo 然后去 M-China 官方活动页，用 ISSUE模板.md 的内容提交报名。
echo 安全提示：发布后建议到 GitHub 撤销刚才使用的 Token。
echo ============================================================
pause
