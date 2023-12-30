# Proppy: Experimental Python Library for Prop-Based Software Design

## Overview

Proppy is an experimental Python library designed to implement the mathematical structure known as "prop," a generalization of an operad. Please note that as a work in progress, Proppy is not ready for use at this stage and is undergoing significant development and changes.

## Features

- **Operation Abstract Class**: The foundational structure of Proppy revolves around the `Operation` abstract class. Users can define their own operations by creating child classes of `Operation`.
  
- **Composable Operations**: Proppy aims to provide various ways to combine multiple operations:
  - **Composition**: Chain operations together, where the output of one operation serves as the input for another.
  - **Concatenation**: Merge operations that share a common input, with their outputs concatenated.
  - **Branching**: Implement conditional operations, deciding which operation to execute based on specific conditions.
  - **Cycling**: Repeat a single operation multiple times in a controlled manner.

## Installation

Since Proppy is not yet ready for public use, it is not available on pip. I advise against attempting to install or use the package in its current state.

## Usage

At this stage, Proppy is not meant to be used. However, once it reaches a stable state, users will define custom operations by creating child classes of the `Operation` abstract class and combine these operations using the various composition techniques provided by Proppy.

## Contributing

Proppy is a work in progress and can benefit from community feedback and contributions. If you're interested in contributing, please follow the guidelines in [CONTRIBUTING.md](CONTRIBUTING.md).

## License

Proppy is licensed under the [MIT License](LICENSE).

## Support

For questions, feedback, or issues related to Proppy, please open an issue on GitHub.
