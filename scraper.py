"""
Servicio de scraping usando Rainforest API
Gestiona las llamadas a la API externa y el parseo de datos
"""
import logging
import httpx
from typing import Optional, Dict, Any, List
from datetime import datetime
from config import settings

logger = logging.getLogger(__name__)


class RainforestAPIError(Exception):
    """Excepción personalizada para errores de Rainforest API"""
    pass


class RateLimitError(RainforestAPIError):
    """Excepción cuando se excede el rate limit"""
    pass


class RainforestScraper:
    """Cliente para interactuar con Rainforest API"""
    
    def __init__(self):
        self.api_key = settings.RAINFOREST_API_KEY
        self.base_url = settings.RAINFOREST_BASE_URL
        self.timeout = settings.SCRAPE_TIMEOUT
        
        if not self.api_key:
            logger.warning("⚠️ RAINFOREST_API_KEY no configurada. Usando datos mock.")
            self.mock_mode = True
        else:
            self.mock_mode = False
    
    async def get_product(
        self, 
        asin: str, 
        country: str = "US",
        include_reviews: bool = False
    ) -> Dict[str, Any]:
        """
        Obtiene información de un producto de Amazon
        
        Args:
            asin: Amazon Standard Identification Number
            country: Código de país (US, MX, CA, UK, etc)
            include_reviews: Incluir reseñas en la respuesta
            
        Returns:
            Diccionario con información del producto
            
        Raises:
            RainforestAPIError: Si hay un error en la API
            RateLimitError: Si se excede el rate limit
        """
        if self.mock_mode:
            return self._get_mock_product(asin, country)
        
        params = {
            "api_key": self.api_key,
            "type": "product",
            "amazon_domain": self._get_amazon_domain(country),
            "asin": asin,
            "include_html": "false",
        }
        
        if include_reviews:
            params["include_reviews"] = "true"
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(self.base_url, params=params)
                
                # Manejar rate limiting
                if response.status_code == 429:
                    logger.error(f"❌ Rate limit excedido para ASIN {asin}")
                    raise RateLimitError("Se ha excedido el límite de requests a Rainforest API")
                
                # Manejar otros errores HTTP
                if response.status_code != 200:
                    logger.error(f"❌ Error {response.status_code} al obtener producto {asin}")
                    raise RainforestAPIError(f"HTTP {response.status_code}: {response.text}")
                
                data = response.json()
                
                # Validar que tengamos datos del producto
                if "product" not in data:
                    logger.error(f"❌ Respuesta inválida de Rainforest API para {asin}")
                    raise RainforestAPIError("Respuesta de API no contiene datos de producto")
                
                logger.info(f"✅ Producto {asin} obtenido exitosamente")
                return self._parse_product_response(data, country)
                
        except httpx.TimeoutException:
            logger.error(f"⏰ Timeout al obtener producto {asin}")
            raise RainforestAPIError("Timeout al conectar con Rainforest API")
        except httpx.RequestError as e:
            logger.error(f"🌐 Error de red al obtener producto {asin}: {str(e)}")
            raise RainforestAPIError(f"Error de red: {str(e)}")
    
    async def search_products(
        self, 
        query: str, 
        country: str = "US",
        page: int = 1
    ) -> List[Dict[str, Any]]:
        """
        Busca productos en Amazon
        
        Args:
            query: Término de búsqueda
            country: Código de país
            page: Número de página
            
        Returns:
            Lista de productos encontrados
        """
        if self.mock_mode:
            return self._get_mock_search_results(query, country)
        
        params = {
            "api_key": self.api_key,
            "type": "search",
            "amazon_domain": self._get_amazon_domain(country),
            "search_term": query,
            "page": page,
        }
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(self.base_url, params=params)
                
                if response.status_code == 429:
                    raise RateLimitError("Rate limit excedido")
                
                if response.status_code != 200:
                    raise RainforestAPIError(f"HTTP {response.status_code}")
                
                data = response.json()
                
                if "search_results" not in data:
                    return []
                
                logger.info(f"✅ Búsqueda '{query}' completada: {len(data['search_results'])} resultados")
                return self._parse_search_results(data["search_results"], country)
                
        except httpx.TimeoutException:
            raise RainforestAPIError("Timeout en búsqueda")
        except httpx.RequestError as e:
            raise RainforestAPIError(f"Error de red: {str(e)}")
    
    def _parse_product_response(self, data: Dict, country: str) -> Dict[str, Any]:
        """Parsea la respuesta de la API en un formato estandarizado"""
        product = data["product"]
        
        # Extraer precio (Rainforest API tiene múltiples formatos de precio)
        price_info = self._extract_price(product)
        
        return {
            "external_id": product.get("asin"),
            "name": product.get("title", ""),
            "description": product.get("description", ""),
            "category": product.get("categories_flat", ""),
            "brand": product.get("brand", ""),
            "image_url": product.get("main_image", {}).get("link"),
            "product_url": product.get("link"),
            "country": country,
            "currency": self._get_currency(country),
            "current_price": price_info.get("current_price"),
            "original_price": price_info.get("original_price"),
            "discount_percentage": price_info.get("discount_percentage"),
            "in_stock": product.get("buybox_winner", {}).get("availability", {}).get("type") == "in_stock",
            "rating": product.get("rating"),
            "ratings_total": product.get("ratings_total"),
            "scraped_at": datetime.now().isoformat(),
        }
    
    def _parse_search_results(self, results: List[Dict], country: str) -> List[Dict[str, Any]]:
        """Parsea los resultados de búsqueda"""
        parsed_results = []
        
        for item in results:
            try:
                price_info = self._extract_price(item)
                
                parsed_results.append({
                    "external_id": item.get("asin"),
                    "name": item.get("title", ""),
                    "image_url": item.get("image"),
                    "product_url": item.get("link"),
                    "country": country,
                    "currency": self._get_currency(country),
                    "current_price": price_info.get("current_price"),
                    "original_price": price_info.get("original_price"),
                    "rating": item.get("rating"),
                    "ratings_total": item.get("ratings_total"),
                })
            except Exception as e:
                logger.warning(f"⚠️ Error parseando resultado de búsqueda: {str(e)}")
                continue
        
        return parsed_results
    
    def _extract_price(self, item: Dict) -> Dict[str, Optional[float]]:
        """Extrae información de precio de un item"""
        price_info = {
            "current_price": None,
            "original_price": None,
            "discount_percentage": None,
        }
        
        # Intentar obtener precio de buybox_winner primero
        buybox = item.get("buybox_winner", {})
        
        if "price" in buybox:
            price_data = buybox["price"]
            price_info["current_price"] = price_data.get("value")
        
        # Precio original (antes de descuento)
        if "rrp" in buybox:
            price_info["original_price"] = buybox["rrp"].get("value")
        
        # Calcular descuento si hay ambos precios
        if price_info["current_price"] and price_info["original_price"]:
            discount = (1 - price_info["current_price"] / price_info["original_price"]) * 100
            price_info["discount_percentage"] = round(discount, 2)
        
        # Fallback: intentar obtener precio directo
        if not price_info["current_price"] and "price" in item:
            price_info["current_price"] = item["price"].get("value")
        
        return price_info
    
    def _get_amazon_domain(self, country: str) -> str:
        """Retorna el dominio de Amazon según el país"""
        domains = {
            "US": "amazon.com",
            "MX": "amazon.com.mx",
            "CA": "amazon.ca",
            "UK": "amazon.co.uk",
            "DE": "amazon.de",
            "FR": "amazon.fr",
            "IT": "amazon.it",
            "ES": "amazon.es",
            "JP": "amazon.co.jp",
            "IN": "amazon.in",
            "BR": "amazon.com.br",
        }
        return domains.get(country.upper(), "amazon.com")
    
    def _get_currency(self, country: str) -> str:
        """Retorna la moneda según el país"""
        currencies = {
            "US": "USD",
            "MX": "MXN",
            "CA": "CAD",
            "UK": "GBP",
            "DE": "EUR",
            "FR": "EUR",
            "IT": "EUR",
            "ES": "EUR",
            "JP": "JPY",
            "IN": "INR",
            "BR": "BRL",
        }
        return currencies.get(country.upper(), "USD")
    
    # ========== MOCK DATA (para desarrollo sin API key) ==========
    
    def _get_mock_product(self, asin: str, country: str) -> Dict[str, Any]:
        """Retorna datos mock de un producto"""
        logger.info(f"📦 Retornando datos MOCK para ASIN: {asin}")
        
        mock_products = {
            "B08N5WRWNW": {
                "name": "iPhone 13 Pro 128GB",
                "brand": "Apple",
                "current_price": 999.99,
                "category": "Electronics > Cell Phones",
            },
            "B09V3KXJPB": {
                "name": "MacBook Air M2 13-inch",
                "brand": "Apple",
                "current_price": 1199.00,
                "category": "Electronics > Computers",
            },
        }
        
        product = mock_products.get(asin, {
            "name": f"Mock Product {asin}",
            "brand": "Mock Brand",
            "current_price": 299.99,
            "category": "Electronics",
        })
        
        return {
            "external_id": asin,
            "name": product["name"],
            "brand": product["brand"],
            "description": f"This is a mock description for {product['name']}",
            "category": product.get("category", "Electronics"),
            "image_url": f"https://via.placeholder.com/300?text={product['name']}",
            "product_url": f"https://amazon.com/dp/{asin}",
            "country": country,
            "currency": self._get_currency(country),
            "current_price": product["current_price"],
            "original_price": product["current_price"] * 1.2,
            "discount_percentage": 16.67,
            "in_stock": True,
            "rating": 4.5,
            "ratings_total": 1234,
            "scraped_at": datetime.now().isoformat(),
        }
    
    def _get_mock_search_results(self, query: str, country: str) -> List[Dict[str, Any]]:
        """Retorna resultados mock de búsqueda"""
        logger.info(f"🔍 Retornando búsqueda MOCK para: {query}")
        
        return [
            {
                "external_id": "B08N5WRWNW",
                "name": "iPhone 13 Pro - Mock Result",
                "image_url": "https://via.placeholder.com/300",
                "product_url": "https://amazon.com/dp/B08N5WRWNW",
                "country": country,
                "currency": self._get_currency(country),
                "current_price": 999.99,
                "rating": 4.7,
                "ratings_total": 5432,
            },
            {
                "external_id": "B09V3KXJPB",
                "name": "MacBook Air M2 - Mock Result",
                "image_url": "https://via.placeholder.com/300",
                "product_url": "https://amazon.com/dp/B09V3KXJPB",
                "country": country,
                "currency": self._get_currency(country),
                "current_price": 1199.00,
                "rating": 4.8,
                "ratings_total": 3210,
            },
        ]


# ========== INSTANCIA GLOBAL ==========

scraper = RainforestScraper()


# ========== FUNCIONES HELPER ==========

async def get_product_price(asin: str, country: str = "US") -> Optional[Dict[str, Any]]:
    """
    Función helper para obtener el precio de un producto
    Incluye manejo de errores y logging
    """
    try:
        product_data = await scraper.get_product(asin, country)
        return product_data
    except RateLimitError:
        logger.error("⏱️ Rate limit excedido. Considera usar caché o esperar.")
        return None
    except RainforestAPIError as e:
        logger.error(f"❌ Error de Rainforest API: {str(e)}")
        return None


async def search_amazon_products(query: str, country: str = "US") -> List[Dict[str, Any]]:
    """Función helper para búsqueda de productos"""
    try:
        results = await scraper.search_products(query, country)
        return results
    except RateLimitError:
        logger.error("⏱️ Rate limit excedido en búsqueda")
        return []
    except RainforestAPIError as e:
        logger.error(f"❌ Error en búsqueda: {str(e)}")
        return []
