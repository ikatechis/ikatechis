# Claude.md - Development Guidelines

## Test-Driven Development (TDD) Practices

This project follows strict TDD practices to ensure reliability and maintainability.

### TDD Workflow

1. **Write Tests First**
   - Write failing tests that define the desired behavior
   - Tests should be specific, focused, and test one thing
   - Use descriptive test names that explain the expected behavior

   ```python
   def test_sleeve_channel_has_correct_radius(self) -> None:
       """Test that channel radius includes sleeve outer diameter plus clearance."""
       # Arrange
       spec = SleeveSpec(outer_diameter=5.0, clearance=0.1)

       # Act
       channel = create_sleeve_channel(position, direction, spec)

       # Assert
       expected_radius = (5.0 / 2) + 0.1
       # Verify channel matches expected dimensions
   ```

2. **Write Minimal Implementation**
   - Write just enough code to make the test pass
   - Don't add features that aren't tested
   - Keep it simple initially

3. **Refactor**
   - Once tests pass, improve code quality
   - Extract functions, add type hints, improve readability
   - Tests protect against regression during refactoring

4. **Repeat**
   - Add new tests for new features
   - Each component should have comprehensive test coverage

### Test Organization

```
surgical_guide_generator/
├── tests/
│   ├── test_config.py          # Config validation tests
│   ├── test_mesh_io.py          # I/O operation tests
│   ├── test_validation.py       # Mesh validation tests
│   ├── test_repair.py           # Repair operation tests
│   ├── test_sleeve_channels.py  # Geometry tests
│   ├── test_boolean_ops.py      # Boolean operation tests
│   └── test_integration.py      # End-to-end tests
```

### Test Naming Convention

- **Class names**: `TestComponentName` (e.g., `TestSleeveSpec`)
- **Method names**: `test_what_when_expected` (e.g., `test_rotation_z_to_x`)
- **Fixtures**: Descriptive names (e.g., `valid_cube_mesh`, `mesh_with_hole`)

### Test Categories

1. **Unit Tests** - Test individual functions in isolation
2. **Integration Tests** - Test component interactions
3. **Edge Case Tests** - Test boundary conditions and error handling
4. **Property Tests** - Test mathematical properties (orthogonality, conservation, etc.)

Example from our codebase:

```python
class TestComputeRotationMatrix:
    """Test rotation matrix computation."""

    def test_rotation_z_to_z(self) -> None:
        """Test rotation from Z to Z (identity)."""
        # Unit test - simple case

    def test_rotation_is_orthogonal(self) -> None:
        """Test that rotation matrix is orthogonal."""
        # Property test - mathematical invariant

    def test_rotation_preserves_length(self) -> None:
        """Test that rotation matrix preserves vector length."""
        # Property test - physical invariant
```

---

## State-of-the-Art Coding Best Practices

### 1. Type Safety

**Use comprehensive type hints** for all function signatures:

```python
from typing import Tuple, Optional
import numpy.typing as npt

def compute_rotation_matrix(
    direction: npt.NDArray[np.float64]
) -> npt.NDArray[np.float64]:
    """Compute rotation matrix with full type information."""
    pass
```

**Benefits**:
- Catch bugs at development time (with mypy)
- Better IDE autocomplete
- Self-documenting code

### 2. Structured Results

**Use dataclasses for structured outputs** instead of tuples or dicts:

```python
from dataclasses import dataclass, field

@dataclass
class ValidationResult:
    """Clear, typed result structure."""
    is_valid: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    metrics: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Enable serialization when needed."""
        return asdict(self)
```

**Benefits**:
- Type-safe field access
- Clear API contracts
- Easy to extend without breaking callers

### 3. Defensive Programming

**Validate inputs aggressively**:

```python
def create_sleeve_channel(
    position: npt.NDArray[np.float64],
    direction: npt.NDArray[np.float64],
    sleeve_spec: SleeveSpec,
) -> trimesh.Trimesh:
    """Create channel with validated inputs."""
    # Normalize direction (defensive - ensure unit vector)
    direction = direction / np.linalg.norm(direction)

    # Validation happens in SleeveSpec.__post_init__
    # Raises ValueError if invalid

    # Proceed with guaranteed-valid inputs
```

**Handle errors gracefully**:

```python
try:
    result_mesh = mesh_a.difference(mesh_b, engine='manifold')
except Exception as e:
    return BooleanResult(
        success=False,
        error_message=f"Boolean difference failed: {str(e)}",
    )
```

### 4. Separation of Concerns

**Each module has a single responsibility**:

- `config.py` - Configuration and validation
- `mesh_io.py` - File I/O operations
- `validation.py` - Mesh quality checks
- `repair.py` - Mesh fixing operations
- `sleeve_channels.py` - Geometry creation
- `boolean_ops.py` - CSG operations

**No circular dependencies**:
```
config.py (no deps) ← mesh_io.py ← repair.py
                    ← validation.py
                    ← sleeve_channels.py
                    ← boolean_ops.py
                    ← generator.py (orchestrates all)
```

### 5. Documentation

**Docstrings with Examples**:

```python
def create_sleeve_channel(...) -> trimesh.Trimesh:
    """Create a cylindrical channel for sleeve placement.

    Creates a cylinder mesh aligned to the implant axis for Boolean
    subtraction from the guide body.

    Args:
        position: Implant platform center (entry point on guide surface)
        direction: Implant axis unit vector (pointing apical/into bone)
        sleeve_spec: Sleeve specifications including dimensions
        extension: Extra cylinder length for clean Boolean cut (mm)

    Returns:
        Cylinder mesh positioned and oriented for Boolean subtraction

    Raises:
        ValueError: If direction vector is zero

    Example:
        >>> spec = SleeveSpec(outer_diameter=5.0, ...)
        >>> position = np.array([25.0, -12.0, 8.0])
        >>> direction = np.array([0.0, 0.1, -0.995])
        >>> channel = create_sleeve_channel(position, direction, spec)
        >>> assert channel.is_volume
    """
```

### 6. Immutability When Possible

**Copy before modifying** to avoid side effects:

```python
def repair_mesh(mesh: trimesh.Trimesh) -> RepairResult:
    """Work on a copy to avoid modifying input."""
    repaired = mesh.copy()  # Don't modify original
    repaired.merge_vertices()
    # ... more operations
    return RepairResult(repaired_mesh=repaired)
```

### 7. Explicit is Better Than Implicit

**Named constants over magic numbers**:

```python
# Good
DEFAULT_SLEEVE_CLEARANCE_MM = 0.05  # 50μm press-fit
VOXEL_SIZE_MIN_MM = 0.1
VOXEL_SIZE_MAX_MM = 0.5

# Bad
if clearance < 0.05:  # What does 0.05 mean?
```

**Explicit engine selection**:

```python
# Good - explicit about which engine
result = mesh_a.difference(mesh_b, engine='manifold')

# Bad - implicit default may change
result = mesh_a.difference(mesh_b)
```

### 8. Fail Fast

**Validate early, fail clearly**:

```python
def __post_init__(self) -> None:
    """Validate immediately after construction."""
    if self.outer_diameter <= self.inner_diameter:
        raise ValueError(
            f"Outer diameter ({self.outer_diameter}mm) must be "
            f"greater than inner diameter ({self.inner_diameter}mm)"
        )
```

### 9. Comprehensive Error Messages

**Include context in errors**:

```python
# Good
raise ValueError(
    f"Boolean subtraction failed for site {site.get('site_id', 'unknown')}. "
    "Check for overlapping sleeves or invalid geometry."
)

# Bad
raise ValueError("Operation failed")
```

### 10. Testable Design

**Dependency injection** for testability:

```python
def validate_mesh(
    mesh: trimesh.Trimesh,
    config: ValidationConfig  # Injected, can be mocked
) -> ValidationResult:
    """Config is injected, making this easy to test."""
    if config.check_watertight:
        # Can test with different configs
```

**Small, focused functions**:

```python
# Good - each function does one thing
def compute_rotation_matrix(direction): ...
def align_cylinder_to_direction(cylinder, position, direction): ...
def create_sleeve_channel(...): ...

# Bad - one giant function doing everything
def create_and_position_channel(...): ...  # 200 lines
```

---

## Project-Specific Guidelines

### Mesh Operations

1. **Always use manifold engine** for Boolean operations
2. **Check watertightness** after Boolean operations
3. **Work on copies** when modifying meshes
4. **Validate inputs** before expensive operations

### Numerical Stability

1. **Normalize vectors** before use
2. **Add epsilon** to divisions: `1 / (x + 1e-10)`
3. **Use `np.allclose`** for floating-point comparisons
4. **Handle edge cases**: zero vectors, degenerate geometries

### Performance

1. **Voxel size** affects performance dramatically
   - 0.1mm: High quality, slow
   - 0.2mm: Good balance
   - 0.3mm+: Fast, lower quality

2. **Boolean operations** are expensive
   - Minimize sequential operations
   - Use coarser meshes when possible

3. **Marching cubes** is the bottleneck
   - Consider parallel processing for multiple guides
   - Cache intermediate results if applicable

---

## Code Review Checklist

- [ ] All functions have type hints
- [ ] All functions have docstrings with examples
- [ ] Tests written before implementation (TDD)
- [ ] Tests cover edge cases and error paths
- [ ] No magic numbers - use named constants
- [ ] Inputs validated in `__post_init__` or function start
- [ ] Errors have clear, actionable messages
- [ ] No circular dependencies
- [ ] Results use dataclasses, not tuples/dicts
- [ ] Meshes copied before modification
- [ ] Boolean ops use `engine='manifold'`
- [ ] All tests passing

---

## Example: Adding a New Feature (TDD)

### 1. Write the test first

```python
# test_new_feature.py
def test_compute_wall_thickness(self) -> None:
    """Test wall thickness computation for guide shell."""
    guide = create_guide_shell(thickness=2.5)

    min_thickness = compute_minimum_wall_thickness(guide)

    assert min_thickness >= 2.0  # Should be close to target
    assert min_thickness <= 3.0
```

### 2. Run test (should fail)

```bash
$ pytest test_new_feature.py
# FAIL - function doesn't exist yet
```

### 3. Implement minimal version

```python
# new_feature.py
def compute_minimum_wall_thickness(mesh: trimesh.Trimesh) -> float:
    """Compute minimum wall thickness."""
    # Minimal implementation
    return 2.5  # Hardcoded to make test pass
```

### 4. Test passes, refactor

```python
def compute_minimum_wall_thickness(
    mesh: trimesh.Trimesh,
    num_samples: int = 1000
) -> float:
    """Compute minimum wall thickness by sampling.

    Args:
        mesh: Guide shell mesh
        num_samples: Number of sample points

    Returns:
        Minimum wall thickness in mm
    """
    # Real implementation with sampling
    # ... proper algorithm
```

### 5. Add more tests

```python
def test_wall_thickness_with_thin_spot(self) -> None:
    """Test detection of thin spots."""

def test_wall_thickness_edge_cases(self) -> None:
    """Test with degenerate inputs."""
```

---

## Metrics

Current project status:
- **96 tests** passing (100% success rate)
- **9 modules** fully implemented
- **Type coverage**: 100% (all functions typed)
- **Docstring coverage**: 100%
- **Test coverage**: ~90% (estimated based on critical paths)

Modules complete:
1. Configuration (14 tests)
2. Mesh I/O (12 tests)
3. Validation (13 tests)
4. Repair (9 tests)
5. Sleeve Channels (13 tests)
6. Boolean Operations (14 tests)
7. Inspection Windows (10 tests)
8. Main Pipeline (11 tests)

---

## References

- **PEP 8**: Python style guide
- **PEP 484**: Type hints
- **PEP 257**: Docstring conventions
- **Trimesh**: https://trimsh.org/
- **Manifold3D**: https://github.com/elalish/manifold
- **Test-Driven Development by Example** (Kent Beck)
- **Clean Code** (Robert C. Martin)
