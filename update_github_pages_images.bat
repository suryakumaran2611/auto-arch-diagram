@echo off
REM Auto Architecture Diagram - Update GitHub Pages Images Script (Windows)
REM This script regenerates all example diagrams and updates GitHub Pages documentation

echo 🚀 Auto Architecture Diagram - GitHub Pages Image Update Script
echo =================================================================

REM Check if virtual environment exists
if not exist ".venv" (
    echo ❌ Virtual environment not found. Please run setup first.
    exit /b 1
)

REM Activate virtual environment
echo 📦 Activating virtual environment...
call .venv\Scripts\activate.bat
if errorlevel 1 (
    echo ❌ Failed to activate virtual environment
    exit /b 1
)

REM Function to regenerate a diagram
goto :main

:regenerate_diagram
set INPUT_FILE=%~1
set OUTPUT_PNG=%~2
set OUTPUT_SVG=%~3
set DESCRIPTION=%~4

echo 🔄 Regenerating %DESCRIPTION%...

python tools\generate_arch_diagram.py --changed-files "%INPUT_FILE%" --out-png "%OUTPUT_PNG%" --out-svg "%OUTPUT_SVG%"
if errorlevel 1 (
    echo ❌ Failed to generate %DESCRIPTION%
    exit /b 1
) else (
    echo ✅ Successfully generated %DESCRIPTION%
)
goto :eof

:update_docs_image
set SOURCE_FILE=%~1
set DEST_FILE=%~2
set DESCRIPTION=%~3

copy "%SOURCE_FILE%" "%DEST_FILE%" >nul
if errorlevel 1 (
    echo ❌ Failed to update %DESCRIPTION% in docs
    exit /b 1
) else (
    echo 📋 Updated %DESCRIPTION% in docs
)
goto :eof

:check_icons
set FILE=%~1
set EXPECTED=%~2
set DESCRIPTION=%~3

if exist "%FILE%" (
    for /f %%i in ('findstr /r /c:"base64" "%FILE%" 2^>nul ^| find /c "base64"') do set COUNT=%%i
    if !COUNT! equ %EXPECTED% (
        echo ✅ %DESCRIPTION%: !COUNT! icons (expected %EXPECTED%)
    ) else (
        echo ⚠️  %DESCRIPTION%: !COUNT! icons (expected %EXPECTED%)
    )
) else (
    echo ❌ %DESCRIPTION%: File not found
)
goto :eof

:main
echo.
echo 🔄 Regenerating all example diagrams...
echo =========================================

REM Regenerate CloudFormation examples
call :regenerate_diagram "examples\serverless-website\aws\cloudformation\template.yaml" "examples\serverless-website\aws\cloudformation\architecture-diagram.png" "examples\serverless-website\aws\cloudformation\architecture-diagram.svg" "AWS CloudFormation Serverless Website"

REM Regenerate Terraform examples
call :regenerate_diagram "examples\serverless-website\aws\terraform\main.tf" "examples\serverless-website\aws\terraform\architecture-diagram.png" "examples\serverless-website\aws\terraform\architecture-diagram.svg" "AWS Terraform Serverless Website"

call :regenerate_diagram "examples\serverless-website\azure\terraform\main.tf" "examples\serverless-website\azure\terraform\architecture-diagram.png" "examples\serverless-website\azure\terraform\architecture-diagram.svg" "Azure Terraform Serverless Website"

call :regenerate_diagram "examples\serverless-website\gcp\terraform\main.tf" "examples\serverless-website\gcp\terraform\architecture-diagram.png" "examples\serverless-website\gcp\terraform\architecture-diagram.svg" "GCP Terraform Serverless Website"

REM Regenerate multi-cloud example
call :regenerate_diagram "examples\terraform\mlops-multi-cloud\main.tf" "examples\terraform\mlops-multi-cloud\architecture-diagram.png" "examples\terraform\mlops-multi-cloud\architecture-diagram.svg" "Multi-Cloud Demo"

REM Regenerate other key examples
call :regenerate_diagram "examples\terraform\custom-icons-demo\main.tf" "examples\terraform\custom-icons-demo\architecture-diagram.png" "examples\terraform\custom-icons-demo\architecture-diagram.svg" "Custom Icons Demo"

call :regenerate_diagram "examples\terraform\mlops-multi-region-aws\main.tf" "examples\terraform\mlops-multi-region-aws\architecture-diagram.png" "examples\terraform\mlops-multi-region-aws\architecture-diagram.svg" "MLOps Multi-Region AWS"

echo.
echo 📋 Updating GitHub Pages documentation images...
echo ==================================================

REM Update docs/images/ with latest generated diagrams
call :update_docs_image "examples\terraform\mlops-multi-cloud\architecture-diagram.png" "docs\images\mlops-multi-cloud.png" "Multi-Cloud Demo image"

call :update_docs_image "examples\terraform\custom-icons-demo\architecture-diagram.png" "docs\images\custom-icons-demo.png" "Custom Icons Demo image"

call :update_docs_image "examples\terraform\mlops-multi-region-aws\architecture-diagram.png" "docs\images\mlops-aws.png" "MLOps Multi-Region AWS image"

call :update_docs_image "examples\serverless-website\aws\terraform\architecture-diagram.png" "docs\images\aws-serverless.png" "AWS Serverless Website image"

call :update_docs_image "examples\serverless-website\azure\terraform\architecture-diagram.png" "docs\images\azure-serverless.png" "Azure Serverless Website image"

call :update_docs_image "examples\serverless-website\gcp\terraform\architecture-diagram.png" "docs\images\gcp-serverless.png" "GCP Serverless Website image"

echo.
echo 📊 Verification - Checking icon counts...
echo ===========================================

REM Enable delayed expansion for variable handling
setlocal enabledelayedexpansion

call :check_icons "examples\terraform\mlops-multi-cloud\architecture-diagram.svg" "7" "Multi-Cloud Demo"
call :check_icons "examples\serverless-website\aws\cloudformation\architecture-diagram.svg" "8" "AWS CloudFormation"
call :check_icons "examples\serverless-website\aws\terraform\architecture-diagram.svg" "11" "AWS Terraform"
call :check_icons "examples\serverless-website\azure\terraform\architecture-diagram.svg" "6" "Azure Terraform"
call :check_icons "examples\serverless-website\gcp\terraform\architecture-diagram.svg" "8" "GCP Terraform"

echo.
echo 🎉 GitHub Pages images update complete!
echo =========================================
echo.
echo 📝 Summary:
echo   • Regenerated 7 key example diagrams
echo   • Updated 6 GitHub Pages documentation images
echo   • Verified icon counts match expectations
echo.
echo 📍 Files updated:
echo   • docs\images\mlops-multi-cloud.png
echo   • docs\images\custom-icons-demo.png
echo   • docs\images\mlops-aws.png
echo   • docs\images\aws-serverless.png
echo   • docs\images\azure-serverless.png
echo   • docs\images\gcp-serverless.png
echo.
echo 🔄 Next steps:
echo   1. Commit the updated images to git
echo   2. Push to GitHub to update GitHub Pages
echo   3. The documentation will reflect the latest code changes