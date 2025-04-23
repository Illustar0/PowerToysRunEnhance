@echo off
setlocal enabledelayedexpansion
chcp 65001 > nul
set "ARCH=x64"
:: 创建并激活虚拟环境
echo 正在创建和激活虚拟环境...
uv venv
if %ERRORLEVEL% NEQ 0 (
    echo 创建虚拟环境失败！
    exit /b %ERRORLEVEL%
)

call ".venv\Scripts\activate.bat"
if %ERRORLEVEL% NEQ 0 (
    echo 激活虚拟环境失败！
    exit /b %ERRORLEVEL%
)

:: 安装依赖
echo 正在同步依赖...
uv sync --frozen
uv pip install nuitka
if %ERRORLEVEL% NEQ 0 (
    echo 依赖同步失败！
    exit /b %ERRORLEVEL%
)

:: 切换到源代码目录
cd src

:: 编译翻译文件
echo 正在编译翻译文件...
for %%F in ("i18n\*.ts") do (
    set "ts_file=%%F"
    set "qm_file=!ts_file:.ts=.qm!"

    echo 编译: !ts_file! → !qm_file!
    uv run pyside6-lrelease "!ts_file!" -qm "!qm_file!"
    if !ERRORLEVEL! NEQ 0 (
        echo 编译翻译文件 !ts_file! 失败！
        exit /b !ERRORLEVEL!
    )
)

:: 使用Nuitka编译成可执行文件
echo 正在编译项目...
uv run nuitka --mingw64 ^
--lto=yes ^
--standalone ^
--follow-imports ^
--include-module=comtypes.stream ^
--enable-plugin=pyside6 ^
--include-data-files=./config.toml=config.toml ^
--include-data-dir=./resources=resources ^
--windows-icon-from-ico=./resources/logo.ico ^
--windows-console-mode=disable ^
--product-name=PowerToysRunEnhance ^
--product-version=%NEW_VERSION% ^
--file-version=%NEW_VERSION% ^
--file-description="A non-intrusive tool that replaces Windows Search with PowerToys Run." ^
--copyright="Copyright (c) 2024 Illustar0 | MIT License" ^
--output-filename=PowerToysRunEnhance.exe ^
--include-data-files=./i18n/*.qm=i18n/ main.py

if %ERRORLEVEL% NEQ 0 (
    echo 编译项目失败！
    exit /b %ERRORLEVEL%
)

:: 使用UPX压缩
echo 正在使用UPX压缩文件...
for /r .\main.dist %%f in (*.dll *.pyd *.exe) do (
    uv run upx --best --lzma "%%f"
)

:: 使用7Z创建压缩包
echo 正在创建便携版压缩包...
if not exist .\Output mkdir .\Output
uv run 7z a -tzip -mx9 ".\Output\PowerRunEnhance-%NEW_VERSION%-%ARCH%-Portable.zip" ".\main.dist\*"
if %ERRORLEVEL% NEQ 0 (
    echo 创建便携版压缩包失败！
    exit /b %ERRORLEVEL%
)

:: 创建安装程序
echo 正在创建安装程序...
uv run iscc /F"PowerRunEnhance-%NEW_VERSION%-%ARCH%-Setup" /D"MyAppVersion=%NEW_VERSION%" setup.iss
if %ERRORLEVEL% NEQ 0 (
    echo 创建安装程序失败！
    exit /b %ERRORLEVEL%
)

echo 构建完成！
exit /b 0