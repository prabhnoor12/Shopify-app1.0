import pytest
from unittest.mock import MagicMock, patch
from sqlalchemy.orm import Session
from openai import OpenAI
import httpx
from fastapi import HTTPException
import datetime

# Import all necessary models to resolve SQLAlchemy relationships for the test session
from my_app.models.shop import ShopifyUser
from my_app.models.brand_voice import BrandVoice
from my_app.services.shop_service import ShopifyService, retry_sync, MAX_RETRIES
from my_app.schemas.shop import (
    GenerateRequest,
    SaveRequest,
    BulkSaveRequest,
    BulkFindReplaceRequest,
    GenerateFromImageRequest,
    GenerateFromUrlRequest,
    RegenerateVariantRequest,
    BenefitOrientedRequest,
    BulkGenerateRequest,
    GenerateResponse,
    SEOAnalysis,
    SEOCheck,
)
from my_app.dependencies.config import settings

# Mark all tests in this file as synchronous
pytestmark = pytest.mark.usefixtures("db_session", "mock_openai_client", "mock_user")



@pytest.fixture
@patch("my_app.services.shop_service.httpx.Client")
def shopify_service(MockClient, db_session, mock_openai_client):
    """Fixture for an instance of ShopifyService with mocked dependencies."""
    # Mock the instance of the client, not the class
    mock_http_client_instance = MockClient.return_value
    mock_http_client_instance.get = MagicMock()
    mock_http_client_instance.put = MagicMock()

    service = ShopifyService(db=db_session, openai_client=mock_openai_client)
    # Replace the client created in __init__ with our mock instance
    service._http_client = mock_http_client_instance
    return service


class TestShopifyService:
    def test_parse_generation_choice(self, shopify_service: ShopifyService):
        """Tests the JSON parsing of OpenAI responses."""
        # Test successful parsing
        valid_json = """{"description": "Test Desc", "keywords": ["a", "b"], "meta_title": "Test Title", "meta_description": "Test Meta"}"""
        mock_choice_ok = MagicMock(message=MagicMock(content=valid_json))
        parsed = shopify_service._parse_generation_choice(mock_choice_ok)
        assert parsed["description"] == "Test Desc"
        assert parsed["keywords"] == ["a", "b"]

        # Test fallback on malformed JSON
        invalid_json = "Just a string, not JSON"
        mock_choice_fail = MagicMock(message=MagicMock(content=invalid_json))
        parsed_fail = shopify_service._parse_generation_choice(mock_choice_fail)
        assert parsed_fail["description"] == "Just a string, not JSON"
        assert parsed_fail["keywords"] == []

    def test_close_method(self, shopify_service: ShopifyService):
        """Tests that the close method calls the http client's close method."""
        shopify_service.close()
        shopify_service._http_client.close.assert_called_once()

    def test_fetch_orders_for_product(
        self, shopify_service: ShopifyService, mock_user: ShopifyUser
    ):
        """Tests fetching orders for a specific product."""
        mock_response = MagicMock(spec=httpx.Response)
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "orders": [{"id": 101, "total_price": "100.00"}]
        }
        shopify_service._http_client.get.return_value = mock_response

        orders = shopify_service.fetch_orders_for_product(mock_user, product_id=1)

        assert len(orders) == 1
        assert orders[0]["id"] == 101
        shopify_service._http_client.get.assert_called_once()
        assert (
            "products/1/orders.json" in shopify_service._http_client.get.call_args[0][0]
        )

    def test_generate_description_from_image(
        self, shopify_service: ShopifyService, mock_user: ShopifyUser, db_session
    ):
        """Tests generating a description from an image URL."""
        mock_openai_response = MagicMock()
        mock_openai_response.choices = [
            MagicMock(
                message=MagicMock(
                    content='{"description": "A description from an image."}'
                )
            )
        ]
        shopify_service.openai_client.chat.completions.create.return_value = (
            mock_openai_response
        )

        req = GenerateFromImageRequest(
            image_url="http://example.com/image.jpg",
            num_variants=1,
            tone="Friendly",
            length="Medium",
        )
        response = shopify_service.generate_description_from_image(mock_user, req)

        assert response.descriptions[0] == "A description from an image."
        shopify_service.openai_client.chat.completions.create.assert_called_once()
        # Verify that the model used is the vision model
        assert (
            shopify_service.openai_client.chat.completions.create.call_args.kwargs[
                "model"
            ]
            == "gpt-4-vision-preview"
        )
        # db_session.commit.assert_called_once()

    def test_bulk_generate_descriptions(
        self, shopify_service: ShopifyService, mock_user: ShopifyUser
    ):
        """Tests bulk generation with a mix of success and failure."""
        product1 = {"product_id": 1, "title": "P1"}
        product2 = {"product_id": 2, "title": "P2"}
        req = BulkGenerateRequest(
            products=[product1, product2],
            tone="Friendly",
            length="Medium",
            num_variants=1,
        )

        with patch.object(shopify_service, "generate_description") as mock_generate:
            mock_generate.side_effect = [
                GenerateResponse(product_id=1, descriptions=["Desc 1"], keywords=[]),
                Exception("Generation failed"),
            ]
            response = shopify_service.bulk_generate_descriptions(mock_user, req)

            assert len(response.results) == 1
            assert response.results[0].descriptions == ["Desc 1"]
            assert response.errors == [2]
            assert mock_generate.call_count == 2

    def test_generate_description_from_url(
        self, shopify_service: ShopifyService, mock_user: ShopifyUser, db_session
    ):
        """Tests generating a description by scraping a URL."""
        # Mock the HTTP GET call to the external URL
        mock_url_response = MagicMock(spec=httpx.Response)
        mock_url_response.status_code = 200
        mock_url_response.text = (
            "<html><body><h1>Title</h1><p>Some content.</p></body></html>"
        )
        shopify_service._http_client.get.return_value = mock_url_response

        # Mock the OpenAI call
        mock_openai_response = MagicMock()
        mock_openai_response.choices = [
            MagicMock(
                message=MagicMock(
                    content='{"description": "A description from a URL."}'
                )
            )
        ]
        shopify_service.openai_client.chat.completions.create.return_value = (
            mock_openai_response
        )

        req = GenerateFromUrlRequest(
            url="http://example.com",
            num_variants=1,
            title="Example",
            tone="Neutral",
            length="Medium",
        )
        response = shopify_service.generate_description_from_url(mock_user, req)

        assert response.descriptions[0] == "A description from a URL."
        # Ensure both the URL fetch and the OpenAI call were made
        shopify_service._http_client.get.assert_called_once_with(
            req.url, timeout=settings.REQUEST_TIMEOUT
        )
        shopify_service.openai_client.chat.completions.create.assert_called_once()
        # db_session.commit.assert_called_once()

    def test_regenerate_variant(
        self, shopify_service: ShopifyService, mock_user: ShopifyUser, db_session
    ):
        """Tests regenerating a single variant based on feedback."""
        mock_openai_response = MagicMock()
        mock_openai_response.choices = [
            MagicMock(
                message=MagicMock(
                    content='{"description": "A regenerated description."}'
                )
            )
        ]
        shopify_service.openai_client.chat.completions.create.return_value = (
            mock_openai_response
        )

        req = RegenerateVariantRequest(
            product_id=1,
            original_description="Old desc",
            feedback="Make it better",
            tone="More exciting",
            length="Longer",
        )
        response = shopify_service.regenerate_variant(mock_user, req)

        assert response.descriptions[0] == "A regenerated description."
        shopify_service.openai_client.chat.completions.create.assert_called_once()
        # db_session.commit.assert_called_once()

    def test_transform_feature_to_benefit(
        self, shopify_service: ShopifyService, mock_user: ShopifyUser, db_session
    ):
        """Tests the feature-to-benefit transformation."""
        mock_openai_response = MagicMock()
        mock_openai_response.choices = [
            MagicMock(
                message=MagicMock(
                    content='{"benefit_text": "This feature saves you time."}'
                )
            )
        ]
        shopify_service.openai_client.chat.completions.create.return_value = (
            mock_openai_response
        )

        req = BenefitOrientedRequest(
            text="It has a 1-click operation.", product_title="Easy-Use Gadget"
        )
        response = shopify_service.transform_feature_to_benefit(mock_user, req)

        assert response.benefit_text == "This feature saves you time."
        shopify_service.openai_client.chat.completions.create.assert_called_once()
        # db_session.commit.assert_called_once()

    def test_fetch_products_with_pagination(
        self, shopify_service: ShopifyService, mock_user: ShopifyUser
    ):
        """Tests successful fetching of products with pagination."""
        # Mock first page response
        mock_response_page1 = MagicMock(spec=httpx.Response)
        mock_response_page1.status_code = 200
        mock_response_page1.json.return_value = {
            "products": [{"id": 1, "title": "Product A"}]
        }
        # The Link header points to the next page
        next_page_url = f"https://{mock_user.shop_domain}/admin/api/{settings.SHOPIFY_API_VERSION}/products.json?page_info=next_page_token"
        mock_response_page1.headers = {"Link": f'<{next_page_url}>; rel="next"'}

        # Mock second page response
        mock_response_page2 = MagicMock(spec=httpx.Response)
        mock_response_page2.status_code = 200
        mock_response_page2.json.return_value = {
            "products": [{"id": 2, "title": "Product B"}]
        }
        mock_response_page2.headers = {}  # No Link header on the last page

        # Set the side_effect to return page 1, then page 2
        shopify_service._http_client.get.side_effect = [
            mock_response_page1,
            mock_response_page2,
        ]

        products = shopify_service.fetch_products(mock_user)

        assert len(products) == 2
        assert products[0]["title"] == "Product A"
        assert products[1]["title"] == "Product B"
        assert shopify_service._http_client.get.call_count == 2

    def test_get_brand_voice_prompt(
        self, shopify_service: ShopifyService, mock_user: ShopifyUser, db_session
    ):
        """Tests the private method for getting the brand voice prompt."""
        mock_brand_voice = BrandVoice(
            tone_of_voice="Witty",
            vocabulary_preferences={"preferred": ["innovative"], "avoid": ["standard"]},
            shop_id=mock_user.id,
        )
        db_session.add(mock_brand_voice)
        db_session.commit()

        prompt = shopify_service._get_brand_voice_prompt(mock_user)
        assert "Witty" in prompt
        assert "Preferred vocabulary: innovative" in prompt
        assert "Avoid using: standard" in prompt

    def test_save_description_header_fix(
        self, shopify_service: ShopifyService, mock_user: ShopifyUser
    ):
        """Tests that the correct Shopify access token header is used."""
        mock_response = MagicMock(spec=httpx.Response)
        mock_response.status_code = 200
        shopify_service._http_client.put.return_value = mock_response

        req = SaveRequest(product_id=123, new_description="Test")
        shopify_service.save_description(mock_user, req)

        call_args = shopify_service._http_client.put.call_args
        assert "X-Shopify-Access-Token" in call_args.kwargs["headers"]
        assert "X-Shopif-Access-Token" not in call_args.kwargs["headers"]

    def test_bulk_find_and_replace_regex_and_pagination(
        self, shopify_service: ShopifyService, mock_user: ShopifyUser
    ):
        """
        Tests the bulk find and replace functionality, including regex matching,
        case-insensitivity, whole-word matching, and pagination.
        """
        # Mock product pages
        mock_response_page1 = MagicMock(spec=httpx.Response)
        mock_response_page1.status_code = 200
        mock_response_page1.json.return_value = {
            "products": [
                {"id": 1, "body_html": "This is an old product."},
                {"id": 2, "body_html": "This is an OLDER product, very old."},
            ]
        }
        next_page_url = f"https://{mock_user.shop_domain}/admin/api/{settings.SHOPIFY_API_VERSION}/products.json?page_info=token"
        mock_response_page1.headers = {"Link": f'<{next_page_url}>; rel="next"'}

        mock_response_page2 = MagicMock(spec=httpx.Response)
        mock_response_page2.status_code = 200
        mock_response_page2.json.return_value = {
            "products": [
                {"id": 3, "body_html": "This product is not old."},
            ]
        }
        mock_response_page2.headers = {}

        shopify_service._http_client.get.side_effect = [
            mock_response_page1,
            mock_response_page2,
        ]

        # Mock the save_description to inspect its calls
        with patch.object(shopify_service, "save_description") as mock_save:
            req = BulkFindReplaceRequest(
                find_text="old",
                replace_text="new",
                is_case_sensitive=False,
                is_whole_word=True,
                is_regex=True,
            )
            response = shopify_service.bulk_find_and_replace(mock_user, req)

            assert response.total_matches == 3
            assert len(response.updated_products) == 3
            assert response.errors == []

            # Check that save was called with the correct replacements
            assert mock_save.call_count == 3

            # We need to check the calls with SaveRequest objects
            from my_app.schemas.shop import SaveRequest
            from unittest.mock import call

            calls = [
                call(
                    mock_user,
                    SaveRequest(
                        product_id=1, new_description="This is an new product."
                    ),
                ),
                call(
                    mock_user,
                    SaveRequest(
                        product_id=2,
                        new_description="This is an OLDER product, very new.",
                    ),
                ),
                call(
                    mock_user,
                    SaveRequest(
                        product_id=3, new_description="This product is not new."
                    ),
                ),
            ]
            mock_save.assert_has_calls(calls, any_order=True)

    def test_bulk_find_and_replace_error_reporting(
        self, shopify_service: ShopifyService, mock_user: ShopifyUser
    ):
        """Tests the improved error reporting in bulk find and replace."""
        mock_response = MagicMock(spec=httpx.Response)
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "products": [{"id": 1, "body_html": "An old product."}]
        }
        mock_response.headers = {}
        shopify_service._http_client.get.return_value = mock_response

        with patch.object(shopify_service, "save_description") as mock_save:
            mock_save.side_effect = Exception("Update failed")
            req = BulkFindReplaceRequest(find_text="old", replace_text="new")
            response = shopify_service.bulk_find_and_replace(mock_user, req)

            assert response.total_matches == 1
            assert response.updated_products == []
            assert len(response.errors) == 1
            assert response.errors[0].product_id == 1
            assert "Update failed" in response.errors[0].error

    def test_fetch_products_success(
        self, shopify_service: ShopifyService, mock_user: ShopifyUser
    ):
        """Tests successful fetching of products from Shopify."""
        mock_response = MagicMock(spec=httpx.Response)
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "products": [
                {
                    "id": 1,
                    "title": "Product A",
                    "tags": "tag1",
                    "product_type": "typeA",
                },
                {
                    "id": 2,
                    "title": "Product B",
                    "tags": "tag2",
                    "product_type": "typeB",
                },
            ]
        }
        mock_response.headers = {}
        shopify_service._http_client.get.return_value = mock_response

        products = shopify_service.fetch_products(mock_user)

        assert len(products) == 2
        assert products[0]["title"] == "Product A"
        # The call count will be 1 because pagination is not triggered
        shopify_service._http_client.get.assert_called_once()

    def test_generate_description_success(
        self, shopify_service: ShopifyService, mock_user: ShopifyUser, db_session
    ):
        """Tests successful generation of a product description."""

        mock_user.trial_ends_at = datetime.datetime.now(
            datetime.timezone.utc
        ) - datetime.timedelta(days=10)  # Trial ended
        mock_user.generations_used = 0
        # Mock BrandVoice query
        mock_brand_voice = BrandVoice(tone_of_voice="Friendly", shop_id=mock_user.id)
        db_session.add(mock_brand_voice)
        db_session.commit()
        # Mock OpenAI call
        mock_openai_response = MagicMock()
        mock_openai_response.choices = [
            MagicMock(
                message=MagicMock(
                    content="""{"description": "A friendly description.", "keywords": ["friendly", "product"], "meta_title": "Friendly Product", "meta_description": "Get this friendly product."}"""
                )
            )
        ]
        shopify_service.openai_client.chat.completions.create.return_value = (
            mock_openai_response
        )

        req = GenerateRequest(
            product_id=1,
            title="Test Product",
            tone="Professional",
            length="Short",
            num_variants=1,
        )

        with patch(
            "my_app.services.shop_service.seo_service", new_callable=MagicMock
        ) as mock_seo:
            mock_seo_analysis = SEOAnalysis(
                overall_score=85,
                checks=[
                    SEOCheck(name="Test Check", score=100, status="pass", message="OK")
                ],
            )

            mock_seo.analyze_seo.return_value = mock_seo_analysis
            mock_seo.generate_seo_improvement_suggestions.return_value = (
                "This is a suggestion."
            )

            response = shopify_service.generate_description(mock_user, req)

        assert response.descriptions[0] == "A friendly description."
        assert response.keywords == ["friendly", "product"]
        assert response.seo_analysis is not None
        assert response.seo_analysis.overall_score == 85
        assert response.seo_suggestions == "This is a suggestion."
        # Check that the brand voice prompt was used
        shopify_service.openai_client.chat.completions.create.assert_called_once()
        prompt = shopify_service.openai_client.chat.completions.create.call_args[1][
            "messages"
        ][0]["content"]
        assert "Professional" in prompt
        # db_session.commit.assert_called_once()

    def test_generate_description_limit_exceeded(
        self, shopify_service: ShopifyService, mock_user: ShopifyUser
    ):
        """Tests that generation is blocked when the monthly limit is exceeded."""
        mock_user.trial_ends_at = datetime.datetime.now(
            datetime.UTC
        ) - datetime.timedelta(days=1)  # Trial ended
        mock_user.generations_used = settings.MONTHLY_GENERATION_LIMIT

        req = GenerateRequest(
            product_id=1,
            title="Test Product",
            tone="Professional",
            length="Short",
            num_variants=1,
        )

        with pytest.raises(HTTPException) as exc_info:
            shopify_service.generate_description(mock_user, req)

        assert exc_info.value.status_code == 402

    def test_save_description_success(
        self, shopify_service: ShopifyService, mock_user: ShopifyUser
    ):
        """Tests successfully saving a product description to Shopify."""
        mock_response = MagicMock(spec=httpx.Response)
        mock_response.status_code = 200
        shopify_service._http_client.put.return_value = mock_response

        req = SaveRequest(
            product_id=123, new_description="This is the new description."
        )
        shopify_service.save_description(mock_user, req)

        shopify_service._http_client.put.assert_called_once()
        call_args = shopify_service._http_client.put.call_args
        assert (
            call_args.kwargs["json"]["product"]["body_html"]
            == "This is the new description."
        )
        # Also test the header fix here
        assert "X-Shopify-Access-Token" in call_args.kwargs["headers"]

    def test_bulk_save_descriptions(
        self, shopify_service: ShopifyService, mock_user: ShopifyUser
    ):
        """Tests bulk saving with a mix of success and failure."""
        save_req1 = SaveRequest(product_id=1, new_description="Desc 1")
        save_req2 = SaveRequest(product_id=2, new_description="Desc 2")

        # Mock the save_description method to control its behavior
        with patch.object(
            shopify_service, "save_description", new_callable=MagicMock
        ) as mock_save:
            mock_save.side_effect = [
                None,
                Exception("Failed to save"),
            ]  # First call succeeds, second fails

            response = shopify_service.bulk_save_descriptions(
                mock_user, BulkSaveRequest(requests=[save_req1, save_req2])
            )

            assert mock_save.call_count == 2
            assert response.success == [1]
            assert response.errors == [2]

    def test_retry_logic(self, mock_user: ShopifyUser):
        """Tests the @retry_sync decorator."""

        @retry_sync
        def failing_function():
            failing_function.call_count += 1
            raise httpx.RequestError("Request failed", request=MagicMock())

        failing_function.call_count = 0

        with pytest.raises(HTTPException) as exc_info:
            failing_function()

        assert exc_info.value.status_code == 500
        assert failing_function.call_count == MAX_RETRIES
