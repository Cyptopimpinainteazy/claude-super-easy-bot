"""
Sample Python file to demonstrate automated documentation features.
This file shows how the auto-docstring extension works with various function types.
"""

from typing import Dict, List, Optional, Union


class SampleClass:
    """A sample class to demonstrate documentation features."""

    def __init__(self, name: str, value: int = 0):
        """Initialize the sample class.

        Args:
            name: The name of the instance
            value: An optional initial value
        """
        self.name = name
        self.value = value

    def calculate_profit(self, price: float, cost: float) -> float:
        """Calculate profit from price and cost.

        This method demonstrates how the auto-docstring extension
        can automatically generate comprehensive docstrings.

        Args:
            price: The selling price
            cost: The cost price

        Returns:
            The calculated profit

        Raises:
            ValueError: If price or cost are negative

        Example:
            >>> calc = SampleClass("test")
            >>> calc.calculate_profit(100, 80)
            20.0
        """
        if price < 0 or cost < 0:
            raise ValueError("Price and cost must be non-negative")

        return price - cost

    def process_data(self, data: List[Dict[str, Union[str, int]]]) -> Optional[Dict[str, int]]:
        """Process a list of data dictionaries.

        Args:
            data: List of dictionaries containing string and int values

        Returns:
            A dictionary with aggregated results or None if no data

        Note:
            This method demonstrates complex type annotations
            that the auto-docstring extension handles automatically.
        """
        if not data:
            return None

        result = {"total": 0, "count": len(data)}
        return result


def standalone_function(param1: str, param2: Optional[int] = None) -> Dict[str, Union[str, int]]:
    """A standalone function demonstrating auto-docstring generation.

    This function shows how the extension automatically generates
    comprehensive docstrings with proper formatting.

    Args:
        param1: A required string parameter
        param2: An optional integer parameter

    Returns:
        A dictionary containing the processed parameters

    TODO:
        Add input validation
        Implement error handling
    """
    result = {"param1": param1}
    if param2 is not None:
        result["param2"] = param2

    return result


# Function without docstring - auto-docstring will suggest adding one
def undocumented_function(x, y):
    return x + y


if __name__ == "__main__":
    # Demonstrate the functionality
    sample = SampleClass("demo", 42)
    profit = sample.calculate_profit(150.0, 120.0)
    print(f"Profit: ${profit}")

    data = [{"name": "item1", "value": 10}, {"name": "item2", "value": 20}]
    result = sample.process_data(data)
    print(f"Processed data: {result}")

    standalone_result = standalone_function("test", 123)
    print(f"Standalone result: {standalone_result}")
