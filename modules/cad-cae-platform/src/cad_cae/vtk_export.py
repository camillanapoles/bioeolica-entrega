"""VTK Export — results visualization for ParaView."""

from __future__ import annotations

import numpy as np
from vtkmodules.vtkCommonDataModel import vtkUnstructuredGrid
from vtkmodules.vtkCommonCore import vtkPoints, vtkDoubleArray, vtkIdList
from vtkmodules.vtkIOXML import vtkXMLUnstructuredGridWriter


def write_vtu(filepath: str, nodes: np.ndarray, elements: list,
              point_data: dict | None = None, cell_data: dict | None = None) -> str:
    """Write an unstructured grid to .vtu format.

    Parameters
    ----------
    filepath : str
        Output .vtu file path.
    nodes : (N, 3) ndarray
        Node coordinates.
    elements : list of tuple
        (elem_type, node_ids) — element type code per VTK.
    point_data : dict, optional
        {name: (N,) array} — nodal results.
    cell_data : dict, optional
        {name: (M,) array} — element results.

    Returns
    -------
    filepath : str
    """
    ndim = nodes.shape[1] if nodes.ndim > 1 else 3
    pts = vtkPoints()
    for i in range(nodes.shape[0]):
        if ndim == 2:
            pts.InsertNextPoint(nodes[i, 0], nodes[i, 1], 0)
        else:
            pts.InsertNextPoint(nodes[i, 0], nodes[i, 1], nodes[i, 2])

    grid = vtkUnstructuredGrid()
    grid.SetPoints(pts)

    cell_types = {4: 10, 5: 24, 6: 13, 8: 12, 10: 12, 20: 29}
    for etype, nids in elements:
        vtk_type = cell_types.get(etype, 10)
        idlist = vtkIdList()
        for nid in nids:
            idlist.InsertNextId(nid)
        grid.InsertNextCell(vtk_type, idlist)

    if point_data:
        for name, data in point_data.items():
            arr = vtkDoubleArray()
            arr.SetName(name)
            flat = np.asarray(data).ravel()
            for val in flat:
                arr.InsertNextValue(float(val))
            grid.GetPointData().AddArray(arr)

    if cell_data:
        for name, data in cell_data.items():
            arr = vtkDoubleArray()
            arr.SetName(name)
            for val in np.asarray(data).ravel():
                arr.InsertNextValue(float(val))
            grid.GetCellData().AddArray(arr)

    writer = vtkXMLUnstructuredGridWriter()
    writer.SetFileName(filepath)
    writer.SetInputData(grid)
    writer.Write()
    return filepath


def write_vtp(filepath: str, points: np.ndarray,
              point_data: dict | None = None) -> str:
    """Write a point cloud to .vtp (VTK PolyData) format.

    Parameters
    ----------
    filepath : str
        Output .vtp file path.
    points : (N, 3) ndarray
        Point coordinates.
    point_data : dict, optional
        {name: (N,) array} — data at points.

    Returns
    -------
    filepath : str
    """
    from vtkmodules.vtkCommonDataModel import vtkPolyData
    from vtkmodules.vtkIOXML import vtkXMLPolyDataWriter

    pts = vtkPoints()
    for i in range(points.shape[0]):
        pts.InsertNextPoint(points[i, 0], points[i, 1], points[i, 2])

    pd = vtkPolyData()
    pd.SetPoints(pts)

    if point_data:
        from vtkmodules.vtkCommonCore import vtkDoubleArray
        for name, data in point_data.items():
            arr = vtkDoubleArray()
            arr.SetName(name)
            for val in np.asarray(data).ravel():
                arr.InsertNextValue(float(val))
            pd.GetPointData().AddArray(arr)

    writer = vtkXMLPolyDataWriter()
    writer.SetFileName(filepath)
    writer.SetInputData(pd)
    writer.Write()
    return filepath
