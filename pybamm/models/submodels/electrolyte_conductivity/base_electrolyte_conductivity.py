#
# Base class for electrolyte conductivity
#

import pybamm


class BaseElectrolyteConductivity(pybamm.BaseSubModel):
    """Base class for conservation of charge in the electrolyte.

    Parameters
    ----------
    param : parameter class
        The parameters to use for this submodel
    domain : str, optional
        The domain in which the model holds
    options : dict, optional
        A dictionary of options to be passed to the model.

    **Extends:** :class:`pybamm.BaseSubModel`
    """

    def __init__(self, param, domain=None, options=None):
        super().__init__(param, domain, options=options)

    def _get_standard_potential_variables(self, phi_e_n, phi_e_s, phi_e_p):
        """
        A private function to obtain the standard variables which
        can be derived from the potential in the electrolyte.

        Parameters
        ----------
        phi_e_n : :class:`pybamm.Symbol`
            The electrolyte potential in the negative electrode.
        phi_e_s : :class:`pybamm.Symbol`
            The electrolyte potential in the separator.
        phi_e_p : :class:`pybamm.Symbol`
            The electrolyte potential in the positive electrode.

        Returns
        -------
        variables : dict
            The variables which can be derived from the potential in the
            electrolyte.
        """

        param = self.param
        pot_scale = param.potential_scale

        phi_e = pybamm.concatenation(phi_e_n, phi_e_s, phi_e_p)

        if self.half_cell:
            # overwrite phi_e_n to be the boundary value of phi_e_s
            phi_e_n = pybamm.boundary_value(phi_e_s, "left")

        phi_e_n_av = pybamm.x_average(phi_e_n)
        phi_e_s_av = pybamm.x_average(phi_e_s)
        phi_e_p_av = pybamm.x_average(phi_e_p)
        eta_e_av = phi_e_p_av - phi_e_n_av
        phi_e_av = pybamm.x_average(phi_e)

        variables = {
            "Negative electrolyte potential": phi_e_n,
            "Negative electrolyte potential [V]": -param.U_n_ref + pot_scale * phi_e_n,
            "Separator electrolyte potential": phi_e_s,
            "Separator electrolyte potential [V]": -param.U_n_ref + pot_scale * phi_e_s,
            "Positive electrolyte potential": phi_e_p,
            "Positive electrolyte potential [V]": -param.U_n_ref + pot_scale * phi_e_p,
            "Electrolyte potential": phi_e,
            "Electrolyte potential [V]": -param.U_n_ref + pot_scale * phi_e,
            "X-averaged electrolyte potential": phi_e_av,
            "X-averaged electrolyte potential [V]": -param.U_n_ref
            + pot_scale * phi_e_av,
            "X-averaged negative electrolyte potential": phi_e_n_av,
            "X-averaged negative electrolyte potential [V]": -param.U_n_ref
            + pot_scale * phi_e_n_av,
            "X-averaged separator electrolyte potential": phi_e_s_av,
            "X-averaged separator electrolyte potential [V]": -param.U_n_ref
            + pot_scale * phi_e_s_av,
            "X-averaged positive electrolyte potential": phi_e_p_av,
            "X-averaged positive electrolyte potential [V]": -param.U_n_ref
            + pot_scale * phi_e_p_av,
            "X-averaged electrolyte overpotential": eta_e_av,
            "X-averaged electrolyte overpotential [V]": pot_scale * eta_e_av,
            "Gradient of separator electrolyte potential": pybamm.grad(phi_e_s),
            "Gradient of positive electrolyte potential": pybamm.grad(phi_e_p),
            "Gradient of electrolyte potential": pybamm.grad(phi_e),
        }

        if not self.half_cell:
            variables.update(
                {"Gradient of negative electrolyte potential": pybamm.grad(phi_e_n)}
            )

        return variables

    def _get_standard_current_variables(self, i_e):
        """
        A private function to obtain the standard variables which
        can be derived from the current in the electrolyte.

        Parameters
        ----------
        i_e : :class:`pybamm.Symbol`
            The current in the electrolyte.

        Returns
        -------
        variables : dict
            The variables which can be derived from the current in the
            electrolyte.
        """

        i_typ = self.param.i_typ
        variables = {
            "Electrolyte current density": i_e,
            "Electrolyte current density [A.m-2]": i_typ * i_e,
        }

        if isinstance(i_e, pybamm.Concatenation):
            i_e_n, _, i_e_p = i_e.orphans
            variables.update(self._get_domain_current_variables(i_e_n, "Negative"))
            variables.update(self._get_domain_current_variables(i_e_p, "Positive"))

        return variables

    def _get_split_overpotential(self, eta_c_av, delta_phi_e_av):
        """
        A private function to obtain the standard variables which
        can be derived from the electrode-averaged concentration
        overpotential and Ohmic losses in the electrolyte.

        Parameters
        ----------
        eta_c_av : :class:`pybamm.Symbol`
            The electrode-averaged concentration overpotential
        delta_phi_e_av: :class:`pybamm.Symbol`
            The electrode-averaged electrolyte Ohmic losses

        Returns
        -------
        variables : dict
            The variables which can be derived from the electrode-averaged
            concentration overpotential and Ohmic losses in the electrolyte
            electrolyte.
        """

        param = self.param
        pot_scale = param.potential_scale

        variables = {
            "X-averaged concentration overpotential": eta_c_av,
            "X-averaged electrolyte ohmic losses": delta_phi_e_av,
            "X-averaged concentration overpotential [V]": pot_scale * eta_c_av,
            "X-averaged electrolyte ohmic losses [V]": pot_scale * delta_phi_e_av,
        }

        return variables

    def _get_standard_surface_potential_difference_variables(self, delta_phi):
        """
        A private function to obtain the standard variables which
        can be derived from the surface potential difference.

        Parameters
        ----------
        delta_phi : :class:`pybamm.Symbol`
            The surface potential difference.

        Returns
        -------
        variables : dict
            The variables which can be derived from the surface potential difference.
        """

        if self.domain == "Negative":
            ocp_ref = self.param.U_n_ref
        elif self.domain == "Positive":
            ocp_ref = self.param.U_p_ref
        pot_scale = self.param.potential_scale

        # Average, and broadcast if necessary
        delta_phi_av = pybamm.x_average(delta_phi)
        if delta_phi.domain == []:
            delta_phi = pybamm.FullBroadcast(
                delta_phi, self.domain_for_broadcast, "current collector"
            )
        elif delta_phi.domain == ["current collector"]:
            delta_phi = pybamm.PrimaryBroadcast(delta_phi, self.domain_for_broadcast)

        variables = {
            self.domain + " electrode surface potential difference": delta_phi,
            "X-averaged "
            + self.domain.lower()
            + " electrode surface potential difference": delta_phi_av,
            self.domain
            + " electrode surface potential difference [V]": ocp_ref
            + delta_phi * pot_scale,
            "X-averaged "
            + self.domain.lower()
            + " electrode surface potential difference [V]": ocp_ref
            + delta_phi_av * pot_scale,
        }

        return variables

    def _get_domain_potential_variables(self, phi_e, domain=None):
        """
        A private function to obtain the standard variables which
        can be derived from the potential in the electrolyte split
        by domain: 'negative electrode', 'separator' and 'positive electrode'.

        Parameters
        ----------
        phi_e : :class:`pybamm.Symbol`
            The potential in the electrolyte within the domain 'domain'.

        Returns
        -------
        variables : dict
            The variables which can be derived from the potential in the
            electrolyte in domain 'domain'.
        """
        domain = domain or self.domain

        pot_scale = self.param.potential_scale
        phi_e_av = pybamm.x_average(phi_e)

        variables = {
            domain + " electrolyte potential": phi_e,
            domain + " electrolyte potential [V]": phi_e * pot_scale,
            "X-averaged " + domain.lower() + " electrolyte potential": phi_e_av,
            "X-averaged "
            + domain.lower()
            + " electrolyte potential [V]": phi_e_av * pot_scale,
        }

        return variables

    def _get_domain_current_variables(self, i_e, domain=None):
        """
        A private function to obtain the standard variables which
        can be derived from the current in the electrolyte split
        by domain: 'negative electrode', 'separator' and 'positive electrode'.

        Parameters
        ----------
        i_e : :class:`pybamm.Symbol`
            The current in the electrolyte within the domain 'domain'.

        Returns
        -------
        variables : dict
            The variables which can be derived from the current in the
            electrolyte in domain 'domain'.
        """
        domain = domain or self.domain

        i_typ = self.param.i_typ

        variables = {
            domain + " electrolyte current density": i_e,
            domain + " electrolyte current density [A.m-2]": i_e * i_typ,
        }

        return variables

    def _get_whole_cell_variables(self, variables):
        """
        A private function to obtain the potential and current concatenated
        across the whole cell. Note: requires 'variables' to contain the potential
        and current in the subdomains: 'negative electrode', 'separator', and
        'positive electrode'.

        Parameters
        ----------
        variables : dict
            The variables that have been set in the rest of the model.

        Returns
        -------
        variables : dict
            The variables including the whole-cell electrolyte potentials
            and currents.
        """

        phi_e_n = variables["Negative electrolyte potential"]
        phi_e_s = variables["Separator electrolyte potential"]
        phi_e_p = variables["Positive electrolyte potential"]

        i_e_n = variables["Negative electrolyte current density"]
        i_e_s = variables["Separator electrolyte current density"]
        i_e_p = variables["Positive electrolyte current density"]
        i_e = pybamm.concatenation(i_e_n, i_e_s, i_e_p)

        variables.update(
            self._get_standard_potential_variables(phi_e_n, phi_e_s, phi_e_p)
        )
        variables.update(self._get_standard_current_variables(i_e))

        return variables

    def _get_electrolyte_overpotentials(self, variables):
        """
        A private function to obtain the electrolyte overpotential and Ohmic losses.
        Note: requires 'variables' to contain the potential, electrolyte concentration
        and temperature the subdomains: 'negative electrode', 'separator', and
        'positive electrode'.

        Parameters
        ----------
        variables : dict
            The variables that have been set in the rest of the model.

        Returns
        -------
        variables : dict
            The variables including the whole-cell electrolyte potentials
            and currents.
        """
        param = self.param

        if self.half_cell:
            # No concentration overpotential in the counter electrode
            phi_e_n = pybamm.Scalar(0)
            indef_integral_n = pybamm.Scalar(0)
        else:
            phi_e_n = variables["Negative electrolyte potential"]
            # concentration overpotential
            c_e_n = variables["Negative electrolyte concentration"]
            T_n = variables["Negative electrode temperature"]
            indef_integral_n = pybamm.IndefiniteIntegral(
                param.chi(c_e_n, T_n)
                * (1 + param.Theta * T_n)
                * pybamm.grad(c_e_n)
                / c_e_n,
                pybamm.standard_spatial_vars.x_n,
            )

        phi_e_p = variables["Positive electrolyte potential"]

        c_e_s = variables["Separator electrolyte concentration"]
        c_e_p = variables["Positive electrolyte concentration"]

        T_s = variables["Separator temperature"]
        T_p = variables["Positive electrode temperature"]

        # concentration overpotential
        indef_integral_s = pybamm.IndefiniteIntegral(
            param.chi(c_e_s, T_s)
            * (1 + param.Theta * T_s)
            * pybamm.grad(c_e_s)
            / c_e_s,
            pybamm.standard_spatial_vars.x_s,
        )
        indef_integral_p = pybamm.IndefiniteIntegral(
            param.chi(c_e_p, T_p)
            * (1 + param.Theta * T_p)
            * pybamm.grad(c_e_p)
            / c_e_p,
            pybamm.standard_spatial_vars.x_p,
        )

        integral_n = indef_integral_n
        integral_s = indef_integral_s + pybamm.boundary_value(integral_n, "right")
        integral_p = indef_integral_p + pybamm.boundary_value(integral_s, "right")

        eta_c_av = pybamm.x_average(integral_p) - pybamm.x_average(integral_n)

        delta_phi_e_av = (
            pybamm.x_average(phi_e_p) - pybamm.x_average(phi_e_n) - eta_c_av
        )

        variables.update(self._get_split_overpotential(eta_c_av, delta_phi_e_av))

        return variables

    def set_boundary_conditions(self, variables):
        phi_e = variables["Electrolyte potential"]

        if self.half_cell:
            phi_s_cn = variables["Negative current collector potential"]
            delta_phi_s = variables["Negative electrode potential drop"]
            delta_phi = variables["Negative electrode surface potential difference"]

            phi_s = phi_s_cn - delta_phi_s
            phi_e_ref = phi_s - delta_phi
            lbc = (phi_e_ref, "Dirichlet")
        else:
            lbc = (pybamm.Scalar(0), "Neumann")
        self.boundary_conditions = {
            phi_e: {"left": lbc, "right": (pybamm.Scalar(0), "Neumann")}
        }
