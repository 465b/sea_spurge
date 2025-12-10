# These methods aim to reduce the verticies count of polygons used on the simulations
# by applying the Ramer-Douglas-Peucker algorithm for line simplification.
# (https://en.wikipedia.org/wiki/Ramer%E2%80%93Douglas%E2%80%93Peucker_algorithm)
# This helps to keep computational time down for "is inside" checks and output jsons small

import math

def _point_to_line_distance(point, line_start, line_end):
    """
    Calculate the perpendicular distance from a point to a line segment.
    
    Args:
        point: [x, y] coordinates of the point
        line_start: [x, y] coordinates of line start
        line_end: [x, y] coordinates of line end
    
    Returns:
        Distance in meters
    """
    x0, y0 = point
    x1, y1 = line_start
    x2, y2 = line_end
    
    # Calculate the distance using the formula for point-to-line distance
    numerator = abs((y2 - y1) * x0 - (x2 - x1) * y0 + x2 * y1 - y2 * x1)
    denominator = math.sqrt((y2 - y1)**2 + (x2 - x1)**2)
    
    if denominator == 0:
        # Line start and end are the same point, return distance to that point
        return math.sqrt((x0 - x1)**2 + (y0 - y1)**2)
    
    return numerator / denominator

def ramer_douglas_peucker(points, tolerance):
    """
    Apply the Ramer-Douglas-Peucker algorithm to simplify a polygon.
    
    Args:
        points: List of [x, y] coordinate pairs
        tolerance: Maximum allowed distance from simplified line (in meters)
    
    Returns:
        Simplified list of points
    """
    if len(points) <= 2:
        return points
    
    # Find the point with the maximum distance from the line connecting first and last points
    max_distance = 0
    max_index = 0
    
    for i in range(1, len(points) - 1):
        distance = _point_to_line_distance(points[i], points[0], points[-1])
        if distance > max_distance:
            max_distance = distance
            max_index = i
    
    # If the maximum distance is greater than tolerance, recursively simplify
    if max_distance > tolerance:
        # Recursively simplify the two segments
        left_segment = ramer_douglas_peucker(points[:max_index + 1], tolerance)
        right_segment = ramer_douglas_peucker(points[max_index:], tolerance)
        
        # Combine the results (removing the duplicate point at max_index)
        return left_segment[:-1] + right_segment
    else:
        # If all points are within tolerance, return just the endpoints
        return [points[0], points[-1]]

def simplify_polygons(catch_polys, tolerance=1000.0):
    """
    Simplify a list of catch polygons using the Ramer-Douglas-Peucker algorithm.
    
    Args:
        catch_polys: List of polygon dictionaries, each containing 'points' and 'name'
        tolerance: Maximum allowed distance from simplified line in meters (default: 1000m)
    
    Returns:
        List of simplified polygon dictionaries with the same structure
    """
    simplified_polys = []
    
    for poly in catch_polys:
        points = poly['points']
        name = poly['name']
        
        # Handle closed polygons - check if first and last points are the same
        is_closed = (len(points) > 2 and 
                    abs(points[0][0] - points[-1][0]) < 1e-6 and 
                    abs(points[0][1] - points[-1][1]) < 1e-6)
        
        if is_closed:
            # For closed polygons, remove the duplicate last point before simplification
            simplified_points = ramer_douglas_peucker(points[:-1], tolerance)
            # Add the first point at the end to close the polygon again
            simplified_points.append(simplified_points[0])
        else:
            # For open polygons, simplify as-is
            simplified_points = ramer_douglas_peucker(points, tolerance)
        
        # Ensure we keep at least 3 points for a valid polygon
        if len(simplified_points) < 3:
            simplified_points = points[:3] if len(points) >= 3 else points
        
        simplified_polys.append({
            'points': simplified_points,
            'name': name
        })
    
    return simplified_polys

