from pytest_check import check
import numpy as np

import fenics
import fenics_adjoint as fa
import ufl

import fdm

import theano
theano.config.optimizer='fast_compile'
theano.config.exception_verbosity='high'
# theano.config.compute_test_value = 'warn'
# theano.config.compute_test_value = "ignore"

# from fenics_pymc3 import fem_eval, vjp_fem_eval_impl
from fenics_pymc3 import fenics_to_numpy, numpy_to_fenics
from fenics_pymc3 import create_fenics_theano_op


mesh = fa.UnitSquareMesh(3, 2)
V = fenics.FunctionSpace(mesh, "P", 1)


def assemble_fenics(u, kappa0, kappa1):

    f = fa.Expression(
        "10*exp(-(pow(x[0] - 0.5, 2) + pow(x[1] - 0.5, 2)) / 0.02)", degree=2
    )

    inner, grad, dx = ufl.inner, ufl.grad, ufl.dx
    J_form = 0.5 * inner(kappa0 * grad(u), grad(u)) * dx - kappa1 * f * u * dx
    J = fa.assemble(J_form)
    return J


templates = (fa.Function(V), fa.Constant(0.0), fa.Constant(0.0))
inputs = (np.ones(V.dim()), np.ones(1) * 0.5, np.ones(1) * 0.6)
# ff = lambda *args: fem_eval(assemble_fenics, templates, *args)[0]  # noqa: E731
# ff0 = lambda x: ff(x, inputs[1], inputs[2])  # noqa: E731
# ff1 = lambda y: ff(inputs[0], y, inputs[2])  # noqa: E731
# ff2 = lambda z: ff(inputs[0], inputs[1], z)  # noqa: E731


# def test_fenics_forward():
#     numpy_output, _, _, _, = fem_eval(assemble_fenics, templates, *inputs)
#     u1 = fa.interpolate(fa.Constant(1.0), V)
#     J = assemble_fenics(u1, fa.Constant(0.5), fa.Constant(0.6))
#     assert np.isclose(numpy_output, J)


# def test_vjp_assemble_eval():
#     numpy_output, fenics_output, fenics_inputs, tape = fem_eval(
#         assemble_fenics, templates, *inputs
#     )
#     g = np.ones_like(numpy_output)
#     vjp_out = vjp_fem_eval_impl(g, fenics_output, fenics_inputs, tape)

#     fdm_jac0 = fdm.jacobian(ff0)(inputs[0])
#     fdm_jac1 = fdm.jacobian(ff1)(inputs[1])
#     fdm_jac2 = fdm.jacobian(ff2)(inputs[2])

#     check1 = np.allclose(vjp_out[0], fdm_jac0)
#     check2 = np.allclose(vjp_out[1], fdm_jac1)
#     check3 = np.allclose(vjp_out[2], fdm_jac2)
#     assert check1 and check2 and check3


hh = create_fenics_theano_op(templates)(assemble_fenics)

from fenics_pymc3 import create_fenics_theano_vjp_op
gg = create_fenics_theano_vjp_op(templates)(assemble_fenics)

x = theano.tensor.vector()
y = theano.tensor.vector()
z = theano.tensor.vector()
g = theano.tensor.vector()
f = theano.function([g, x, y, z], gg(g, x, y, z))#, on_unused_input='warn')
f(np.ones(1), *inputs)

##

x = theano.tensor.vector()
y = theano.tensor.vector()
z = theano.tensor.vector()
g = theano.tensor.vector()

o = hh(x, y, z)

o1 = theano.tensor.sum(o)
gs = theano.grad(o1, x)

# theano.tensor.Lop(o, [x, y, z], g)

import theano.tests.unittest_tools

f = theano.function([x, y, z], hh(x, y, z))

f(*inputs)

# dodx = theano.grad(theano.tensor.sum(o), x)
# g = theano.tensor.scalar()
# f_grad = theano.function([g], dodx)

VJ = theano.tensor.Lop(o, [x, y, z], g)
fg = theano.function([g, x, y, z], VJ)