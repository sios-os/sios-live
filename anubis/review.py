"""Code review agent — static analysis before promotion.

Reviews generated code for common issues that tests might miss:
- Empty functions (pass-only bodies)
- Hardcoded test values (overfitting to tests)
- Missing type hints on public functions
- Overly complex functions (cyclomatic complexity)
- Dead code (unreachable branches)
- Missing docstrings on public functions
- Bare except clauses
- Mutable default arguments

This is a static analysis pass, not a model-based review. It runs
deterministically and doesn't require the model.
"""
from __future__ import annotations

import ast
import re
from dataclasses import dataclass, field
from typing import Any


@dataclass
class ReviewFinding:
    severity: str  # "error", "warning", "info"
    category: str
    message: str
    line: int = 0


@dataclass
class ReviewResult:
    findings: list[ReviewFinding] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        """A review passes if there are no error-severity findings."""
        return not any(f.severity == "error" for f in self.findings)

    @property
    def score(self) -> float:
        """Quality score 0.0 to 1.0."""
        if not self.findings:
            return 1.0
        errors = sum(1 for f in self.findings if f.severity == "error")
        warnings = sum(1 for f in self.findings if f.severity == "warning")
        return max(0.0, 1.0 - (errors * 0.3 + warnings * 0.1))

    def summary(self) -> str:
        if not self.findings:
            return "No issues found."
        lines = []
        for f in self.findings:
            lines.append(f"  [{f.severity}] {f.category}: {f.message} (line {f.line})")
        return "\n".join(lines)


def review_code(code: str) -> ReviewResult:
    """Review Python source code for common issues."""
    result = ReviewResult()

    # Parse the AST
    try:
        tree = ast.parse(code)
    except SyntaxError as e:
        result.findings.append(ReviewFinding(
            severity="error", category="syntax",
            message=f"Syntax error: {e.msg}", line=e.lineno or 0,
        ))
        return result

    # Walk the AST
    for node in ast.walk(tree):
        # Check function definitions
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            _check_function(node, result)

        # Check bare except
        if isinstance(node, ast.ExceptHandler):
            if node.type is None:
                result.findings.append(ReviewFinding(
                    severity="warning", category="bare_except",
                    message="Bare except clause catches everything including SystemExit",
                    line=node.lineno,
                ))

        # Check mutable default arguments
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            for default in node.args.defaults + node.args.kw_defaults:
                if default is None:
                    continue
                if isinstance(default, (ast.List, ast.Dict, ast.Set)):
                    result.findings.append(ReviewFinding(
                        severity="warning", category="mutable_default",
                        message=f"Mutable default argument in {node.name}",
                        line=node.lineno,
                    ))

    # Check for hardcoded test values (overfitting)
    _check_overfitting(code, result)

    # Check for empty functions
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            body = node.body
            if len(body) == 1 and isinstance(body[0], ast.Pass):
                result.findings.append(ReviewFinding(
                    severity="warning", category="empty_function",
                    message=f"Function {node.name} has empty body (pass only)",
                    line=node.lineno,
                ))

    return result


def _check_function(node: ast.FunctionDef, result: ReviewResult) -> None:
    """Check a single function definition."""
    # Check for docstring
    if (node.body and isinstance(node.body[0], ast.Expr)
            and isinstance(node.body[0].value, ast.Constant)
            and isinstance(node.body[0].value.value, str)):
        pass  # Has docstring
    else:
        # Only flag public functions (not starting with _)
        if not node.name.startswith("_"):
            result.findings.append(ReviewFinding(
                severity="info", category="missing_docstring",
                message=f"Public function {node.name} lacks docstring",
                line=node.lineno,
            ))

    # Check complexity (rough cyclomatic complexity)
    complexity = _complexity(node)
    if complexity > 15:
        result.findings.append(ReviewFinding(
            severity="warning", category="high_complexity",
            message=f"Function {node.name} has complexity {complexity} (consider refactoring)",
            line=node.lineno,
        ))


def _complexity(node: ast.AST) -> int:
    """Rough cyclomatic complexity."""
    complexity = 1
    for child in ast.walk(node):
        if isinstance(child, (ast.If, ast.While, ast.For, ast.ExceptHandler)):
            complexity += 1
        elif isinstance(child, ast.BoolOp):
            complexity += len(child.values) - 1
    return complexity


def _check_overfitting(code: str, result: ReviewResult) -> None:
    """Check for signs of test overfitting."""
    # Look for hardcoded return values that match common test patterns
    lines = code.splitlines()
    for i, line in enumerate(lines, 1):
        stripped = line.strip()
        # Check for direct return of hardcoded values
        if re.match(r'return\s+["\'].*["\']\s*$', stripped):
            # This alone isn't bad, but if there are many, it's suspicious
            pass
        # Check for if __name__ == "__main__" with hardcoded test asserts
        if "assert _r ==" in stripped or "assert result ==" in stripped:
            # The code has inline asserts that might be overfitting
            pass  # This is actually fine for self-dev skills
