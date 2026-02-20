import ast
import logging
import re
from datetime import timedelta
from typing import List, Union

logger = logging.getLogger(__name__)


def remove_comments(text: str, comment_style: str = ";") -> str:
    # Remove single-line comments
    text = re.sub(rf"{comment_style}.*", "", text)
    # Remove multi-line comments
    # text = re.sub(r"\(\*[\s\S]*?\*\)", "", text)
    return text


def parse_timedelta(td_string: str) -> timedelta:
    result = re.match(r"(\d+(\.\d+)?)([\w]+)", td_string)
    assert result is not None, f"Invalid timedelta format: {td_string}"

    value = float(result.group(1))  # Get the numeric value
    unit = result.group(3)  # Get the unit (e.g., "s", "ms")

    if unit == "s":  # Seconds
        return timedelta(seconds=value)
    elif unit == "ms":  # Milliseconds
        return timedelta(milliseconds=value)
    else:
        raise ValueError(f"Unsupported unit: {unit}")


def wrap_code(code, lang):
    return f"```{lang}\n" + code + "\n```"


def get_markup_from_text(text: str, markup: Union[str, List[str]]) -> List[str]:
    if isinstance(markup, str):
        markup = [markup]

    markup_str = "|".join(markup)
    if markup.count("```") % 2 != 0:
        raise ValueError("Unmatched number of ``` in the text.")

    markdown_cells = [match.strip() for match in re.findall(rf"(```[\w\W]*?```)", text)]
    correct_markdown_cells = []
    for markdown_cell in markdown_cells:
        match = re.search(rf"```(?:{markup_str})?[\n\s]([\w\W]+)```", markdown_cell)
        if match is None:
            continue

        correct_markdown_cells.append(match.group(1).strip())
    return correct_markdown_cells


def snake_to_camel(snake_str: str) -> str:
    """Convert snake_case to camelCase."""
    components = snake_str.split("_")
    return components[0] + "".join(word.capitalize() for word in components[1:])


def snake_to_pascal(snake_str: str) -> str:
    """Convert snake_case to PascalCase."""
    components = snake_str.split("_")
    return "".join(word.capitalize() for word in components)


def camel_to_snake(camel_str: str) -> str:
    """Convert camelCase to snake_case."""
    return re.sub(r"(?<!^)(?=[A-Z])", "_", camel_str).lower()


def remove_docstrings(source_code: str) -> str:
    """Remove docstrings from Python source code using AST parsing."""
    try:
        tree = ast.parse(source_code)

        class DocstringRemover(ast.NodeTransformer):
            def visit_FunctionDef(self, node):
                # Remove docstring if it exists (first statement is a string)
                if (
                    node.body
                    and isinstance(node.body[0], ast.Expr)
                    and isinstance(node.body[0].value, ast.Constant)
                    and isinstance(node.body[0].value.value, str)
                ):
                    node.body = node.body[1:]
                return self.generic_visit(node)

            def visit_AsyncFunctionDef(self, node):
                # Same for async functions
                if (
                    node.body
                    and isinstance(node.body[0], ast.Expr)
                    and isinstance(node.body[0].value, ast.Constant)
                    and isinstance(node.body[0].value.value, str)
                ):
                    node.body = node.body[1:]
                return self.generic_visit(node)

            def visit_ClassDef(self, node):
                # Same for classes
                if (
                    node.body
                    and isinstance(node.body[0], ast.Expr)
                    and isinstance(node.body[0].value, ast.Constant)
                    and isinstance(node.body[0].value.value, str)
                ):
                    node.body = node.body[1:]
                return self.generic_visit(node)

        # Transform the tree
        transformer = DocstringRemover()
        new_tree = transformer.visit(tree)

        # Convert back to source code
        return ast.unparse(new_tree)
    except Exception as e:
        logger.warning(f"Failed to remove docstrings: {e}")
        return source_code


def xml_escape(text: str) -> str:
    return text.replace("&", "and")


def extract_first_skill_list(text: str):
    # Find all bullet lists (contiguous *-lines)
    lists = re.findall(r"(?:^[\* \-]+.*(?:\n[\* \-]+.*)*)", text, flags=re.MULTILINE)  # a group of consecutive *-lines

    func_regex = r"\b[\w_]+\([^)]*\)"  # matches function calls like func_name(arg1, arg2)

    if not lists:
        if re.search(func_regex, text):
            raise ValueError("No skill list found, but skills found outside of a list.")
        else:
            return []

    if len(lists) > 1:
        raise ValueError("Multiple skill lists found. Only list one list of skills below # Skill Mapping.")

    # Split the first list into lines
    first_list = lists[0].strip().splitlines()

    skills = []
    for line in first_list:
        match = re.search(func_regex, line.strip())
        if not match:
            raise ValueError(f"Malformed bullet line: {line!r}")
        skills.append(match.group())

    return skills
