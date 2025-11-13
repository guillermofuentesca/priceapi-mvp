"""
Sistema simplificado de URLs
TODOS los tiers reciben URLs limpias (sin affiliate tags)
"""
from typing import Optional, Tuple, Dict
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse


def remove_all_tracking(url: str) -> str:
    """
    Limpia URL de cualquier parámetro de tracking
    
    Args:
        url: URL del producto
        
    Returns:
        URL limpia sin parámetros de tracking
    """
    if not url:
        return ""
    
    parsed = urlparse(url)
    query_params = parse_qs(parsed.query)
    
    # Remover parámetros de tracking comunes
    tracking_params = ['tag', 'ref', 'ref_', 'psc', 'qid', 'sr', 'keywords']
    for param in tracking_params:
        query_params.pop(param, None)
    
    # Reconstruir URL limpia
    new_query = urlencode(query_params, doseq=True) if query_params else ""
    clean_url = urlunparse((
        parsed.scheme,
        parsed.netloc,
        parsed.path,
        parsed.params,
        new_query,
        parsed.fragment
    ))
    
    return clean_url


def get_clean_url(product_url: str, tier: str) -> Tuple[str, Dict]:
    """
    Retorna URL limpia para cualquier tier
    
    Args:
        product_url: URL original del producto
        tier: Tier del usuario
        
    Returns:
        (url_limpia, metadata)
    """
    if not product_url:
        return "", {
            "tier": tier,
            "url_type": "clean",
            "commission_strategy": "Developer earns 100%"
        }
    
    clean_url = remove_all_tracking(product_url)
    
    metadata = {
        "tier": tier,
        "url_type": "clean",
        "commission_strategy": "Developer earns 100% - add your own affiliate tag",
        "why": "We believe in developer success. You keep all commissions."
    }
    
    return clean_url, metadata


# Tier info simplificado
TIER_INFO = {
    "free": {
        "requests": 500,
        "description": "Start earning affiliate commissions immediately"
    },
    "starter": {
        "requests": 10000,
        "description": "Scale your affiliate business"
    },
    "professional": {
        "requests": 50000,
        "description": "Professional-grade price intelligence"
    },
    "business": {
        "requests": 250000,
        "description": "Enterprise-scale operations"
    },
    "enterprise": {
        "requests": "unlimited",
        "description": "Custom solutions"
    }
}


def get_tier_info(tier: str) -> dict:
    """Obtiene información sobre un tier"""
    return TIER_INFO.get(tier, TIER_INFO["free"])