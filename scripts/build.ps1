# 设置编码和参数
$OutputEncoding = [System.Text.Encoding]::UTF8

if ($null -eq $env:NEW_VERSION) {
    $env:NEW_VERSION = "0.1.0"
}

if ($null -eq $env:ARCH) {
    $env:ARCH = "x64"
}


# 创建并激活虚拟环境
Write-Host "正在创建和激活虚拟环境..."
if ($null -ne $env:PYTHON ) {
    uv venv --python $env:PYTHON
} else {
    uv venv
}

if ($LASTEXITCODE -ne 0) {
Write-Host "创建虚拟环境失败！"
exit $LASTEXITCODE
}

# 激活虚拟环境
& ".venv\Scripts\Activate.ps1"
if ($LASTEXITCODE -ne 0) {
Write-Host "激活虚拟环境失败！"
exit $LASTEXITCODE
}

# 安装依赖
Write-Host "正在同步依赖..."
uv sync --frozen
uv pip install nuitka
if ($LASTEXITCODE -ne 0) {
Write-Host "依赖同步失败！"
exit $LASTEXITCODE
}

# 切换到源代码目录
#Set-Location -Path src

# 编译翻译文件
<#
Write-Host "正在编译翻译文件..."
Get-ChildItem -Path "i18n\*.ts" | ForEach-Object {
    $ts_file = $_.FullName
    $qm_file = $ts_file -replace "\.ts$", ".qm"

    Write-Host "编译: $ts_file → $qm_file"
    uv run pyside6-lrelease "$ts_file" -qm "$qm_file"
    if ($LASTEXITCODE -ne 0) {
        Write-Host "编译翻译文件 $ts_file 失败！"
        exit $LASTEXITCODE
    }
}
#>

# 使用Nuitka编译成可执行文件
Write-Host "正在编译项目..."

<#
if ($null -ne $env:GITHUB_ACTIONS -and $env:GITHUB_ACTIONS -eq "true") {
    uv run nuitka --msvc=latest `
    --lto=yes `
    --standalone `
    --follow-imports `
    --include-module=comtypes.stream `
    --enable-plugin=pyside6 `
    --include-data-files=./config.toml=config.toml `
    --include-data-dir=./resources=resources `
    --windows-icon-from-ico=./resources/logo.ico `
    --windows-console-mode=disable `
    --product-name=PowerToysRunEnhance `
    --product-version=$env:NEW_VERSION `
    --file-version=$env:NEW_VERSION `
    --file-description="A non-intrusive tool that replaces Windows Search with PowerToys Run." `
    --copyright="Copyright (c) 2024 Illustar0 | MIT License" `
    --output-filename=PowerToysRunEnhance.exe `
    --assume-yes-for-downloads `
    --include-data-files=./i18n/*.qm=i18n/ main.py
} else {
    uv run nuitka --mingw64 `
    --lto=yes `
    --standalone `
    --follow-imports `
    --include-module=comtypes.stream `
    --enable-plugin=pyside6 `
    --include-data-files=./config.toml=config.toml `
    --include-data-dir=./resources=resources `
    --windows-icon-from-ico=./resources/logo.ico `
    --windows-console-mode=disable `
    --product-name=PowerToysRunEnhance `
    --product-version=$env:NEW_VERSION `
    --file-version=$env:NEW_VERSION `
    --file-description="A non-intrusive tool that replaces Windows Search with PowerToys Run." `
    --copyright="Copyright (c) 2024 Illustar0 | MIT License" `
    --output-filename=PowerToysRunEnhance.exe `
    --assume-yes-for-downloads `
    --include-data-files=./i18n/*.qm=i18n/ main.py
}
#>


$nuitkaArgs = @(
    "--mingw64",
    "--lto=yes",
    "--standalone",
    "--follow-imports",
    "--include-module=comtypes.stream",
    "--include-module=scipy._cyutility",
    "--enable-plugin=pyside6",
    "--include-data-files=./src/providers/*.py=providers/",
    "--include-data-dir=./src/resources=resources",
    "--include-package=src.providers",
    "--windows-icon-from-ico=./src/resources/logo.ico",
    "--product-name=WindowsSearchUtility",
    "--product-version=$env:NEW_VERSION",
    "--file-version=$env:NEW_VERSION",
    "--file-description=WindowsSearchUtility",
    "--copyright=Copyright (c) 2024-2025 Illustar0 | GPLv3 License",
    "--output-filename=WindowsSearchUtility.exe",
    "--assume-yes-for-downloads"
)


if ($null -ne $env:USE_UPX) {
    Write-Host "USE_UPX environment variable is set. Enabling UPX plugin." -ForegroundColor Green
    $nuitkaArgs += "--enable-plugin=upx"
} else {
    Write-Host "USE_UPX environment variable not set. UPX plugin will be disabled." -ForegroundColor Yellow
}


if ($null -ne $env:DEBUG -and $env:DEBUG -eq "DEBUG") {
    Write-Host "Building in DEBUG mode..." -ForegroundColor Cyan
} else {
    Write-Host "Building in RELEASE mode..." -ForegroundColor Cyan
    $nuitkaArgs += "--windows-console-mode=disable"
    $nuitkaArgs += "--deployment"
}

$nuitkaArgs += "src/main.py"

Write-Host "Running Nuitka with the following arguments:"

$nuitkaArgs | ForEach-Object { Write-Host "  $_" }

uv run nuitka @nuitkaArgs

if ($LASTEXITCODE -ne 0) {
    Write-Host "编译项目失败！"
    exit $LASTEXITCODE
}

# 使用7Z创建压缩包
Write-Host "正在创建便携版压缩包..."
if (-not (Test-Path -Path ".\Output")) {
    New-Item -ItemType Directory -Path ".\Output" | Out-Null
}
if ($null -ne $env:DEBUG -and $env:DEBUG -eq "DEBUG") {
    uv run 7z a -tzip -mx9 ".\Output\WindowsSearchUtility-$env:NEW_VERSION-$env:ARCH-Portable-Debug.zip" ".\main.dist\*"
} else {
    uv run 7z a -tzip -mx9 ".\Output\WindowsSearchUtility-$env:NEW_VERSION-$env:ARCH-Portable.zip" ".\main.dist\*"
}
if ($LASTEXITCODE -ne 0) {
    Write-Host "创建便携版压缩包失败！"
    exit $LASTEXITCODE
}

# 创建安装程序
Write-Host "正在创建安装程序..."
if ($null -ne $env:DEBUG -and $env:DEBUG -eq "DEBUG") {
    uv run iscc /F"WindowsSearchUtility-$env:NEW_VERSION-$env:ARCH-Setup-Debug" /D"MyAppVersion=$env:NEW_VERSION" scripts/setup.iss
} else {
    uv run iscc /F"WindowsSearchUtility-$env:NEW_VERSION-$env:ARCH-Setup" /D"MyAppVersion=$env:NEW_VERSION" scripts/setup.iss
}

if ($LASTEXITCODE -ne 0) {
    Write-Host "创建安装程序失败！"
    exit $LASTEXITCODE
}

Write-Host "构建完成！"
exit 0 