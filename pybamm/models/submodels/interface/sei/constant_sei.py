#
# Class for constant SEI thickness
#
import pybamm
from .base_sei import BaseModel


class ConstantSEI(BaseModel):
    """
    Class for SEI with constant thickness.

    Note that there is no SEI current, so we don't need to update the "sum of
    interfacial current densities" variables from
    :class:`pybamm.interface.BaseInterface`

    Parameters
    ----------
    param : parameter class
        The parameters to use for this submodel

    **Extends:** :class:`pybamm.sei.BaseModel`
    """

    def __init__(self, param):
        super().__init__(param)

    def get_fundamental_variables(self):
        # Constant thicknesses
        L_inner = self.param.L_inner_0
        L_outer = self.param.L_outer_0
        variables = self._get_standard_thickness_variables(L_inner, L_outer)

        # Concentrations (derived from thicknesses)
        variables.update(self._get_standard_concentration_variables(variables))

        # Reactions
        zero = pybamm.FullBroadcast(
            pybamm.Scalar(0), "negative electrode", "current collector"
        )
        variables.update(self._get_standard_reaction_variables(zero, zero))

        return variables
