from unittest.mock import MagicMock, AsyncMock, patch
import pytest
from sqlalchemy.orm import Session
from my_app.services.product_service import ProductService
from my_app.models.product import Product
from my_app.schemas.product import (
    ProductCreate,
    ProductUpdate,
    Product as ProductSchema,
)
from my_app.models.shop import ShopifyUser

"""
Comprehensive tests for the ProductService layer.

This test suite covers all methods in ProductService, ensuring that the business logic,
database interactions (via mocking the CRUD layer), and external API calls (Shopify)
are handled correctly.
"""


@pytest.fixture
def mock_db_session() -> MagicMock:
    """Provides a MagicMock for the SQLAlchemy Session."""
    db = MagicMock(spec=Session)
    # Mock the relationship to avoid errors when accessing product.shop.shop_domain
    db.query.return_value.filter.return_value.first.return_value.shop = MagicMock(
        spec=ShopifyUser
    )
    return db


@pytest.fixture
def mock_product_model() -> Product:
    """Provides a mock Product SQLAlchemy model instance."""
    product = MagicMock(spec=Product)
    product.id = 1
    product.shopify_product_id = "101"
    product.title = "Test Product"
    product.body_html = "A test product."
    product.shop_id = 1
    # Mock the shop relationship
    mock_shop = MagicMock(spec=ShopifyUser)
    mock_shop.shop_domain = "test-shop.myshopify.com"
    mock_shop.access_token = "test_access_token"
    product.shop = mock_shop
    return product


@pytest.fixture
async def product_service(mock_db_session: MagicMock) -> ProductService:
    """
    Provides a ProductService instance with a mocked DB and httpx.AsyncClient.
    This is an async fixture to allow for proper cleanup of the http client.
    """
    with patch(
        "my_app.services.product_service.httpx.AsyncClient", new_callable=AsyncMock
    ) as MockAsyncClient:
        service = ProductService(db=mock_db_session)
        # The service creates its own client, so we replace it after initialization
        service._http_client = MockAsyncClient
        yield service
        await service.close()


@patch("my_app.services.product_service.product_crud")
class TestProductService:
    """Test suite for the ProductService."""

    async def test_create_product(
        self,
        mock_crud: MagicMock,
        product_service: ProductService,
        mock_product_model: Product,
    ):
        """
        Tests that create_product correctly calls the CRUD layer with the right data.
        """
        product_data = ProductCreate(
            shopify_product_id="12345",
            shop_id=1,
            title="Test Product",
            body_html="A new product.",
        )
        mock_crud.create_product.return_value = mock_product_model

        result = product_service.create_product(product_data=product_data)

        mock_crud.create_product.assert_called_once_with(
            product_service.db, product_data
        )
        assert result == mock_product_model

    async def test_get_product(
        self,
        mock_crud: MagicMock,
        product_service: ProductService,
        mock_product_model: Product,
    ):
        """
        Tests that get_product retrieves a product by its ID via the CRUD layer.
        """
        mock_crud.get_product.return_value = mock_product_model

        result = product_service.get_product(product_id=1)

        mock_crud.get_product.assert_called_once_with(product_service.db, product_id=1)
        assert result == mock_product_model

    async def test_list_products(
        self,
        mock_crud: MagicMock,
        product_service: ProductService,
        mock_product_model: Product,
    ):
        """
        Tests that list_products retrieves a list of products via the CRUD layer.
        """
        mock_crud.get_products.return_value = [mock_product_model]

        result = product_service.list_products(skip=0, limit=10)

        mock_crud.get_products.assert_called_once_with(
            product_service.db, skip=0, limit=10
        )
        assert result == [mock_product_model]

    async def test_update_product(
        self,
        mock_crud: MagicMock,
        product_service: ProductService,
        mock_product_model: Product,
    ):
        """
        Tests that update_product correctly calls the CRUD layer to update a product.
        """
        product_update_data = ProductUpdate(body_html="New updated description.")
        mock_crud.get_product.return_value = mock_product_model
        mock_crud.update_product.return_value = mock_product_model

        result = product_service.update_product(
            product_id=1, product_update=product_update_data
        )

        mock_crud.get_product.assert_called_once_with(product_service.db, product_id=1)
        mock_crud.update_product.assert_called_once_with(
            db=product_service.db,
            db_product=mock_product_model,
            product_in=product_update_data,
        )
        assert result == mock_product_model

    async def test_delete_product(
        self,
        mock_crud: MagicMock,
        product_service: ProductService,
        mock_product_model: Product,
    ):
        """
        Tests that delete_product correctly calls the CRUD layer to delete a product.
        """
        mock_crud.delete_product.return_value = mock_product_model

        result = product_service.delete_product(product_id=1)

        mock_crud.delete_product.assert_called_once_with(
            product_service.db, product_id=1
        )
        assert result == mock_product_model

    async def test_update_product_description_in_shopify(
        self,
        mock_crud: MagicMock,
        product_service: ProductService,
        mock_product_model: Product,
    ):
        """
        Tests updating a product's description in Shopify via an API call.
        """
        new_description = "This is the updated product description."
        mock_crud.get_product.return_value = mock_product_model

        # Mock the response from the Shopify API
        mock_response = AsyncMock()
        mock_response.raise_for_status = MagicMock()

        # This is the expected JSON structure from Shopify's Product API
        shopify_response_json = {
            "product": {
                "id": 101,
                "shop_id": 1,
                "shopify_product_id": "101",
                "title": "Test Product",
                "body_html": new_description,
                "created_at": "2024-01-01T00:00:00+00:00",
                "updated_at": "2024-01-01T00:00:00+00:00",
            }
        }
        mock_response.json = AsyncMock(return_value=shopify_response_json)
        product_service._http_client.put = AsyncMock(return_value=mock_response)

        # Call the service method
        result = await product_service.update_product_description_in_shopify(
            product_id=1, new_description=new_description
        )

        # Assert the result
        assert result == ProductSchema.model_validate(shopify_response_json["product"])
