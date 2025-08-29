"""
Similarity calculation utilities for BAC Hunter.
Consolidates duplicate functions used across different modules.
"""

import re
from typing import Dict, Any, List
from urllib.parse import urlparse


def calculate_url_similarity(url_a: str, url_b: str) -> float:
    """
    Calculate similarity between two URLs.
    
    Args:
        url_a: First URL to compare
        url_b: Second URL to compare
        
    Returns:
        Similarity score between 0.0 and 1.0
    """
    try:
        pa = urlparse(url_a).path.strip('/').split('/')
        pb = urlparse(url_b).path.strip('/').split('/')
    except Exception:
        pa = url_a.strip('/').split('/')
        pb = url_b.strip('/').split('/')
    
    if not pa and not pb:
        return 1.0
    
    if len(pa) != len(pb):
        # Compare only up to min length to avoid false zeros
        upto = min(len(pa), len(pb))
        if upto == 0:
            return 0.0
        matches = sum(1 for a, b in zip(pa[:upto], pb[:upto]) 
                     if a == b or (a.isdigit() and b.isdigit()))
        return matches / float(upto)
    
    matches = sum(1 for a, b in zip(pa, pb) 
                 if a == b or (a.isdigit() and b.isdigit()))
    return matches / float(len(pa) or 1)


def calculate_content_similarity(content_a: str, content_b: str) -> float:
    """
    Calculate similarity between response contents.
    
    Args:
        content_a: First content string
        content_b: Second content string
        
    Returns:
        Similarity score between 0.0 and 1.0
    """
    if content_a == content_b:
        return 1.0
    
    if not content_a or not content_b:
        return 0.0
    
    # Simple word-based similarity using Jaccard index
    words_a = set(content_a.lower().split())
    words_b = set(content_b.lower().split())
    
    union = words_a | words_b
    if not union:
        return 0.0
    
    intersection = words_a & words_b
    return len(intersection) / float(len(union))


def analyze_content_for_user_data(resp_a: Dict[str, Any], resp_b: Dict[str, Any]) -> Dict[str, Any]:
    """
    Analyze response content for user-specific data patterns.
    
    Args:
        resp_a: First response dictionary
        resp_b: Second response dictionary
        
    Returns:
        Dictionary with analysis results
    """
    content_a = resp_a.get('body', '') or ''
    content_b = resp_b.get('body', '') or ''
    
    # Look for user-specific patterns
    user_patterns = [
        r'user[_-]?id["\s:]*(\w+)',
        r'email["\s:]*([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})',
        r'name["\s:]*([A-Za-z\s]+)',
        r'account[_-]?number["\s:]*(\w+)'
    ]
    
    data_a = {}
    data_b = {}
    
    for pattern in user_patterns:
        matches_a = re.findall(pattern, content_a, re.IGNORECASE)
        matches_b = re.findall(pattern, content_b, re.IGNORECASE)
        
        if matches_a:
            data_a[pattern] = matches_a
        if matches_b:
            data_b[pattern] = matches_b
    
    # Check if data suggests different users
    suggests_cross_access = False
    if data_a and data_b:
        # If we found user data in both responses and they're different
        for pattern in user_patterns:
            if pattern in data_a and pattern in data_b:
                if data_a[pattern] != data_b[pattern]:
                    suggests_cross_access = True
                    break
    
    return {
        'suggests_cross_access': suggests_cross_access,
        'data_a': data_a,
        'data_b': data_b,
        'content_similarity': calculate_content_similarity(content_a, content_b)
    }


def analyze_id_patterns(responses: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Analyze ID patterns for predictability.
    
    Args:
        responses: List of response dictionaries
        
    Returns:
        List of findings related to ID patterns
    """
    ids = []
    
    for response in responses:
        url = response.get('url', '')
        body = response.get('body', '') or ''
        
        # Extract numeric IDs from URLs
        url_ids = re.findall(r'/(\d+)(?:/|$|\?)', url)
        ids.extend([int(id_str) for id_str in url_ids])
        
        # Extract IDs from response bodies
        body_ids = re.findall(r'(?:id|user_id|account_id)["\':\s]*(\d+)', body)
        ids.extend([int(id_str) for id_str in body_ids])
    
    if len(ids) < 3:
        return []
    
    ids.sort()
    seq = sum(1 for i in range(1, len(ids)) if ids[i] - ids[i-1] == 1)
    
    findings = []
    if seq >= 3:
        findings.append({
            'type': 'IDOR',
            'severity': 'medium',
            'title': 'Sequential ID pattern detected',
            'evidence': {'ids': ids[:10], 'sequential_count': seq}
        })
    
    return findings
