import sys

from matplotlib import pyplot as plt
import numpy as np
import scipy.constants

from files import Files
from particle import Particle
from plot import Plot

class Simulation():
    def __init__(self, particles: list, num_ticks: int, tick_size: float = 1.0) -> None:
        """Initiate one simulation.

        Parameters
        ----------
        particles : list
            A list of particles that are interacting with each other
        num_ticks: int
            The number of ticks that the simulation runs for
        tick_size : float, optional
            The amount of time between each tick in seconds, by default 1.0
        """
        self.particles = particles
        self.particle_positions = np.empty((len(self.particles), num_ticks, 3))

        # Constant, universal fields
        self.electric_field = np.zeros(3)
        self.magnetic_field = np.zeros(3)
        self.gravitational_field = np.zeros(3)

        self.num_ticks = num_ticks
        self.current_tick = 0
        self.tick_size = tick_size

    def tick(self) -> None:
        """Run one tick of the simulation(i.e. the time specified by `tick_size`).
        """
        # Calculate the electrostatic force that the particles exert on each other
        # Update the particle's acceleration and and velocity, but not the position
        for particle1 in self.particles:
            print(particle1.position)
            net_force = 0

            # Calculate the forces from the other particles
            for particle2 in self.particles:
                if particle1 != particle2:
                    net_force += particle1.coulombs_law(particle2)
                    net_force += particle1.biot_savart_law(particle2)
                    net_force += particle1.gravity(particle2)

            # Add the constant fields
            net_force += particle1.charge * self.electric_field
            net_force += particle1.charge * np.cross(particle1.velocity, self.magnetic_field)
            net_force += particle1.mass * self.gravitational_field

            # Apply the force to the particle's acceleration and update its velocity
            particle1.apply_force(net_force)
            particle1.velocity += particle1.acceleration * self.tick_size

        # Update position after calculating the force, so it doesn't affect the force calculations
        for i in range(len(self.particles)):
            particle = self.particles[i]
            
            self.particle_positions[i][self.current_tick] = particle.position
            particle.position += particle.velocity * self.tick_size

        self.current_tick += 1
        print()

    def run(self, ticks_to_run: int = None) -> None:
        """Run the simulation for a given number of ticks. 

        Parameters
        ----------
        ticks_to_run : int, optional
            The number of ticks that the simulation runs by, by default `self.num_ticks`
        """
        if ticks_to_run == None:
            ticks_to_run = self.num_ticks

        for i in range(ticks_to_run):
            simulation.tick()

if __name__ == '__main__':
    # Check if the user supplied a config file
    if len(sys.argv) < 2:
        raise ValueError('Please enter the name of the config file.')

    # Read the config file data and create particles based on that data
    file_data = Files.read_config_file(sys.argv[1])

    particles = [
        Particle(
            np.array((line[0], line[1], line[2])),
            line[3],
            line[4]
        )
        for line in file_data
    ]

    simulation = Simulation(particles, num_ticks=100, tick_size=0.1)
    simulation.gravitational_field = np.array((0, 0, -scipy.constants.g))
    simulation.run()
    
    plot = Plot(simulation.particle_positions, tick_size=simulation.tick_size)