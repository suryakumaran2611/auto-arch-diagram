#!/usr/bin/env python3
"""Generate custom icons for architecture diagrams"""

from PIL import Image, ImageDraw
import math
import os

def create_icon(name, color):
    """Create a simple custom icon"""
    size = 128
    img = Image.new('RGBA', (size, size), (255, 255, 255, 0))
    draw = ImageDraw.Draw(img)
    
    # Add colored shape based on icon type
    if name == 'datapipeline':
        # Pipeline with arrows
        draw.rectangle([20, 40, 108, 60], fill=color)
        draw.polygon([(108, 35), (108, 65), (128, 50)], fill=color)
        draw.rectangle([20, 68, 108, 88], fill=color)
        draw.polygon([(108, 63), (108, 93), (128, 78)], fill=color)
    
    elif name == 'datastream':
        # Flowing lines
        for i in range(5):
            y = 20 + i * 22
            draw.ellipse([10, y, 30, y+10], fill=color)
            draw.rectangle([25, y+2, 55, y+8], fill=color)
            draw.ellipse([50, y, 70, y+10], fill=color)
            draw.rectangle([65, y+2, 95, y+8], fill=color)
            draw.ellipse([90, y, 110, y+10], fill=color)
    
    elif name == 'streamprocessor':
        # Processor with gears
        draw.ellipse([30, 30, 98, 98], outline=color, width=8)
        draw.rectangle([50, 20, 78, 108], fill=color)
        draw.rectangle([20, 50, 108, 78], fill=color)
    
    elif name == 'eventtrigger':
        # Lightning bolt
        draw.polygon([(64, 20), (50, 64), (64, 64), (50, 108), (78, 64), (64, 64)], fill=color)
    
    elif name == 'databasestream':
        # Database with stream
        draw.ellipse([25, 20, 75, 40], fill=color)
        draw.rectangle([25, 30, 75, 70], fill=color)
        draw.ellipse([25, 60, 75, 80], fill=color)
        # Stream arrows
        for y in [40, 60]:
            draw.polygon([(80, y-5), (80, y+5), (105, y)], fill=color)
    
    elif name == 'searchengine':
        # Magnifying glass
        draw.ellipse([20, 20, 80, 80], outline=color, width=8)
        draw.rectangle([65, 65, 105, 75], fill=color, outline=None)
        draw.polygon([(75, 70), (108, 108), (108, 70)], fill=color)
    
    elif name == 'datacrawler':
        # Spider/crawler
        center = 64
        draw.ellipse([center-20, center-20, center+20, center+20], fill=color)
        for angle in range(0, 360, 45):
            x = center + int(40 * math.cos(math.radians(angle)))
            y = center + int(40 * math.sin(math.radians(angle)))
            draw.line([(center, center), (x, y)], fill=color, width=4)
            draw.ellipse([x-5, y-5, x+5, y+5], fill=color)
    
    elif name == 'scheduler':
        # Clock
        draw.ellipse([20, 20, 108, 108], outline=color, width=8)
        draw.rectangle([60, 25, 68, 64], fill=color)
        draw.rectangle([64, 60, 90, 68], fill=color)
    
    elif name == 'alertnotification':
        # Bell
        draw.polygon([(45, 30), (83, 30), (90, 70), (38, 70)], fill=color)
        draw.ellipse([52, 70, 76, 88], fill=color)
        draw.rectangle([60, 18, 68, 30], fill=color)
        draw.ellipse([58, 12, 70, 24], fill=color)
    
    elif name == 'messagequeue':
        # Queue boxes
        for i, y in enumerate([20, 50, 80]):
            alpha = 255 - i * 50
            c = color[:3] + (alpha,) if len(color) == 4 else color
            draw.rectangle([30, y, 98, y+25], fill=c, outline=color[:3] if len(color) == 4 else color, width=3)
    
    elif name == 'cloudmonitor':
        # Monitor with graph
        draw.rectangle([20, 30, 108, 90], outline=color, width=6)
        # Graph line
        points = [(30, 75), (45, 55), (60, 65), (75, 45), (90, 60), (98, 40)]
        for i in range(len(points)-1):
            draw.line([points[i], points[i+1]], fill=color, width=4)
    
    return img

def main():
    """Generate all custom icons"""
    icons = {
        'datapipeline': (52, 152, 219, 255),      # Blue
        'datastream': (46, 204, 113, 255),        # Green
        'streamprocessor': (155, 89, 182, 255),   # Purple
        'eventtrigger': (241, 196, 15, 255),      # Yellow
        'databasestream': (52, 73, 94, 255),      # Dark blue
        'searchengine': (230, 126, 34, 255),      # Orange
        'datacrawler': (231, 76, 60, 255),        # Red
        'scheduler': (22, 160, 133, 255),         # Teal
        'alertnotification': (192, 57, 43, 255),  # Dark red
        'messagequeue': (142, 68, 173, 255),      # Purple
        'cloudmonitor': (41, 128, 185, 255),      # Blue
    }
    
    for name, color in icons.items():
        img = create_icon(name, color)
        filename = f'{name}.png'
        img.save(filename)
        print(f'Created {filename}')
    
    print('\nAll custom icons created successfully!')

if __name__ == '__main__':
    main()
