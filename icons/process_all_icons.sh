#!/bin/bash
set -e

echo '=========================================='
echo 'Processing Cloud Provider Icons'
echo '=========================================='
echo ''

# Process AWS icons (prefer PNG, fallback to SVG)
echo '[1/3] Processing AWS icons...'
count=0
find .temp/aws -type f \( -name '*.png' -o -name '*.svg' \) 2>/dev/null | while read -r icon; do
    filename=$(basename "$icon")
    ext="${filename##*.}"
    base="${filename%.*}"
    
    # Clean filename: lowercase, replace spaces/hyphens with underscores
    clean_name=$(echo "$base" | tr '[:upper:]' '[:lower:]' | sed 's/[- ]/_/g' | sed 's/__*/_/g' | sed 's/_32$//' | sed 's/_48$//' | sed 's/_64$//' | sed 's/_dark$//' | sed 's/_light$//')
    
    # Skip if already processed
    [ -f "aws/${clean_name}.png" ] && continue
    
    # Check file size
    filesize=$(stat -c%s "$icon" 2>/dev/null || echo "0")
    [ "$filesize" -lt 500 ] && continue
    
    # Convert to PNG if SVG, or resize if PNG
    if [ "$ext" = "svg" ]; then
        convert "$icon" -resize 256x256 -background none "aws/${clean_name}.png" 2>/dev/null || true
    else
        convert "$icon" -resize 256x256 -background none -gravity center -extent 256x256 "aws/${clean_name}.png" 2>/dev/null || true
    fi
    count=$((count + 1))
    if [ $((count % 100)) -eq 0 ]; then
        echo "  Processed $count icons..."
    fi
done

aws_count=$(find aws -type f -name '*.png' 2>/dev/null | wc -l)
echo "✓ Processed $aws_count AWS icons"
echo ''

# Process Azure icons (all SVG)
echo '[2/3] Processing Azure icons...'
count=0
find .temp/azure -type f -name '*.svg' 2>/dev/null | while read -r icon; do
    filename=$(basename "$icon")
    base="${filename%.svg}"
    
    # Clean filename
    clean_name=$(echo "$base" | tr '[:upper:]' '[:lower:]' | sed 's/[- ]/_/g' | sed 's/__*/_/g' | sed 's/_icon$//')
    
    # Skip if already processed
    [ -f "azure/${clean_name}.png" ] && continue
    
    # Check file size
    filesize=$(stat -c%s "$icon" 2>/dev/null || echo "0")
    [ "$filesize" -lt 300 ] && continue
    
    # Convert SVG to PNG
    convert "$icon" -resize 256x256 -background none "azure/${clean_name}.png" 2>/dev/null || true
    count=$((count + 1))
    if [ $((count % 50)) -eq 0 ]; then
        echo "  Processed $count icons..."
    fi
done

azure_count=$(find azure -type f -name '*.png' 2>/dev/null | wc -l)
echo "✓ Processed $azure_count Azure icons"
echo ''

# Process GCP icons
echo '[3/3] Processing GCP icons...'
find .temp/gcp -type f \( -name '*.png' -o -name '*.svg' \) 2>/dev/null | while read -r icon; do
    filename=$(basename "$icon")
    ext="${filename##*.}"
    base="${filename%.*}"
    
    # Clean filename
    clean_name=$(echo "$base" | tr '[:upper:]' '[:lower:]' | sed 's/[- ]/_/g' | sed 's/__*/_/g')
    
    # Skip if already processed
    [ -f "gcp/${clean_name}.png" ] && continue
    
    # Check file size
    filesize=$(stat -c%s "$icon" 2>/dev/null || echo "0")
    [ "$filesize" -lt 300 ] && continue
    
    # Convert to PNG if SVG, or resize if PNG
    if [ "$ext" = "svg" ]; then
        convert "$icon" -resize 256x256 -background none "gcp/${clean_name}.png" 2>/dev/null || true
    else
        convert "$icon" -resize 256x256 -background none -gravity center -extent 256x256 "gcp/${clean_name}.png" 2>/dev/null || true
    fi
done

gcp_count=$(find gcp -type f -name '*.png' 2>/dev/null | wc -l)
echo "✓ Processed $gcp_count GCP icons"
echo ''

# Cleanup
echo 'Cleaning up temporary files...'
rm -rf .temp aws-temp azure-temp gcp-temp
echo ''

echo '=========================================='
echo '✓ Icon processing complete!'
echo '=========================================='
echo "Summary:"
echo "  AWS icons:   $aws_count"
echo "  Azure icons: $azure_count"
echo "  GCP icons:   $gcp_count"
echo ''
echo 'Icons are now ready to use with the diagram generator!'
