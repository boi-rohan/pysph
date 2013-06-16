"""Mixing/Unmixing problem to test periodicity and/or SPH integrators

The problem is purely kinematical with a fluid in a doubly periodic
box [0,1] X [0,1] subjected to a velocity profile :

u(x, y) = cos(pi t/T)*sin^2(pi x) * sin(2*pi y)
v(x, y) = -cos(pi t/T)*sin^2(pi y) * sin(2*pi x)

which is divergence free and periodic with period T. After a time of
one period, the fluid should return to it's original position which
can be used to check for the accuracy of the numeircal integration.

An additional color function phi(x, y) = cos(2 pi x) * cos(4 pi y) can
be used to visualize the mixing/unmixing of this problem.

I picked up this test from the paper "3DFLUX: A high-order fully
three-dimensional flux integral solver for the scalar transport
equation", Emmanuel Germaine, Laurent Mydlarski, Luca Cortelezzi, JCP
(240), 2013, pp 121-144

"""
# PyZoltan imports
from pyzoltan.core.carray import LongArray

# PySPH imports
from pysph.base.nnps import DomainLimits
from pysph.base.utils import get_particle_array_wcsph
from pysph.base.kernels import Gaussian, WendlandQuintic, CubicSpline
from pysph.solver.solver import Solver
from pysph.solver.application import Application
from pysph.sph.integrator import EulerIntegrator

# the eqations
from pysph.sph.equations import Group
from pysph.sph.advection_equations import Advect, MixingVelocityUpdate

# numpy
import numpy as np

# domain and constants
L = 1.0; T = 0.1

# Numerical setup
nx = 50; dx = L/nx
hdx = 1.2

def create_particles(empty=False, **kwargs):
    if empty:
        fluid = get_particle_array_wcsph(name='fluid')
    else:
        # create the particles
        _x = np.arange( dx/2, L, dx )
        x, y = np.meshgrid(_x, _x); x = x.ravel(); y = y.ravel()
        h = np.ones_like(x) * dx

        # create the arrays
        fluid = get_particle_array_wcsph(name='fluid', x=x, y=y, h=h)
    
        # add the requisite arrays
        fluid.add_property( {'name': 'color'} )
        fluid.add_property( {'name': 'ax'} )
        fluid.add_property( {'name': 'ay'} )
        fluid.add_property( {'name': 'az'} )

        fluid.add_property( {'name': 'u0'} )
        fluid.add_property( {'name': 'v0'} )

        print "Advection mixing problem :: nfluid = %d"%(
            fluid.get_number_of_particles())

        # setup the particle properties
        pi = np.pi; cos = np.cos; sin=np.sin

        # color
        fluid.color[:] = cos(2*pi*x) * cos(4*pi*y)

        # velocities
        fluid.u0[:] = +sin(pi*x)*sin(pi*x) * sin(2*pi*y)
        fluid.v0[:] = -sin(pi*y)*sin(pi*y) * sin(2*pi*x)
                
    # return the particle list
    return [fluid,]

# domain for periodicity
domain = DomainLimits(xmin=0, xmax=L, ymin=0, ymax=L, 
                      periodic_in_x=True, periodic_in_y=True)

# Create the application.
app = Application(domain=domain)

# Create the kernel
kernel = WendlandQuintic(dim=2)

# Create a solver.
solver = Solver(
    kernel=kernel, dim=2, integrator_type=EulerIntegrator)

# Setup default parameters.
solver.set_time_step(1e-3)
solver.set_final_time(T)

equations = [

    # Update velocities and advect
    Group(
        equations=[
            MixingVelocityUpdate(
                dest='fluid', sources=None, T=T),

            Advect(dest='fluid', sources=None)
            ])
    
    ]

# Setup the application and solver.  This also generates the particles.
app.setup(solver=solver, equations=equations, 
          particle_factory=create_particles)

with open('mixing.pyx', 'w') as f:
    app.dump_code(f)

app.run()