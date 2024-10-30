# parsers/parser_factory.py

from parsers.markdown_response_parser import MarkdownResponseParser
from parsers.response_parser import ResponseParser

class ParserFactory:
    @staticmethod
    def get_parser(handler_name: str, patterns_filename: str = "patterns_config.txt", mapping_filename: str = "helper_mapping.txt") -> ResponseParser:
        """
        Returns an instance of MarkdownResponseParser configured with the specified pattern and mapping files.

        Args:
            handler_name (str): The name of the handler (currently unused but can be utilized for future expansions).
            patterns_filename (str, optional): The patterns configuration file name. Defaults to "patterns_config.txt".
            mapping_filename (str, optional): The helper mappings configuration file name. Defaults to "helper_mapping.txt".

        Returns:
            ResponseParser: An instance of MarkdownResponseParser.
        """
        # Currently, handler_name is not used since all handlers use MarkdownResponseParser.
        # This can be extended in the future to support multiple parsers based on handler_name.
        return MarkdownResponseParser(patterns_filename=patterns_filename, mapping_filename=mapping_filename)
