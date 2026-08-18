"""
Modular Beam Integration definitions for OpenSees beam-column elements.
Supports plastic hinge integration methods, distributed plasticity, and user-defined integration.
Reference: https://openseespydoc.readthedocs.io/en/latest/src/beamIntegration.html
"""

from abc import ABC, abstractmethod
from typing import Optional, List, Union


class BeamIntegration(ABC):
    """
    Abstract base class for OpenSees beam integration rules.
    """

    @abstractmethod
    def build(self, tag: int, model) -> None:
        """
        Execute the OpenSees beamIntegration command.

        Parameters
        ----------
        tag : int
            Integration rule tag (passed to beamIntegration and element).
        model : Model
            The RC Column Model instance containing section tags, plastic hinge length, etc.
        """
        pass


# =========================================================================
# 1. Plastic Hinge Integration Methods
# =========================================================================

class HingeRadau(BeamIntegration):
    """
    Gauss-Radau plastic hinge integration method.
    Uses 2 integration points in hinge I (at node I and 4/3*lpI),
    2 in hinge J (at node J and 4/3*lpJ), and 2 in the elastic interior.

    Command: ops.beamIntegration('HingeRadau', tag, secI, lpI, secJ, lpJ, secE)
    """

    def __init__(
        self,
        lp_bottom: Optional[float] = None,
        lp_top: float = 0.0,
        sec_i: Optional[int] = None,
        sec_j: Optional[int] = None,
        sec_e: Optional[int] = None,
    ):
        self.lp_bottom = lp_bottom
        self.lp_top = lp_top
        self.sec_i = sec_i
        self.sec_j = sec_j
        self.sec_e = sec_e

    def build(self, tag: int, model) -> None:
        import openseespy.opensees as ops

        lp_i = self.lp_bottom if self.lp_bottom is not None else model.lp
        lp_j = self.lp_top
        sec_i = self.sec_i if self.sec_i is not None else model.fib_sec_tag
        sec_j = self.sec_j if self.sec_j is not None else model.fib_sec_tag
        sec_e = self.sec_e if self.sec_e is not None else model.elastic_sec_tag

        ops.beamIntegration('HingeRadau', tag, sec_i, lp_i, sec_j, lp_j, sec_e)


class HingeRadauTwo(BeamIntegration):
    """
    Modified Gauss-Radau plastic hinge integration with two points placed on each end.
    
    Command: ops.beamIntegration('HingeRadauTwo', tag, secI, lpI, secJ, lpJ, secE)
    """

    def __init__(
        self,
        lp_bottom: Optional[float] = None,
        lp_top: float = 0.0,
        sec_i: Optional[int] = None,
        sec_j: Optional[int] = None,
        sec_e: Optional[int] = None,
    ):
        self.lp_bottom = lp_bottom
        self.lp_top = lp_top
        self.sec_i = sec_i
        self.sec_j = sec_j
        self.sec_e = sec_e

    def build(self, tag: int, model) -> None:
        import openseespy.opensees as ops

        lp_i = self.lp_bottom if self.lp_bottom is not None else model.lp
        lp_j = self.lp_top
        sec_i = self.sec_i if self.sec_i is not None else model.fib_sec_tag
        sec_j = self.sec_j if self.sec_j is not None else model.fib_sec_tag
        sec_e = self.sec_e if self.sec_e is not None else model.elastic_sec_tag

        ops.beamIntegration('HingeRadauTwo', tag, sec_i, lp_i, sec_j, lp_j, sec_e)


class HingeMidpoint(BeamIntegration):
    """
    Midpoint plastic hinge integration method.
    Places integration points at lpI/2 and L - lpJ/2.

    Command: ops.beamIntegration('HingeMidpoint', tag, secI, lpI, secJ, lpJ, secE)
    """

    def __init__(
        self,
        lp_bottom: Optional[float] = None,
        lp_top: float = 0.0,
        sec_i: Optional[int] = None,
        sec_j: Optional[int] = None,
        sec_e: Optional[int] = None,
    ):
        self.lp_bottom = lp_bottom
        self.lp_top = lp_top
        self.sec_i = sec_i
        self.sec_j = sec_j
        self.sec_e = sec_e

    def build(self, tag: int, model) -> None:
        import openseespy.opensees as ops

        lp_i = self.lp_bottom if self.lp_bottom is not None else model.lp
        lp_j = self.lp_top
        sec_i = self.sec_i if self.sec_i is not None else model.fib_sec_tag
        sec_j = self.sec_j if self.sec_j is not None else model.fib_sec_tag
        sec_e = self.sec_e if self.sec_e is not None else model.elastic_sec_tag

        ops.beamIntegration('HingeMidpoint', tag, sec_i, lp_i, sec_j, lp_j, sec_e)


class HingeEndpoint(BeamIntegration):
    """
    Endpoint plastic hinge integration method.
    Places integration points at the element endpoints (0 and L).

    Command: ops.beamIntegration('HingeEndpoint', tag, secI, lpI, secJ, lpJ, secE)
    """

    def __init__(
        self,
        lp_bottom: Optional[float] = None,
        lp_top: float = 0.0,
        sec_i: Optional[int] = None,
        sec_j: Optional[int] = None,
        sec_e: Optional[int] = None,
    ):
        self.lp_bottom = lp_bottom
        self.lp_top = lp_top
        self.sec_i = sec_i
        self.sec_j = sec_j
        self.sec_e = sec_e

    def build(self, tag: int, model) -> None:
        import openseespy.opensees as ops

        lp_i = self.lp_bottom if self.lp_bottom is not None else model.lp
        lp_j = self.lp_top
        sec_i = self.sec_i if self.sec_i is not None else model.fib_sec_tag
        sec_j = self.sec_j if self.sec_j is not None else model.fib_sec_tag
        sec_e = self.sec_e if self.sec_e is not None else model.elastic_sec_tag

        ops.beamIntegration('HingeEndpoint', tag, sec_i, lp_i, sec_j, lp_j, sec_e)


class UserHinge(BeamIntegration):
    """
    User-specified plastic hinge integration method.
    Allows specifying number of integration points, positions (pts), weights (wts), and sections (secs).

    Command: ops.beamIntegration('UserHinge', tag, secE, npL, *secsL, *ptsL, *wtsL, npR, *secsR, *ptsR, *wtsR)
    """

    def __init__(
        self,
        np_i: int,
        secs_i: List[int],
        pts_i: List[float],
        wts_i: List[float],
        np_j: int = 0,
        secs_j: Optional[List[int]] = None,
        pts_j: Optional[List[float]] = None,
        wts_j: Optional[List[float]] = None,
        sec_e: Optional[int] = None,
    ):
        self.np_i = np_i
        self.secs_i = secs_i
        self.pts_i = pts_i
        self.wts_i = wts_i
        self.np_j = np_j
        self.secs_j = secs_j if secs_j is not None else []
        self.pts_j = pts_j if pts_j is not None else []
        self.wts_j = wts_j if wts_j is not None else []
        self.sec_e = sec_e

    def build(self, tag: int, model) -> None:
        import openseespy.opensees as ops

        sec_e = self.sec_e if self.sec_e is not None else model.elastic_sec_tag
        ops.beamIntegration(
            'UserHinge',
            tag,
            sec_e,
            self.np_i,
            *self.secs_i,
            *self.pts_i,
            *self.wts_i,
            self.np_j,
            *self.secs_j,
            *self.pts_j,
            *self.wts_j,
        )


# =========================================================================
# 2. Distributed Plasticity Integration Methods
# =========================================================================

class Lobatto(BeamIntegration):
    """
    Gauss-Lobatto integration method (distributed plasticity throughout the element).
    Places integration points at element ends (0 and L) and interior points.

    Command: ops.beamIntegration('Lobatto', tag, secTag, N)
    """

    def __init__(self, num_points: int = 5, sec_tag: Optional[int] = None):
        self.num_points = num_points
        self.sec_tag = sec_tag

    def build(self, tag: int, model) -> None:
        import openseespy.opensees as ops

        sec = self.sec_tag if self.sec_tag is not None else model.fib_sec_tag
        ops.beamIntegration('Lobatto', tag, sec, self.num_points)


class Legendre(BeamIntegration):
    """
    Gauss-Legendre integration method (distributed plasticity).
    Interior integration points (none exactly at the end nodes).

    Command: ops.beamIntegration('Legendre', tag, secTag, N)
    """

    def __init__(self, num_points: int = 5, sec_tag: Optional[int] = None):
        self.num_points = num_points
        self.sec_tag = sec_tag

    def build(self, tag: int, model) -> None:
        import openseespy.opensees as ops

        sec = self.sec_tag if self.sec_tag is not None else model.fib_sec_tag
        ops.beamIntegration('Legendre', tag, sec, self.num_points)


class NewtonCotes(BeamIntegration):
    """
    Newton-Cotes integration method with equally spaced integration points.

    Command: ops.beamIntegration('NewtonCotes', tag, secTag, N)
    """

    def __init__(self, num_points: int = 5, sec_tag: Optional[int] = None):
        self.num_points = num_points
        self.sec_tag = sec_tag

    def build(self, tag: int, model) -> None:
        import openseespy.opensees as ops

        sec = self.sec_tag if self.sec_tag is not None else model.fib_sec_tag
        ops.beamIntegration('NewtonCotes', tag, sec, self.num_points)


class Radau(BeamIntegration):
    """
    Gauss-Radau integration method with an integration point at one end.

    Command: ops.beamIntegration('Radau', tag, secTag, N)
    """

    def __init__(self, num_points: int = 5, sec_tag: Optional[int] = None):
        self.num_points = num_points
        self.sec_tag = sec_tag

    def build(self, tag: int, model) -> None:
        import openseespy.opensees as ops

        sec = self.sec_tag if self.sec_tag is not None else model.fib_sec_tag
        ops.beamIntegration('Radau', tag, sec, self.num_points)


class Trapezoidal(BeamIntegration):
    """
    Trapezoidal integration rule.

    Command: ops.beamIntegration('Trapezoidal', tag, secTag, N)
    """

    def __init__(self, num_points: int = 5, sec_tag: Optional[int] = None):
        self.num_points = num_points
        self.sec_tag = sec_tag

    def build(self, tag: int, model) -> None:
        import openseespy.opensees as ops

        sec = self.sec_tag if self.sec_tag is not None else model.fib_sec_tag
        ops.beamIntegration('Trapezoidal', tag, sec, self.num_points)


class CompositeSimpson(BeamIntegration):
    """
    Composite Simpson's integration rule.

    Command: ops.beamIntegration('CompositeSimpson', tag, secTag, N)
    """

    def __init__(self, num_points: int = 5, sec_tag: Optional[int] = None):
        self.num_points = num_points
        self.sec_tag = sec_tag

    def build(self, tag: int, model) -> None:
        import openseespy.opensees as ops

        sec = self.sec_tag if self.sec_tag is not None else model.fib_sec_tag
        ops.beamIntegration('CompositeSimpson', tag, sec, self.num_points)


# =========================================================================
# 3. User-Defined Multi-Section Integration
# =========================================================================

class UserDefined(BeamIntegration):
    """
    User-defined integration method specifying section tags, positions (pts),
    and integration weights (wts) along the element length (normalized 0 to 1).

    Command: ops.beamIntegration('UserDefined', tag, N, *secTags, *pts, *wts)
    """

    def __init__(
        self,
        sec_tags: List[int],
        pts: List[float],
        wts: List[float],
    ):
        if not (len(sec_tags) == len(pts) == len(wts)):
            raise ValueError("sec_tags, pts, and wts must all have the same length.")
        self.sec_tags = sec_tags
        self.pts = pts
        self.wts = wts

    def build(self, tag: int, model) -> None:
        import openseespy.opensees as ops

        n_pts = len(self.sec_tags)
        ops.beamIntegration('UserDefined', tag, n_pts, *self.sec_tags, *self.pts, *self.wts)
