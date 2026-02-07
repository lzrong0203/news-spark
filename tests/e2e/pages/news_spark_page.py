"""Page Object Model for the News Spark Streamlit app."""

from playwright.sync_api import Page, expect


class NewsSparkPage:
    """Page object encapsulating the News Spark Streamlit UI."""

    def __init__(self, page: Page, base_url: str) -> None:
        self.page = page
        self.base_url = base_url

    # ── Navigation ──────────────────────────────────────────────

    def goto(self) -> None:
        """Navigate to the app and wait for Streamlit to finish rendering."""
        self.page.goto(self.base_url)
        # Wait for Streamlit's main container to be present
        self.page.wait_for_selector(
            "[data-testid='stAppViewContainer']", timeout=30_000
        )
        # Give Streamlit time to finish rendering custom HTML
        self.page.wait_for_load_state("networkidle")

    # ── Sidebar locators ────────────────────────────────────────

    @property
    def sidebar(self):
        return self.page.locator("[data-testid='stSidebar']")

    @property
    def topic_input(self):
        return self.sidebar.locator("input[type='text']").first

    @property
    def analyze_button(self):
        return self.sidebar.get_by_role("button", name="開始分析")

    @property
    def platform_multiselect(self):
        return self.sidebar.locator("[data-testid='stMultiSelect']")

    # ── Main content locators ───────────────────────────────────

    @property
    def main_title(self):
        return self.page.locator(".main-title")

    @property
    def subtitle(self):
        return self.page.locator(".subtitle")

    @property
    def metric_cards(self):
        return self.page.locator(".metric-card")

    @property
    def metric_values(self):
        return self.page.locator(".metric-value")

    @property
    def metric_labels(self):
        return self.page.locator(".metric-label")

    @property
    def cards(self):
        return self.page.locator(".card")

    @property
    def card_titles(self):
        return self.page.locator(".card-title")

    @property
    def hook_box(self):
        return self.page.locator(".hook-box")

    @property
    def talking_points(self):
        return self.page.locator(".talking-point")

    @property
    def visual_tips(self):
        return self.page.locator(".visual-tip")

    @property
    def cta_box(self):
        return self.page.locator(".cta-box")

    @property
    def hashtag_tags(self):
        return self.page.locator(".tag:not(.tag-emotion)")

    @property
    def emotion_tag(self):
        return self.page.locator(".tag-emotion")

    @property
    def platform_cards(self):
        return self.page.locator(".platform-card")

    @property
    def source_items(self):
        return self.page.locator(".source-item")

    @property
    def source_types(self):
        return self.page.locator(".source-type")

    # ── Assertions ──────────────────────────────────────────────

    def expect_page_loaded(self) -> None:
        """Assert the page rendered its main title and subtitle."""
        expect(self.main_title).to_be_visible()
        expect(self.subtitle).to_be_visible()

    def expect_metric_card_count(self, count: int) -> None:
        expect(self.metric_cards).to_have_count(count)

    def expect_hook_visible(self) -> None:
        expect(self.hook_box).to_be_visible()
