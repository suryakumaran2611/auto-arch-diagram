#!/bin/bash
# Script to help setup cloud provider icons for auto-arch-diagram
# Since cloud provider icon packages require manual download, this script
# provides instructions and helps organize icons once downloaded

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
ICONS_DIR="$REPO_ROOT/icons"

echo "=========================================="
echo "Cloud Provider Icons Setup"
echo "=========================================="
echo ""
echo "Cloud provider icon packages require manual download."
echo "Please download the latest icon packages from:"
echo ""
echo "1. AWS Architecture Icons:"
echo "   Visit: https://aws.amazon.com/architecture/icons/"
echo "   Download: Asset Package (ZIP)"
echo "   Save to: $REPO_ROOT/downloads/aws-icons.zip"
echo ""
echo "2. Azure Architecture Icons:"
echo "   Visit: https://learn.microsoft.com/en-us/azure/architecture/icons/"
echo "   Download: All Azure icons (SVG)"
echo "   Save to: $REPO_ROOT/downloads/azure-icons.zip"
echo ""
echo "3. GCP Architecture Icons:"
echo "   Visit: https://cloud.google.com/icons"
echo "   Download: All icons"
echo "   Save to: $REPO_ROOT/downloads/gcp-icons.zip"
echo ""
echo "=========================================="
echo ""

# Check if downloads directory exists and has files
DOWNLOADS_DIR="$REPO_ROOT/downloads"
if [ ! -d "$DOWNLOADS_DIR" ]; then
    mkdir -p "$DOWNLOADS_DIR"
    echo "Created downloads directory: $DOWNLOADS_DIR"
    echo "Please download icon packages there and run this script again."
    exit 0
fi

# Check for downloaded files
AWS_ZIP="$DOWNLOADS_DIR/aws-icons.zip"
AZURE_ZIP="$DOWNLOADS_DIR/azure-icons.zip"
GCP_ZIP="$DOWNLOADS_DIR/gcp-icons.zip"

found_count=0
if [ -f "$AWS_ZIP" ]; then found_count=$((found_count + 1)); fi
if [ -f "$AZURE_ZIP" ]; then found_count=$((found_count + 1)); fi
if [ -f "$GCP_ZIP" ]; then found_count=$((found_count + 1)); fi

if [ $found_count -eq 0 ]; then
    echo "No icon packages found in $DOWNLOADS_DIR"
    echo "Please download icon packages and try again."
    exit 0
fi

echo "Found $found_count icon package(s). Processing..."
echo ""

TEMP_DIR="$REPO_ROOT/.icons_temp"
mkdir -p "$TEMP_DIR"
cd "$TEMP_DIR"

# ============================================
# AWS Icons
# ============================================
if [ -f "$AWS_ZIP" ]; then
    echo "[1/3] Processing AWS Architecture Icons..."
    
    if ! unzip -t "$AWS_ZIP" >/dev/null 2>&1; then
        echo "⚠ AWS ZIP file appears corrupted, skipping..."
    else
        unzip -q "$AWS_ZIP" -d aws-extracted
        
        # Find PNG icons and copy to icons/aws/
        echo "Extracting AWS icons..."
        mkdir -p "$ICONS_DIR/aws"
        find aws-extracted -type f -name "*.png" | while read -r icon; do
            filename=$(basename "$icon")
            # Convert to lowercase and replace spaces/hyphens with underscores
            clean_name=$(echo "$filename" | tr '[:upper:]' '[:lower:]' | tr ' -' '__' | sed 's/_dark\.png$/\.png/' | sed 's/_light\.png$/\.png/')
            
            # Check file size (skip very small files - likely thumbnails)
            filesize=$(stat -c%s "$icon" 2>/dev/null || stat -f%z "$icon" 2>/dev/null || echo "0")
            
            if [ "$filesize" -ge 1024 ]; then
                # Resize to 256x256 if imagemagick is available, otherwise just copy
                if command -v convert &> /dev/null; then
                    convert "$icon" -resize 256x256 -background none -gravity center -extent 256x256 "$ICONS_DIR/aws/$clean_name" 2>/dev/null || cp "$icon" "$ICONS_DIR/aws/$clean_name"
                else
                    cp "$icon" "$ICONS_DIR/aws/$clean_name"
                fi
            fi
        done
        
        aws_count=$(find "$ICONS_DIR/aws" -type f -name "*.png" | wc -l)
        echo "✓ Processed $aws_count AWS icons"
    fi
    echo ""
fi

# ============================================
# Azure Icons
# ============================================
if [ -f "$AZURE_ZIP" ]; then
    echo "[2/3] Processing Azure Architecture Icons..."
    
    if ! unzip -t "$AZURE_ZIP" >/dev/null 2>&1; then
        echo "⚠ Azure ZIP file appears corrupted, skipping..."
    else
        unzip -q "$AZURE_ZIP" -d azure-extracted
        
        echo "Extracting Azure icons..."
        mkdir -p "$ICONS_DIR/azure"
        find azure-extracted -type f \( -name "*.svg" -o -name "*.png" \) | while read -r icon; do
            filename=$(basename "$icon")
            ext="${filename##*.}"
            
            # Convert to lowercase and clean name
            clean_name=$(echo "$filename" | tr '[:upper:]' '[:lower:]' | tr ' -' '__')
            
            # Check file size (skip very small files)
            filesize=$(stat -c%s "$icon" 2>/dev/null || stat -f%z "$icon" 2>/dev/null || echo "0")
            
            if [ "$filesize" -ge 512 ]; then
                # Convert SVG to PNG if imagemagick is available
                if [ "$ext" = "svg" ] && command -v convert &> /dev/null; then
                    clean_name="${clean_name%.svg}.png"
                    convert "$icon" -resize 256x256 -background none "$ICONS_DIR/azure/$clean_name" 2>/dev/null
                elif [ "$ext" = "png" ]; then
                    # Resize PNG to 256x256 if imagemagick is available
                    if command -v convert &> /dev/null; then
                        convert "$icon" -resize 256x256 -background none -gravity center -extent 256x256 "$ICONS_DIR/azure/$clean_name" 2>/dev/null || cp "$icon" "$ICONS_DIR/azure/$clean_name"
                    else
                        cp "$icon" "$ICONS_DIR/azure/$clean_name"
                    fi
                fi
            fi
        done
        
        azure_count=$(find "$ICONS_DIR/azure" -type f -name "*.png" | wc -l)
        echo "✓ Processed $azure_count Azure icons"
    fi
    echo ""
fi

# ============================================
# GCP Icons
# ============================================
# GCP icons (official Google Cloud icon repository)
GCP_URL="https://cloud.google.com/icons
GCP_URL="https://cloud.google.com/static/icons/files/google-cloud-icons.zip"
GCP_ZIP="gcp-icons.zip"

if command -v curl &> /dev/null; then
    curl -L -o "$GCP_ZIP" "$GCP_URL" || echo "Warning: GCP icons download failed, skipping..."
else
    wget -O "$GCP_ZIP" "$GCP_URL" || echo "Warning: GCP icons download failed, skipping..."
fi

if [ -f "$GCP_ZIP" ]; then
    echo "Extracting GCP icons..."
    unzip -q "$GCP_ZIP" -d gcp-extracted 2>/dev/null || true
    
    echo "Processing GCP icons..."
    mkdir -p "$ICONS_DIR/gcp"
    find gcp-extracted -type f \( -name "*.svg" -o -name "*.png" \) | while read -r icon; do
        filename=$(basename "$icon")
        ext="${filename##*.}"
        
        # Convert to lowercase and clean name
        clean_name=$(echo "$filename" | tr '[:upper:]' '[:lower:]' | tr ' -' '__')
        
        # Check file size (skip very small files)
        filesize=$(stat -c%s "$icon" 2>/dev/null || stat -f%z "$icon" 2>/dev/null || echo "0")
        
        if [ "$filesize" -ge 512 ]; then
            # Convert SVG to PNG if imagemagick is available
            if [ "$ext" = "svg" ] && command -v convert &> /dev/null; then
                clean_name="${clean_name%.svg}.png"
                convert "$icon" -resize 256x256 -background none "$ICONS_DIR/gcp/$clean_name" 2>/dev/null
            elif [ "$ext" = "png" ]; then
                # Resize PNG to 256x256 if imagemagick is available
                if command -v convert &> /dev/null; then
                    convert "$icon" -resize 256x256 -background none -gravity center -extent 256x256 "$ICONS_DIR/gcp/$clean_name" 2>/dev/null || cp "$icon" "$ICONS_DIR/gcp/$clean_name"
                else
                    cp "$icon" "$ICONS_DIR/gcp/$clean_name"
                fi
            fi
        fi
    done
    
    gcp_count=$(find "$ICONS_DIR/gcp" -type f -name "*.png" | wc -l)
    echo "✓ Processed $gcp_count GCP icons"
else
    echo "⚠ GCP icons download skipped"
fi
echo ""

# ============================================
# Cleanup
# ============================================
echo "Cleaning up temporary files..."
cd "$REPO_ROOT"
rm -rf "$TEMP_DIR"

echo ""
echo "=========================================="
echo "✓ Icon processing complete!"
echo "=========================================="
if [ -f "$AWS_ZIP" ]; then
    aws_final=$(find "$ICONS_DIR/aws" -type f -name "*.png" 2>/dev/null | wc -l)
    echo "  AWS icons:   $aws_final"
fi
if [ -f "$AZURE_ZIP" ]; then
    azure_final=$(find "$ICONS_DIR/azure" -type f -name "*.png" 2>/dev/null | wc -l)
    echo "  Azure icons: $azure_final"
fi
if [ -f "$GCP_ZIP" ]; then
    gcp_final=$(find "$ICONS_DIR/gcp" -type f -name "*.png" 2>/dev/null | wc -l)
    echo "  GCP icons:   $gcp_final"
fi
echo ""
echo "Icons saved to: $ICONS_DIR"
echo ""
echo "Next steps:"
echo "1. Run: python3 tools/map_icons.py"
echo "2. Review icon mappings in icons/icon_mappings.json"
echo "3. Rename icons to match Terraform resource types"
echo "   Example: azurerm_static_web_app → static_web_app.png"
echo ""
