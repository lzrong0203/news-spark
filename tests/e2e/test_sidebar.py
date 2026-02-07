"""E2E tests for the News Spark sidebar inputs."""

import pytest
from playwright.sync_api import Page, expect

from tests.e2e.pages.news_spark_page import NewsSparkPage


@pytest.fixture()
def spark_page(page: Page, app_url: str) -> NewsSparkPage:
    nsp = NewsSparkPage(page, app_url)
    nsp.goto()
    return nsp


class TestSidebarRendering:
    """Verify sidebar elements render correctly on initial load."""

    def test_sidebar_is_visible(self, spark_page: NewsSparkPage) -> None:
        expect(spark_page.sidebar).to_be_visible()

    def test_topic_input_present(self, spark_page: NewsSparkPage) -> None:
        expect(spark_page.topic_input).to_be_visible()

    def test_topic_input_empty_by_default(self, spark_page: NewsSparkPage) -> None:
        expect(spark_page.topic_input).to_have_value("")

    def test_analyze_button_visible(self, spark_page: NewsSparkPage) -> None:
        expect(spark_page.analyze_button).to_be_visible()
        expect(spark_page.analyze_button).to_contain_text("開始分析")

    def test_sources_multiselect_visible(self, spark_page: NewsSparkPage) -> None:
        expect(spark_page.platform_multiselect).to_be_visible()

    def test_default_sources_selected(self, spark_page: NewsSparkPage) -> None:
        """新聞, 社群, 論壇 should be selected by default."""
        multiselect = spark_page.platform_multiselect
        expect(multiselect).to_contain_text("新聞")
        expect(multiselect).to_contain_text("社群")
        expect(multiselect).to_contain_text("論壇")

    def test_tone_slider_visible(self, spark_page: NewsSparkPage) -> None:
        expect(spark_page.sidebar).to_contain_text("內容調性")


class TestSidebarInteraction:
    """Verify sidebar inputs can be interacted with."""

    def test_can_type_topic(self, spark_page: NewsSparkPage) -> None:
        spark_page.topic_input.fill("區塊鏈")
        expect(spark_page.topic_input).to_have_value("區塊鏈")

    def test_empty_topic_shows_warning(self, spark_page: NewsSparkPage) -> None:
        spark_page.analyze_button.click()
        warning = spark_page.page.locator("[data-testid='stAlert']")
        expect(warning).to_be_visible(timeout=5_000)
