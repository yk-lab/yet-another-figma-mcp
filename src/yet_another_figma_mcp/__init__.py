"""YetAnotherFigmaMCP - Figma ファイルをローカルキャッシュし MCP サーバーとして提供"""

__all__ = ["__version__"]

try:
    from yet_another_figma_mcp._version import __version__
except ImportError:
    __version__ = "0.0.0+unknown"
