"""E2E tests for the News Spark main content rendering."""

import pytest
from playwright.sync_api import Page, expect

from tests.e2e.pages.news_spark_page import NewsSparkPage

# Expected data from get_mock_data()
EXPECTED_TALKING_POINTS = 5
EXPECTED_VISUAL_TIPS = 4
EXPECTED_HASHTAGS = 7
EXPECTED_PLATFORM_VARIANTS = 3
EXPECTED_SOURCES = 3


@pytest.fixture()
def spark_page(page: Page, app_url: str) -> NewsSparkPage:
    nsp = NewsSparkPage(page, app_url)
    nsp.goto()
    return nsp


class TestPageHeader:
    """Verify the main title and subtitle render."""

    def test_main_title_visible(self, spark_page: NewsSparkPage) -> None:
        spark_page.expect_page_loaded()

    def test_main_title_text(self, spark_page: NewsSparkPage) -> None:
        expect(spark_page.main_title).to_contain_text("News Spark")

    def test_subtitle_text(self, spark_page: NewsSparkPage) -> None:
        expect(spark_page.subtitle).to_contain_text("AI 驅動的新聞分析與短片素材產生器")


class TestMetricCards:
    """Verify the 4 metric cards at the top."""

    def test_four_metric_cards_rendered(self, spark_page: NewsSparkPage) -> None:
        spark_page.expect_metric_card_count(4)

    def test_viral_score_displayed(self, spark_page: NewsSparkPage) -> None:
        first_value = spark_page.metric_values.nth(0)
        expect(first_value).to_contain_text("85%")

    def test_talking_points_count_displayed(self, spark_page: NewsSparkPage) -> None:
        second_value = spark_page.metric_values.nth(1)
        expect(second_value).to_contain_text(str(EXPECTED_TALKING_POINTS))

    def test_sources_count_displayed(self, spark_page: NewsSparkPage) -> None:
        third_value = spark_page.metric_values.nth(2)
        expect(third_value).to_contain_text(str(EXPECTED_SOURCES))

    def test_hashtags_count_displayed(self, spark_page: NewsSparkPage) -> None:
        fourth_value = spark_page.metric_values.nth(3)
        expect(fourth_value).to_contain_text(str(EXPECTED_HASHTAGS))

    def test_metric_labels(self, spark_page: NewsSparkPage) -> None:
        labels = spark_page.metric_labels
        expect(labels.nth(0)).to_contain_text("病毒傳播潛力")
        expect(labels.nth(1)).to_contain_text("重點論述")
        expect(labels.nth(2)).to_contain_text("資料來源")
        expect(labels.nth(3)).to_contain_text("Hashtags")


class TestTopicAndHook:
    """Verify topic card, title suggestion, and hook line."""

    def test_research_topic_visible(self, spark_page: NewsSparkPage) -> None:
        expect(spark_page.page.locator("text=研究主題").first).to_be_visible()

    def test_topic_text(self, spark_page: NewsSparkPage) -> None:
        expect(spark_page.page.locator("text=AI 取代工作潮").first).to_be_visible()

    def test_title_suggestion_visible(self, spark_page: NewsSparkPage) -> None:
        expect(spark_page.page.locator("text=建議標題").first).to_be_visible()

    def test_title_suggestion_content(self, spark_page: NewsSparkPage) -> None:
        expect(
            spark_page.page.locator("text=這 5 種工作即將被 AI 取代").first
        ).to_be_visible()

    def test_hook_line_box_visible(self, spark_page: NewsSparkPage) -> None:
        spark_page.expect_hook_visible()

    def test_hook_line_content(self, spark_page: NewsSparkPage) -> None:
        expect(spark_page.hook_box).to_contain_text("40% 的工作將被 AI 取代")

    def test_target_emotion_tag(self, spark_page: NewsSparkPage) -> None:
        expect(spark_page.emotion_tag).to_be_visible()
        expect(spark_page.emotion_tag).to_contain_text("焦慮轉希望")


class TestTalkingPointsAndVisuals:
    """Verify key talking points and visual suggestions."""

    def test_talking_points_count(self, spark_page: NewsSparkPage) -> None:
        expect(spark_page.talking_points).to_have_count(EXPECTED_TALKING_POINTS)

    def test_first_talking_point_content(self, spark_page: NewsSparkPage) -> None:
        expect(spark_page.talking_points.first).to_contain_text("OpenAI 最新報告")

    def test_last_talking_point_content(self, spark_page: NewsSparkPage) -> None:
        expect(spark_page.talking_points.last).to_contain_text("成功案例")

    def test_visual_tips_count(self, spark_page: NewsSparkPage) -> None:
        expect(spark_page.visual_tips).to_have_count(EXPECTED_VISUAL_TIPS)

    def test_visual_tips_content(self, spark_page: NewsSparkPage) -> None:
        expect(spark_page.visual_tips.first).to_contain_text("開場")
        expect(spark_page.visual_tips.last).to_contain_text("結尾")


class TestCTAAndHashtags:
    """Verify CTA box and hashtag chips."""

    def test_cta_box_visible(self, spark_page: NewsSparkPage) -> None:
        expect(spark_page.cta_box).to_be_visible()

    def test_cta_content(self, spark_page: NewsSparkPage) -> None:
        expect(spark_page.cta_box).to_contain_text("追蹤我")

    def test_hashtag_count(self, spark_page: NewsSparkPage) -> None:
        expect(spark_page.hashtag_tags).to_have_count(EXPECTED_HASHTAGS)

    def test_specific_hashtags_present(self, spark_page: NewsSparkPage) -> None:
        tags_container = spark_page.page.locator(".tag")
        expect(tags_container.filter(has_text="#AI取代工作").first).to_be_visible()
        expect(tags_container.filter(has_text="#ChatGPT").first).to_be_visible()
        expect(tags_container.filter(has_text="#2025趨勢").first).to_be_visible()


class TestPlatformVariants:
    """Verify platform-specific variant cards."""

    def test_platform_cards_count(self, spark_page: NewsSparkPage) -> None:
        expect(spark_page.platform_cards).to_have_count(EXPECTED_PLATFORM_VARIANTS)

    def test_tiktok_variant(self, spark_page: NewsSparkPage) -> None:
        tiktok = spark_page.platform_cards.nth(0)
        expect(tiktok).to_contain_text("TikTok")
        expect(tiktok).to_contain_text("60 秒")
        expect(tiktok).to_contain_text("9:16")

    def test_youtube_shorts_variant(self, spark_page: NewsSparkPage) -> None:
        yt = spark_page.platform_cards.nth(1)
        expect(yt).to_contain_text("YouTube Shorts")
        expect(yt).to_contain_text("≤60 秒")

    def test_instagram_reels_variant(self, spark_page: NewsSparkPage) -> None:
        ig = spark_page.platform_cards.nth(2)
        expect(ig).to_contain_text("Instagram Reels")
        expect(ig).to_contain_text("30-90 秒")

    def test_platform_tips_rendered(self, spark_page: NewsSparkPage) -> None:
        """Each platform card has a list of tips."""
        for i in range(EXPECTED_PLATFORM_VARIANTS):
            card = spark_page.platform_cards.nth(i)
            tips = card.locator("li")
            expect(tips).to_have_count(4)


class TestDataSources:
    """Verify data source section."""

    def test_sources_count(self, spark_page: NewsSparkPage) -> None:
        expect(spark_page.source_items).to_have_count(EXPECTED_SOURCES)

    def test_source_types_present(self, spark_page: NewsSparkPage) -> None:
        types = spark_page.source_types
        expect(types).to_have_count(EXPECTED_SOURCES)

    def test_news_source(self, spark_page: NewsSparkPage) -> None:
        expect(
            spark_page.source_items.filter(has_text="OpenAI 發布 GPT-5").first
        ).to_be_visible()

    def test_forum_source(self, spark_page: NewsSparkPage) -> None:
        expect(
            spark_page.source_items.filter(has_text="PTT 熱議").first
        ).to_be_visible()

    def test_social_source(self, spark_page: NewsSparkPage) -> None:
        expect(
            spark_page.source_items.filter(has_text="LinkedIn").first
        ).to_be_visible()

    def test_source_type_badges(self, spark_page: NewsSparkPage) -> None:
        expect(spark_page.source_types.nth(0)).to_contain_text("新聞")
        expect(spark_page.source_types.nth(1)).to_contain_text("論壇")
        expect(spark_page.source_types.nth(2)).to_contain_text("社群")
