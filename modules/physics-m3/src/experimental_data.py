"""
Module for ingesting, validating, and managing experimental data from material
and mechanical tests.

Provides the :class:`ExperimentalData` container class that supports CSV, JSON,
and dictionary import; interpolation/resampling; validation against common
experimental-data defects (NaN, inf, non-monotonic x); summary statistics; and
matplotlib-based visualisation.
"""

from __future__ import annotations

import csv
import json
from copy import deepcopy
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _validate_numeric_array(arr: np.ndarray, name: str = "array") -> None:
    """Raise ``ValueError`` if *arr* contains NaN or infinity."""
    if np.any(np.isnan(arr)):
        raise ValueError(f"{name} contains NaN values")
    if np.any(np.isinf(arr)):
        raise ValueError(f"{name} contains infinite values")


def _ensure_numpy(
    data: Union[List[float], np.ndarray],
) -> np.ndarray:
    """Coerce *data* to a 1-D float64 :class:`~numpy.ndarray`."""
    arr = np.asarray(data, dtype=np.float64).ravel()
    return arr


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


class ExperimentalData:
    """Container for one or more experimental datasets.

    Each dataset is stored as a dictionary with keys ``x``, ``y``,
    ``y_err``, and ``metadata``.  The class provides import/export,
    interpolation, validation, and plotting convenience methods.

    Parameters
    ----------
    name : str
        Human-readable identifier for this collection of datasets.
    data_source : str or Path or None, optional
        Optional file path or URL string describing where the data
        originated.  Stored as metadata on the parent container but
        not used internally.

    Attributes
    ----------
    name : str
        Collection name.
    data_source : str or None
        Origin descriptor.
    _datasets : dict[str, dict]
        Internal storage.  Each value has the
        structure ``{x, y, y_err, metadata}``.

    Examples
    --------
    >>> ed = ExperimentalData("tensile-test-001")
    >>> ed.add_dataset("specimen-A", x=[0, 1, 2], y=[0, 5, 10])
    >>> ed.list_datasets()
    ['specimen-A']
    """

    # ------------------------------------------------------------------
    # Construction and import
    # ------------------------------------------------------------------

    def __init__(
        self,
        name: str,
        data_source: Optional[Union[str, Path]] = None,
    ) -> None:
        self.name: str = name
        self.data_source: Optional[str] = str(data_source) if data_source is not None else None
        self._datasets: Dict[str, Dict[str, Any]] = {}

    def from_csv(
        self,
        filepath: Union[str, Path],
        delimiter: str = ",",
    ) -> "ExperimentalData":
        """Load experimental data from a CSV file.

        The method expects at least two numeric columns.  Columns are
        auto-detected:

        * If the header contains a column named ``'x'`` (case-insensitive),
          that column is used as the independent variable.
        * If the header contains ``'y'``, ``'stress'``, ``'strain'``,
          ``'force'``, or ``'load'``, it is used as the dependent
          variable.  The first matching column wins.
        * If auto-detection fails (e.g. no header or no recognised names),
          the **first** column is used as *x* and the **second** as *y*.
        * Any additional column named with a ``'_err'`` suffix or
          ``'y_err'`` / ``'error'`` is treated as the uncertainty on *y*.

        Parameters
        ----------
        filepath : str or Path
            Path to the CSV file.
        delimiter : str, optional
            Column delimiter (default ``','``).

        Returns
        -------
        ExperimentalData
            ``self`` (method chaining).

        Raises
        ------
        FileNotFoundError
            If *filepath* does not exist.
        ValueError
            If the file cannot be parsed or fewer than two columns
            are found.
        """
        filepath = Path(filepath)
        if not filepath.exists():
            raise FileNotFoundError(f"CSV file not found: {filepath}")

        with filepath.open("r", newline="") as fh:
            sample = fh.read(65536)
            fh.seek(0)
            dialect = csv.Sniffer().sniff(sample, delimiters=",;\t|")
            reader = csv.reader(fh, dialect)

            rows = list(reader)
            if len(rows) < 2:
                raise ValueError(
                    f"CSV file must contain at least a header + 1 data row; "
                    f"found {len(rows)} rows."
                )

            header = rows[0]
            data_rows = rows[1:]
            num_cols = len(header)
            # Build column index
            col_index: Dict[str, int] = {}
            for i, col_name in enumerate(header):
                stripped = col_name.strip().lower()
                col_index[stripped] = i
                col_index[stripped.rstrip("_err").rstrip("_error")] = i

            # Auto-detect x column
            x_col: Optional[int] = None
            for candidate in ("x", "time", "displacement", "position"):
                if candidate in col_index:
                    x_col = col_index[candidate]
                    break
            if x_col is None:
                x_col = 0  # fallback: first column

            # Auto-detect y column
            y_col: Optional[int] = None
            for candidate in (
                "y",
                "stress",
                "strain",
                "force",
                "load",
                "response",
            ):
                if candidate in col_index:
                    y_col = col_index[candidate]
                    break
            if y_col is None:
                y_col = 1 if num_cols > 1 else None  # fallback: second column

            if y_col is None:
                raise ValueError("Could not determine y-column; fewer than 2 columns found.")

            # Auto-detect y_err column
            y_err_col: Optional[int] = None
            for candidate in ("y_err", "y_error", "error", "uncertainty"):
                if candidate in col_index:
                    y_err_col = col_index[candidate]
                    break
            # Also check for any column ending in _err
            for candidate, idx in col_index.items():
                if candidate.endswith("_err") and idx not in (x_col, y_col):
                    y_err_col = idx
                    break

            # Parse numeric data
            x_vals: List[float] = []
            y_vals: List[float] = []
            y_err_vals: Optional[List[float]] = [] if y_err_col is not None else None

            for row in data_rows:
                if len(row) <= max(x_col, y_col):
                    continue
                try:
                    x_vals.append(float(row[x_col].strip()))
                    y_vals.append(float(row[y_col].strip()))
                    if y_err_col is not None and len(row) > y_err_col:
                        err_val = row[y_err_col].strip()
                        y_err_vals.append(float(err_val) if err_val else None)  # type: ignore[union-attr]
                    elif y_err_vals is not None:
                        y_err_vals.append(None)
                except (ValueError, IndexError):
                    continue

            dataset_name = filepath.stem
            self.add_dataset(
                name=dataset_name,
                x=x_vals,
                y=y_vals,
                y_err=y_err_vals,
                metadata={"source": str(filepath), "delimiter": delimiter},
            )
        return self

    def from_json(self, filepath: Union[str, Path]) -> "ExperimentalData":
        """Load experimental data from a JSON file.

        Expected JSON structure (list or single object)::

            [
                {
                    "name": "dataset-1",
                    "x": [0, 1, 2],
                    "y": [0, 5, 10],
                    "y_err": [0.1, 0.2, 0.1],
                    "metadata": {"condition": "ambient"}
                },
                ...
            ]

        Parameters
        ----------
        filepath : str or Path
            Path to the JSON file.

        Returns
        -------
        ExperimentalData
            ``self`` (method chaining).

        Raises
        ------
        FileNotFoundError
            If the file does not exist.
        ValueError
            If the JSON cannot be parsed into the expected schema.
        """
        filepath = Path(filepath)
        if not filepath.exists():
            raise FileNotFoundError(f"JSON file not found: {filepath}")

        with filepath.open("r") as fh:
            raw = json.load(fh)

        if isinstance(raw, dict):
            raw = [raw]

        if not isinstance(raw, list):
            raise ValueError(
                "JSON root must be an object (single dataset) or an array "
                "(multiple datasets)."
            )

        for entry in raw:
            if "name" not in entry or "x" not in entry or "y" not in entry:
                raise ValueError(
                    "Each JSON dataset entry must contain 'name', 'x', and 'y'."
                )
            self.add_dataset(
                name=entry["name"],
                x=entry["x"],
                y=entry["y"],
                y_err=entry.get("y_err"),
                metadata=entry.get("metadata"),
            )

        return self

    def from_dict(self, data: Dict[str, Any]) -> "ExperimentalData":
        """Load experimental data from a Python dictionary.

        The dictionary must have a ``'datasets'`` key whose value is a
        list of dataset dicts (same schema as :meth:`from_json`).

        Parameters
        ----------
        data : dict
            Dictionary with structure ``{'datasets': [...], ...}``.

        Returns
        -------
        ExperimentalData
            ``self`` (method chaining).

        Raises
        ------
        ValueError
            If the dictionary does not contain a ``'datasets'`` key or
            the datasets are malformed.
        """
        datasets = data.get("datasets")
        if datasets is None:
            raise ValueError("Input dict must contain a 'datasets' key.")
        if not isinstance(datasets, list):
            raise ValueError("'datasets' must be a list.")

        for entry in datasets:
            if "name" not in entry or "x" not in entry or "y" not in entry:
                raise ValueError(
                    "Each dataset entry must contain 'name', 'x', and 'y'."
                )
            self.add_dataset(
                name=entry["name"],
                x=entry["x"],
                y=entry["y"],
                y_err=entry.get("y_err"),
                metadata=entry.get("metadata"),
            )

        return self

    # ------------------------------------------------------------------
    # Dataset management
    # ------------------------------------------------------------------

    def add_dataset(
        self,
        name: str,
        x: Union[List[float], np.ndarray],
        y: Union[List[float], np.ndarray],
        y_err: Optional[Union[List[float], np.ndarray]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Add a single experimental dataset.

        Parameters
        ----------
        name : str
            Unique name for the dataset.  If a dataset with this name
            already exists it will be overwritten.
        x : array-like
            Independent variable values.
        y : array-like
            Dependent variable values.
        y_err : array-like or None, optional
            Uncertainty (standard deviation / error bar) on *y*.
        metadata : dict or None, optional
            Arbitrary key-value metadata (e.g. temperature, strain rate).

        Raises
        ------
        ValueError
            If *x* and *y* have different lengths.
        """
        x_arr = _ensure_numpy(x)
        y_arr = _ensure_numpy(y)

        if x_arr.shape != y_arr.shape:
            raise ValueError(
                f"x and y must have the same length; got {len(x_arr)} vs "
                f"{len(y_arr)}."
            )

        y_err_arr: Optional[np.ndarray] = None
        if y_err is not None:
            y_err_arr = _ensure_numpy(y_err)
            if y_err_arr.shape != x_arr.shape:
                raise ValueError(
                    f"y_err must have the same length as x; got "
                    f"{len(y_err_arr)} vs {len(x_arr)}."
                )

        self._datasets[name] = {
            "x": x_arr,
            "y": y_arr,
            "y_err": y_err_arr,
            "metadata": deepcopy(metadata) if metadata else {},
        }

    def get_dataset(self, name: str) -> Dict[str, Any]:
        """Return a single dataset as a dictionary.

        Parameters
        ----------
        name : str
            Dataset name.

        Returns
        -------
        dict
            Dictionary with keys ``x``, ``y``, ``y_err`` (or ``None``),
            and ``metadata``.

        Raises
        ------
        KeyError
            If *name* does not exist.
        """
        if name not in self._datasets:
            raise KeyError(f"Dataset '{name}' not found.")
        return {
            "x": self._datasets[name]["x"].copy(),
            "y": self._datasets[name]["y"].copy(),
            "y_err": (
                self._datasets[name]["y_err"].copy()
                if self._datasets[name]["y_err"] is not None
                else None
            ),
            "metadata": deepcopy(self._datasets[name]["metadata"]),
        }

    def list_datasets(self) -> List[str]:
        """Return the names of all stored datasets.

        Returns
        -------
        list of str
            Dataset names in insertion order.
        """
        return list(self._datasets.keys())

    # ------------------------------------------------------------------
    # Summary and reporting
    # ------------------------------------------------------------------

    def summary(self) -> Dict[str, Dict[str, Any]]:
        """Compute summary statistics for all datasets.

        For each dataset the following are returned:

        * ``'n_points'`` — number of data points
        * ``'x_min'``, ``'x_max'`` — independent variable range
        * ``'y_min'``, ``'y_max'`` — dependent variable range
        * ``'y_mean'``, ``'y_std'`` — mean & standard deviation of *y*
        * ``'has_errors'`` — whether *y_err* is present
        * ``'x_monotonic'`` — whether *x* is strictly monotonic

        Returns
        -------
        dict
            Mapping ``dataset_name -> stats_dict``.
        """
        result: Dict[str, Dict[str, Any]] = {}
        for dset_name, dset in self._datasets.items():
            x = dset["x"]
            y = dset["y"]
            dx = np.diff(x)
            is_monotonic_inc = np.all(dx > 0)
            is_monotonic_dec = np.all(dx < 0)
            result[dset_name] = {
                "n_points": int(len(x)),
                "x_min": float(x.min()),
                "x_max": float(x.max()),
                "y_min": float(y.min()),
                "y_max": float(y.max()),
                "y_mean": float(y.mean()),
                "y_std": float(y.std(ddof=1)) if len(y) > 1 else 0.0,
                "has_errors": dset["y_err"] is not None,
                "x_monotonic": bool(is_monotonic_inc or is_monotonic_dec),
            }
        return result

    # ------------------------------------------------------------------
    # Resampling / interpolation
    # ------------------------------------------------------------------

    def resample(
        self,
        name: str,
        x_new: Union[List[float], np.ndarray],
    ) -> np.ndarray:
        """Interpolate a dataset onto new *x* points.

        Linear interpolation is used.  Values outside the original range
        are extrapolated linearly.

        Parameters
        ----------
        name : str
            Dataset name.
        x_new : array-like
            New independent variable points.

        Returns
        -------
        numpy.ndarray
            Interpolated *y* values at *x_new*.

        Raises
        ------
        KeyError
            If *name* does not exist.
        ValueError
            If the dataset has fewer than 2 unique points (cannot
            interpolate).
        """
        if name not in self._datasets:
            raise KeyError(f"Dataset '{name}' not found.")

        dset = self._datasets[name]
        x = dset["x"]
        y = dset["y"]
        x_new_arr = _ensure_numpy(x_new)

        if len(np.unique(x)) < 2:
            raise ValueError(
                f"Dataset '{name}' has fewer than 2 unique x-values; "
                f"cannot interpolate."
            )

        return np.interp(x_new_arr, x, y)

    # ------------------------------------------------------------------
    # Validation
    # ------------------------------------------------------------------

    def validate(self) -> Dict[str, Any]:
        """Validate all datasets and return a report.

        Checks performed per dataset:

        * No NaN values in *x* or *y*
        * No infinite values in *x* or *y*
        * *x* is strictly monotonic (increasing or decreasing)
        * At least 2 data points
        * *y_err* (if present) is non-negative and finite

        Returns
        -------
        dict
            Validation report with keys:

            * ``'valid'`` — ``True`` if all checks pass for all datasets
            * ``'n_datasets'`` — total number of datasets
            * ``'n_valid'`` — number of datasets that pass all checks
            * ``'n_invalid'`` — number of datasets with at least one
              failure
            * ``'details'`` — per-dataset list of issue strings (empty
              list for valid datasets)
        """
        details: Dict[str, List[str]] = {}
        n_valid = 0
        n_invalid = 0

        for dset_name, dset in self._datasets.items():
            issues: List[str] = []
            x = dset["x"]
            y = dset["y"]

            # NaN / inf
            if np.any(np.isnan(x)):
                issues.append("x contains NaN")
            if np.any(np.isinf(x)):
                issues.append("x contains inf")
            if np.any(np.isnan(y)):
                issues.append("y contains NaN")
            if np.any(np.isinf(y)):
                issues.append("y contains inf")

            # Length
            if len(x) < 2:
                issues.append(f"fewer than 2 data points ({len(x)})")

            # Monotonicity
            dx = np.diff(x)
            if not (np.all(dx > 0) or np.all(dx < 0)):
                issues.append("x is not strictly monotonic")

            # y_err checks
            y_err = dset["y_err"]
            if y_err is not None:
                if np.any(np.isnan(y_err)):
                    issues.append("y_err contains NaN")
                if np.any(np.isinf(y_err)):
                    issues.append("y_err contains inf")
                if np.any(y_err < 0):
                    issues.append("y_err contains negative values")

            details[dset_name] = issues
            if issues:
                n_invalid += 1
            else:
                n_valid += 1

        valid = n_invalid == 0
        return {
            "valid": valid,
            "n_datasets": len(self._datasets),
            "n_valid": n_valid,
            "n_invalid": n_invalid,
            "details": details,
        }

    # ------------------------------------------------------------------
    # Plotting
    # ------------------------------------------------------------------

    def plot(
        self,
        names: Optional[Union[str, List[str]]] = None,
    ) -> "tuple":  # noqa: UP037  -- lazy import
        """Plot selected datasets using Matplotlib.

        Parameters
        ----------
        names : str or list of str or None, optional
            Name(s) of datasets to plot.  If ``None``, all datasets are
            plotted (default).

        Returns
        -------
        tuple (matplotlib.figure.Figure, matplotlib.axes.Axes)
            Figure and axes handle for further customisation.

        Raises
        ------
        ImportError
            If ``matplotlib`` is not installed.
        KeyError
            If a requested dataset does not exist.
        """
        try:
            import matplotlib.pyplot as plt
        except ImportError:
            raise ImportError(
                "matplotlib is required for plotting. "
                "Install it with: pip install matplotlib"
            )

        if names is None:
            names = self.list_datasets()
        elif isinstance(names, str):
            names = [names]

        fig, ax = plt.subplots()
        for dset_name in names:
            if dset_name not in self._datasets:
                raise KeyError(f"Dataset '{dset_name}' not found.")
            dset = self._datasets[dset_name]
            x = dset["x"]
            y = dset["y"]
            y_err = dset["y_err"]
            label = dset_name

            if y_err is not None:
                ax.errorbar(x, y, yerr=y_err, fmt="o-", capsize=3, label=label)
            else:
                ax.plot(x, y, "o-", label=label)

        ax.set_xlabel("x")
        ax.set_ylabel("y")
        ax.set_title(self.name)
        ax.legend()
        ax.grid(True, alpha=0.35)

        return fig, ax

    # ------------------------------------------------------------------
    # Export
    # ------------------------------------------------------------------

    def to_json(self, filepath: Union[str, Path]) -> None:
        """Export all datasets to a JSON file.

        The output structure matches the schema expected by
        :meth:`from_json`.

        Parameters
        ----------
        filepath : str or Path
            Destination file path.
        """
        output: List[Dict[str, Any]] = []
        for dset_name, dset in self._datasets.items():
            entry: Dict[str, Any] = {
                "name": dset_name,
                "x": dset["x"].tolist(),
                "y": dset["y"].tolist(),
                "metadata": dset["metadata"],
            }
            if dset["y_err"] is not None:
                # Replace None placeholders with NaN for JSON
                y_err_list = dset["y_err"].tolist()
                entry["y_err"] = [
                    v if v is not None else None for v in y_err_list
                ]
            else:
                entry["y_err"] = None
            output.append(entry)

        filepath = Path(filepath)
        with filepath.open("w") as fh:
            json.dump(
                {"datasets": output, "source": self.name},
                fh,
                indent=2,
                allow_nan=False,
            )
