"""研究工作流圖結構測試"""

from src.graph.research_graph import build_research_graph, create_research_workflow


class TestBuildResearchGraph:
    def test_graph_has_all_nodes(self):
        graph = build_research_graph()
        node_names = set(graph.nodes.keys())

        expected_nodes = {
            "supervisor",
            "news_scraper",
            "social_media",
            "deep_analyzer",
            "content_synthesizer",
            "error_handler",
        }
        assert expected_nodes.issubset(node_names)

    def test_create_workflow_compiles(self):
        workflow = create_research_workflow()
        assert workflow is not None
