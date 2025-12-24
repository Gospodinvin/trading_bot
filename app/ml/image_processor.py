import cv2
import numpy as np
from PIL import Image
import io
from app.utils.logger import logger

class ImageProcessor:
    def __init__(self):
        self.min_chart_area = 1000
        self.candle_min_area = 50
        self.candle_max_area = 500
        
    def preprocess_image(self, image_bytes):
        """Preprocess image for analysis"""
        try:
            # Convert bytes to PIL Image
            image = Image.open(io.BytesIO(image_bytes))
            image = image.convert('RGB')
            img_np = np.array(image)
            
            # Convert to grayscale
            gray = cv2.cvtColor(img_np, cv2.COLOR_RGB2GRAY)
            
            # Enhance contrast
            gray = cv2.equalizeHist(gray)
            
            # Apply bilateral filter to reduce noise
            gray = cv2.bilateralFilter(gray, 9, 75, 75)
            
            # Normalize
            gray = gray / 255.0
            
            return gray, img_np
        except Exception as e:
            logger.error(f"Image preprocessing error: {e}")
            raise
    
    def detect_chart_grid(self, gray_image):
        """Detect chart grid using line detection"""
        # Edge detection
        edges = cv2.Canny(gray_image, 50, 150, apertureSize=3)
        
        # Detect lines using Hough Transform
        lines = cv2.HoughLinesP(
            edges, 
            1, 
            np.pi/180, 
            threshold=50, 
            minLineLength=30, 
            maxLineGap=10
        )
        
        if lines is not None:
            # Count horizontal and vertical lines
            horizontal = 0
            vertical = 0
            
            for line in lines:
                x1, y1, x2, y2 = line[0]
                angle = np.arctan2(y2 - y1, x2 - x1) * 180 / np.pi
                
                if abs(angle) < 10 or abs(angle - 180) < 10:  # Horizontal
                    horizontal += 1
                elif abs(angle - 90) < 10:  # Vertical
                    vertical += 1
            
            return horizontal >= 2 and vertical >= 2
        
        return False
    
    def detect_candles(self, gray_image, color_image):
        """Detect candlesticks in the image"""
        # Threshold to binary
        _, binary = cv2.threshold((gray_image * 255).astype(np.uint8), 
                                 127, 255, cv2.THRESH_BINARY_INV)
        
        # Find contours
        contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, 
                                      cv2.CHAIN_APPROX_SIMPLE)
        
        candles = []
        for contour in contours:
            area = cv2.contourArea(contour)
            
            # Filter by area (candle size)
            if self.candle_min_area < area < self.candle_max_area:
                x, y, w, h = cv2.boundingRect(contour)
                
                # Calculate aspect ratio (candles are usually tall and thin)
                aspect_ratio = h / w if w > 0 else 0
                
                if aspect_ratio > 1.5:  # Typical candle aspect ratio
                    # Get color at the center
                    center_x = x + w // 2
                    center_y = y + h // 2
                    
                    if 0 <= center_x < color_image.shape[1] and 0 <= center_y < color_image.shape[0]:
                        color = color_image[center_y, center_x]
                        
                        # Determine if it's green (bullish) or red (bearish) candle
                        is_green = self._is_green_candle(color)
                        is_red = self._is_red_candle(color)
                        
                        candles.append({
                            'x': x,
                            'y': y,
                            'width': w,
                            'height': h,
                            'center_x': center_x,
                            'center_y': center_y,
                            'color': 'green' if is_green else 'red' if is_red else 'unknown',
                            'area': area
                        })
        
        # Sort candles by x position (left to right)
        candles.sort(key=lambda c: c['x'])
        
        return candles
    
    def _is_green_candle(self, color):
        """Check if color represents a green candle"""
        r, g, b = color
        # Green candles: higher green value
        return g > r and g > b and g > 100
    
    def _is_red_candle(self, color):
        """Check if color represents a red candle"""
        r, g, b = color
        # Red candles: higher red value
        return r > g and r > b and r > 100
    
    def extract_ohlc_from_candles(self, candles, image_height):
        """Extract OHLC data from detected candles"""
        if not candles:
            return None
        
        ohlc_data = []
        
        for candle in candles:
            # Convert y position to price (assuming higher y = lower price)
            # This is a simplification - real implementation needs scale calibration
            high_price = candle['y'] / image_height
            low_price = (candle['y'] + candle['height']) / image_height
            
            # For simplicity, assume body is middle 60% of candle
            body_start = candle['y'] + candle['height'] * 0.2
            body_end = candle['y'] + candle['height'] * 0.8
            
            if candle['color'] == 'green':
                open_price = body_start / image_height
                close_price = body_end / image_height
            else:  # red candle
                open_price = body_end / image_height
                close_price = body_start / image_height
            
            ohlc_data.append({
                'open': open_price,
                'high': high_price,
                'low': low_price,
                'close': close_price,
                'color': candle['color']
            })
        
        return ohlc_data
    
    def prepare_for_cnn(self, gray_image):
        """Prepare image for CNN model"""
        # Resize to 64x64
        resized = cv2.resize(gray_image, (64, 64))
        
        # Add channel dimension
        if len(resized.shape) == 2:
            resized = np.expand_dims(resized, axis=-1)
        
        # Normalize
        resized = resized.astype(np.float32)
        
        return np.expand_dims(resized, axis=0)