from enum import auto, Enum, unique

import numpy as np
import scipy
import scipy.integrate
from typing import Callable

from vectors import *

@unique
class WireMaterial(Enum):
    COPPER = auto()
    SILVER = auto()
    GOLD = auto()
    ALUMINUM = auto()


'''
All data is at 20 degrees Celsius.
Densities are in kilgrams per cubic meter (kg/m^3)
and are taken from the Royal Society of Chemistry(RSC): 
 - https://www.rsc.org/periodic-table/element/29/copper
 - https://www.rsc.org/periodic-table/element/47/silver 
 - https://www.rsc.org/periodic-table/element/79/gold
 - https://www.rsc.org/periodic-table/element/13/aluminium 
'''
MATERIAL_DENSITIES = {
    WireMaterial.COPPER: 8.96e3,
    WireMaterial.SILVER: 10.5e3,
    WireMaterial.GOLD: 19.3e3,
    WireMaterial.ALUMINUM: 2.70e3
}


'''
All restivities are taken from the Engineering Toolbox: 
https://www.engineeringtoolbox.com/resistivity-conductivity-d_418.html. 
The values are in ohm-meters(Ω⋅m)
'''
MATERIAL_RESISTIVITIES = {
    WireMaterial.COPPER: 1.724e-8,
    WireMaterial.SILVER: 1.59e-8,
    WireMaterial.GOLD: 2.24e-8,
    WireMaterial.ALUMINUM: 2.65e-8
}


class Wire():
    """A straight current-carrying wire with a specified position, length, and resistance."""

    def __init__(self, points: np.ndarray[PositionVector],
                 mass: np.float64 = 1.0,
                 resistance: np.float64 = 1.0,
                 material: WireMaterial = None,
                 cross_sectional_area: np.float64 = -1.0
                 ) -> None:
        """Initiate a straight current-carrying wire.

        `resistance` and `mass` are meant to be mutually exclusive with `material` and `cross_sectional_area`.
        If all are specified, `resistance` and `mass` take precedence.

        Parameters
        ----------
        points : np.ndarray[np.float64]
            A 2D array of the points that the wire connects.
        mass : np.float64
            The total mass of the wire in kilograms(kg). Greater than 0, by default 1.0.
        resistance : np.float64
            The total resistance of the wire in ohms(Ω). Greater than 0, by default 1.0.
        material : WireMaterial
            The material that the wire is composed of(e.g. copper, silver, and aluminum), by default `None`
        cross_sectional_area : np.float64
            The cross sectional area of the wire in meters squared(m^2), by default -1.0.
        """
        self.points = points
        self.velocity = np.zeros(shape=(len(points), 3))
        self.acceleration = np.zeros(shape=(len(points), 3))

        if material == None and cross_sectional_area == -1.0:
            self.mass = mass
            self.resistance = resistance

        else:
            length = self.get_length()
            self.mass = length * cross_sectional_area * \
                MATERIAL_DENSITIES[material]
            self.resistance = MATERIAL_RESISTIVITIES[material] * \
                length / cross_sectional_area

    def get_unit_vector(self) -> np.ndarray[np.float64]:
        """Get the unit vector in the direction of the wire from the first to last point.

        Returns
        -------
        np.ndarray[np.float64]
            A 3D vector representing the unit vector in the direction of the wire. 
        """
        wire_vector = self.points[1] - self.points[0]
        return wire_vector / np.linalg.norm(wire_vector)

    def get_wire_point(self, distance: np.float64) -> PositionVector:
        """Returns a point along the wire given a distance from the first point.

        Parameters
        ----------
        distance : np.float64
            The distance from the start of the wire. 

        Returns
        -------
        np.ndarray[np.float64]
            A 3D vector representing a point along the wire. 
        """
        return self.points[0] + self.get_unit_vector() * distance

    def get_center_of_mass(self) -> PositionVector:
        """Get the center of mass of this wire.
        
        Since the wire is uniform in linear density, the center of mass is in the middle.

        Returns
        -------
        PositionVector
            A 3D vector representing the position of the center of mass.
        """
        return (self.points[0] + self.points[1]) / 2.0

    def integrate_wire_segments(self, func: Callable) -> np.float64:
        """Perform a calculation on each segment of the wire and sum them.

        Parameters
        ----------
        func : Callable
            A function with a calculation to perform on each segment of the wire
        """
        total = 0

        # Loop through each segment of the wire
        for i in range(len(self.points) - 1):
            # The vector of the space between the points
            wire_vector = self.points[i+1] - self.points[i]
            unit_vector = wire_vector / np.linalg.norm(wire_vector)

            total += func()

        return total

    def get_length(self) -> np.float64:
        """Calculate the total length of the wire.

        Returns
        -------
        np.float64
            A scalar value representing the total length of this wire. 
        """
        # Sum the distance between each point
        length = 0
        for i in range(0, len(self.points) - 1):
            length += np.linalg.norm(self.points[i+1] - self.points[i])

        return length

    def get_electromotive_force(self, electric_field: Callable[[PositionVector], FieldVector]) -> np.float64:
        """Calculate the electromotive force(emf) generated across the wire.

        Parameters
        ----------
        electric_field : Callable
            A function that returns the electric field at any given point.

        Returns
        -------
        np.float64
            The electromotive force across this wire, measured in volts(V).
        """
        # Negative integral of the electric field across the wire.
        return -scipy.integrate.quad(
            lambda l: np.dot(
                electric_field(self.get_wire_point(l)),
                self.get_unit_vector()
            ),
            0,
            self.get_length()
        )[0]

    def get_current(self, electric_field: Callable) -> np.float64:
        """Calculate the current flowing through this wire.

        Parameters
        ----------
        electric_field : Callable
            A function that returns the electric field at any given point.

        Returns
        -------
        np.float64
            The current flowing through this wire, measured in amps(A).
        """
        return self.get_electromotive_force(electric_field) / self.resistance

    def get_magnetic_field(self, field_point: PositionVector, electric_field: Callable[[PositionVector], FieldVector]) -> FieldVector:
        """Calculate the magnetic field generated by this wire at a point.

        Parameters
        ----------
        field_point : np.ndarray[np.float64]
            A 3D vector of np.float64 representing a point to calculate the magnetic field at.
        electric_field : Callable
            A function that returns the electric field at any given point.

        Returns
        -------
        np.ndarray[np.float64]
            A 3D vector representing the strength of the magnetic field at the point in teslas. 
        """
        def r(l: np.float64) -> np.ndarray[np.float64]:
            """Calculate r, the 3D vector between the magnetic field point and the point of integration.

            Parameters
            ----------
            l : np.float64
                The distance along this wire from `start_point` in meters.

            Returns
            -------
            np.ndarray[np.float64]
                A 3D vector from the point of integration to `field_point`.
            """
            return field_point - self.get_wire_point(l)

        # Biot-Savart law
        biot_savart_constant = scipy.constants.mu_0 / (4 * scipy.constants.pi)
        return biot_savart_constant \
            * self.get_current(electric_field) \
            * scipy.integrate.quad_vec(
                lambda l: np.cross(
                    self.get_unit_vector(),
                    r(l) / np.linalg.norm(r(l)) ** 3
                ),
                0,
                self.get_length()
            )[0]

    def apply_force(self, force: ForceVector) -> None:
        """Apply a force to this wire. 

        Parameters
        ----------
        force : np.ndarray[np.float64]
            The force that is applied upon this wire.
        """
        

    def apply_magnetic_field(self, magnetic_field: Callable[[PositionVector], FieldVector]) -> None:
        """Apply a magnetic force to the wire based on a magnetic field.

        Parameters
        ----------
        magnetic_field : function
            A function that returns the magnetic field at any given point.
        """
        self.apply_force(
            scipy.integrate.quad_vec(
                lambda l: np.cross(
                    magnetic_field(l),
                    self.get_unit_vector()
                )
            )
        )


if __name__ == '__main__':
    points = np.array(
        (
            (-1e3, 0, 0),
            (1e3, 0, 0)
        )
    )

    wire = Wire(points, 1.0)
    constatnt_electric_field = np.array((100, 0.0, 0.0))
    particles = ()

    def electric_field(l: np.float64):
        return sum([particle.get_electric_field(
        wire.get_wire_point(l)) for particle in particles]) + constatnt_electric_field

    print(wire.get_current(electric_field))
    print()
    print(wire.get_magnetic_field(
        np.array((0.0, 0.0, 0.001)), electric_field))
