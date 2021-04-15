##############################################################################
# Institute for the Design of Advanced Energy Systems Process Systems
# Engineering Framework (IDAES PSE Framework) Copyright (c) 2018-2020, by the
# software owners: The Regents of the University of California, through
# Lawrence Berkeley National Laboratory,  National Technology & Engineering
# Solutions of Sandia, LLC, Carnegie Mellon University, West Virginia
# University Research Corporation, et al. All rights reserved.
#
# Please see the files COPYRIGHT.txt and LICENSE.txt for full copyright and
# license information, respectively. Both files are also available online
# at the URL "https://github.com/IDAES/idaes-pse".
##############################################################################
"""
Tests for eNRTL methods

Author: Andrew Lee
"""
import pytest

from pyomo.environ import (ConcreteModel,
                           Expression,
                           exp,
                           log,
                           Set,
                           Var,
                           units as pyunits)

from idaes.core import (AqueousPhase,
                        Solvent,
                        Solute,
                        Apparent,
                        Anion,
                        Cation)
from idaes.generic_models.properties.core.eos.enrtl import ENRTL
from idaes.generic_models.properties.core.generic.generic_property import (
        GenericParameterBlock)
from idaes.generic_models.properties.core.state_definitions import FTPx
from idaes.core.util.exceptions import ConfigurationError
import idaes.logger as idaeslog


configuration = {
    "components": {
        "H2O": {"type": Solvent},
        "C6H12": {"type": Solute},
        "NaCl": {"type": Apparent,
                 "dissociation_species": {"Na+": 1, "Cl-": 1}},
        "HCl": {"type": Apparent,
                "dissociation_species": {"H+": 1, "Cl-": 1}},
        "NaOH": {"type": Apparent,
                 "dissociation_species": {"Na+": 1, "OH-": 1}},
        "Na+": {"type": Cation,
                "charge": +1},
        "H+": {"type": Cation,
               "charge": +1},
        "Cl-": {"type": Anion,
                "charge": -1},
        "OH-": {"type": Anion,
                "charge": -1}},
    "phases": {
        "Liq": {"type": AqueousPhase,
                "equation_of_state": ENRTL}},
    "base_units": {"time": pyunits.s,
                   "length": pyunits.m,
                   "mass": pyunits.kg,
                   "amount": pyunits.mol,
                   "temperature": pyunits.K},
    "state_definition": FTPx,
    "pressure_ref": 1e5,
    "temperature_ref": 300}


class TestParameters(object):
    @pytest.mark.unit
    def test_parameters_no_assignment(self):
        m = ConcreteModel()

        m.params = GenericParameterBlock(default=configuration)

        assert isinstance(m.params.Liq.ion_pair_set, Set)
        assert len(m.params.Liq.ion_pair_set) == 4
        for p in m.params.Liq.ion_pair_set:
            assert p in [("Na+, Cl-"), ("Na+, OH-"),
                         ("H+, Cl-"), ("H+, OH-")]

        assert isinstance(m.params.Liq.component_pair_set, Set)
        assert len(m.params.Liq.component_pair_set) == 30
        assert isinstance(m.params.Liq.component_pair_set_symmetric, Set)
        assert len(m.params.Liq.component_pair_set_symmetric) == 15

        assert isinstance(m.params.Liq.alpha, Var)
        assert len(m.params.Liq.alpha) == 15
        for (i, j) in m.params.Liq.alpha:
            if i != j:
                assert (j, i) not in m.params.Liq.alpha
            if (i, j) in [
                    ("C6H12", "C6H12"), ("H2O", "H2O"), ("H2O", "C6H12")]:
                assert m.params.Liq.alpha[(i, j)].value == 0.3
                assert m.params.Liq.alpha[(i, j)].fixed
            else:
                assert m.params.Liq.alpha[(i, j)].value == 0.2
                assert m.params.Liq.alpha[(i, j)].fixed

        assert isinstance(m.params.Liq.tau, Var)
        assert len(m.params.Liq.tau) == 30
        for (i, j) in m.params.Liq.tau:
            assert m.params.Liq.tau[(i, j)].value == 0
            assert m.params.Liq.tau[(i, j)].fixed

    @pytest.mark.unit
    def test_parameters_assignment(self):
        test_config = dict(configuration)
        test_config["parameter_data"] = {}
        test_config["parameter_data"]["Liq_alpha"] = {}
        test_config["parameter_data"]["Liq_alpha"][("H2O", "Na+, Cl-")] = 0.6
        test_config["parameter_data"]["Liq_tau"] = {}
        test_config["parameter_data"]["Liq_tau"][("H2O", "Na+, Cl-")] = 0.1

        m = ConcreteModel()

        m.params = GenericParameterBlock(default=test_config)

        assert isinstance(m.params.Liq.alpha, Var)
        assert len(m.params.Liq.alpha) == 15
        for (i, j) in m.params.Liq.alpha:
            if i != j:
                assert (j, i) not in m.params.Liq.alpha
            if (i, j) == ("H2O", "Na+, Cl-"):
                assert m.params.Liq.alpha[(i, j)].value == 0.6
                assert m.params.Liq.alpha[(i, j)].fixed
            elif (i, j) in [
                    ("C6H12", "C6H12"), ("H2O", "H2O"), ("H2O", "C6H12")]:
                assert m.params.Liq.alpha[(i, j)].value == 0.3
                assert m.params.Liq.alpha[(i, j)].fixed
            else:
                assert m.params.Liq.alpha[(i, j)].value == 0.2
                assert m.params.Liq.alpha[(i, j)].fixed

        assert isinstance(m.params.Liq.tau, Var)
        assert len(m.params.Liq.tau) == 30
        for (i, j) in m.params.Liq.tau:
            print(i, j)
            if (i, j) == ("H2O", "Na+, Cl-"):
                assert m.params.Liq.tau[(i, j)].value == 0.1
                assert m.params.Liq.tau[(i, j)].fixed
            else:
                assert m.params.Liq.tau[(i, j)].value == 0
                assert m.params.Liq.tau[(i, j)].fixed

    @pytest.mark.unit
    def test_parameters_unsymmetric_alpha(self):
        test_config = dict(configuration)
        test_config["parameter_data"] = {}
        test_config["parameter_data"]["Liq_alpha"] = {}
        test_config["parameter_data"]["Liq_alpha"][("H2O", "Na+, Cl-")] = 0.6
        test_config["parameter_data"]["Liq_alpha"][("Na+, Cl-", "H2O")] = 0.8

        m = ConcreteModel()

        # TODO: Having trouble getting regex to match component tuple
        # Using a wildcard for now
        with pytest.raises(ConfigurationError,
                           match="params.Liq eNRTL alpha parameter assigned "
                           "non-symmetric value for pair (.+?). Please assign "
                           "only one value for component pair."):
            m.params = GenericParameterBlock(default=test_config)

    @pytest.mark.unit
    def test_parameters_alpha_symmetry_duplicate(self, caplog):
        caplog.set_level(
            idaeslog.INFO,
            logger=("idaes.generic_models.properties.core."
                    "generic.generic_property"))

        test_config = dict(configuration)
        test_config["parameter_data"] = {}
        test_config["parameter_data"]["Liq_alpha"] = {}
        test_config["parameter_data"]["Liq_alpha"][("H2O", "Na+, Cl-")] = 0.6
        test_config["parameter_data"]["Liq_alpha"][("Na+, Cl-", "H2O")] = 0.6

        m = ConcreteModel()

        m.params = GenericParameterBlock(default=test_config)

        assert ("eNRTL alpha value provided for both ('H2O', 'Na+, Cl-') and "
                "('Na+, Cl-', 'H2O'). It is only necessary to provide a "
                "value for one of these due to symmetry." in caplog.text)

    @pytest.mark.unit
    def test_parameters_alpha_unused_parameter(self):
        test_config = dict(configuration)
        test_config["parameter_data"] = {}
        test_config["parameter_data"]["Liq_alpha"] = {}
        test_config["parameter_data"]["Liq_alpha"][("H2O", "Na+")] = 0.6

        m = ConcreteModel()

        # TODO: Having trouble getting regex to match component tuple
        # Using a wildcard for now
        with pytest.raises(ConfigurationError,
                           match="params.Liq eNRTL alpha parameter provided "
                           "for invalid component pair (.+?). Please check "
                           "typing and only provide parameters for valid "
                           "species pairs."):
            m.params = GenericParameterBlock(default=test_config)

    @pytest.mark.unit
    def test_parameters_tau_asymmetric(self):
        test_config = dict(configuration)
        test_config["parameter_data"] = {}
        test_config["parameter_data"]["Liq_tau"] = {}
        test_config["parameter_data"]["Liq_tau"][("H2O", "Na+, Cl-")] = 0.1
        test_config["parameter_data"]["Liq_tau"][("Na+, Cl-", "H2O")] = -0.1

        m = ConcreteModel()

        m.params = GenericParameterBlock(default=test_config)

        assert isinstance(m.params.Liq.tau, Var)
        assert len(m.params.Liq.tau) == 30
        for (i, j) in m.params.Liq.tau:
            print(i, j)
            if (i, j) == ("H2O", "Na+, Cl-"):
                assert m.params.Liq.tau[(i, j)].value == 0.1
                assert m.params.Liq.tau[(i, j)].fixed
            elif (i, j) == ("Na+, Cl-", "H2O"):
                assert m.params.Liq.tau[(i, j)].value == -0.1
                assert m.params.Liq.tau[(i, j)].fixed
            else:
                assert m.params.Liq.tau[(i, j)].value == 0
                assert m.params.Liq.tau[(i, j)].fixed

    @pytest.mark.unit
    def test_parameters_tau_unused_parameter(self):
        test_config = dict(configuration)
        test_config["parameter_data"] = {}
        test_config["parameter_data"]["Liq_tau"] = {}
        test_config["parameter_data"]["Liq_tau"][("H2O", "Na+")] = 0.6

        m = ConcreteModel()

        # TODO: Having trouble getting regex to match component tuple
        # Using a wildcard for now
        with pytest.raises(ConfigurationError,
                           match="params.Liq eNRTL tau parameter provided for "
                           "invalid component pair (.+?). Please check typing "
                           "and only provide parameters for valid species "
                           "pairs."):
            m.params = GenericParameterBlock(default=test_config)


class TestStateBlock(object):
    @pytest.fixture(scope="class")
    def model(self):
        m = ConcreteModel()
        m.params = GenericParameterBlock(default=configuration)

        m.state = m.params.build_state_block([1])

        return m

    @pytest.mark.unit
    def test_common(self, model):
        assert isinstance(model.state[1].Liq_X, Expression)
        assert len(model.state[1].Liq_X) == 6
        for j in model.state[1].Liq_X:
            if j in ["H2O", "C6H12"]:
                # _X should be mole_frac_phase_comp_true
                assert (
                    str(model.state[1].Liq_X[j]._expr) ==
                    str(model.state[1].mole_frac_phase_comp_true["Liq", j]))
            else:
                # _X should be mutiplied by charge
                assert (
                    str(model.state[1].Liq_X[j]._expr) ==
                    str(model.state[1].mole_frac_phase_comp_true["Liq", j] *
                        model.params.get_component(j).config.charge))

        assert isinstance(model.state[1].Liq_Y, Expression)
        assert len(model.state[1].Liq_Y) == 4
        for j in model.state[1].Liq_Y:
            if j in ["H+", "Na+"]:
                assert (str(model.state[1].Liq_Y[j]._expr) ==
                        str(model.state[1].Liq_X[j] /
                            (model.state[1].Liq_X["Na+"] +
                             model.state[1].Liq_X["H+"])))
            else:
                assert (str(model.state[1].Liq_Y[j]._expr) ==
                        str(model.state[1].Liq_X[j] /
                            (model.state[1].Liq_X["Cl-"] +
                             model.state[1].Liq_X["OH-"])))

    @pytest.mark.unit
    def test_alpha(self, model):
        assert isinstance(model.state[1].Liq_alpha, Expression)
        assert len(model.state[1].Liq_alpha) == 26

        # Molecule-molecule interactions
        assert (model.state[1].Liq_alpha["H2O", "C6H12"].expr ==
                model.params.Liq.alpha["H2O", "C6H12"])
        assert (model.state[1].Liq_alpha["C6H12", "H2O"].expr ==
                model.params.Liq.alpha["H2O", "C6H12"])

        # Molecule-ion interactions
        assert (model.state[1].Liq_alpha["H2O", "Na+"].expr ==
                (model.state[1].Liq_Y["Cl-"] *
                 model.params.Liq.alpha["H2O", "Na+, Cl-"] +
                 model.state[1].Liq_Y["OH-"] *
                 model.params.Liq.alpha["H2O", "Na+, OH-"]))
        assert (model.state[1].Liq_alpha["H2O", "H+"].expr ==
                (model.state[1].Liq_Y["Cl-"] *
                 model.params.Liq.alpha["H2O", "H+, Cl-"] +
                 model.state[1].Liq_Y["OH-"] *
                 model.params.Liq.alpha["H2O", "H+, OH-"]))
        assert (model.state[1].Liq_alpha["Na+", "H2O"].expr ==
                (model.state[1].Liq_Y["Cl-"] *
                 model.params.Liq.alpha["H2O", "Na+, Cl-"] +
                 model.state[1].Liq_Y["OH-"] *
                 model.params.Liq.alpha["H2O", "Na+, OH-"]))
        assert (model.state[1].Liq_alpha["H+", "H2O"].expr ==
                (model.state[1].Liq_Y["Cl-"] *
                 model.params.Liq.alpha["H2O", "H+, Cl-"] +
                 model.state[1].Liq_Y["OH-"] *
                 model.params.Liq.alpha["H2O", "H+, OH-"]))
        assert (model.state[1].Liq_alpha["H2O", "Cl-"].expr ==
                (model.state[1].Liq_Y["Na+"] *
                 model.params.Liq.alpha["H2O", "Na+, Cl-"] +
                 model.state[1].Liq_Y["H+"] *
                 model.params.Liq.alpha["H2O", "H+, Cl-"]))
        assert (model.state[1].Liq_alpha["H2O", "OH-"].expr ==
                (model.state[1].Liq_Y["Na+"] *
                 model.params.Liq.alpha["H2O", "Na+, OH-"] +
                 model.state[1].Liq_Y["H+"] *
                 model.params.Liq.alpha["H2O", "H+, OH-"]))
        assert (model.state[1].Liq_alpha["Cl-", "H2O"].expr ==
                (model.state[1].Liq_Y["Na+"] *
                 model.params.Liq.alpha["H2O", "Na+, Cl-"] +
                 model.state[1].Liq_Y["H+"] *
                 model.params.Liq.alpha["H2O", "H+, Cl-"]))
        assert (model.state[1].Liq_alpha["OH-", "H2O"].expr ==
                (model.state[1].Liq_Y["Na+"] *
                 model.params.Liq.alpha["H2O", "Na+, OH-"] +
                 model.state[1].Liq_Y["H+"] *
                 model.params.Liq.alpha["H2O", "H+, OH-"]))

        assert (model.state[1].Liq_alpha["C6H12", "Na+"].expr ==
                (model.state[1].Liq_Y["Cl-"] *
                 model.params.Liq.alpha["C6H12", "Na+, Cl-"] +
                 model.state[1].Liq_Y["OH-"] *
                 model.params.Liq.alpha["C6H12", "Na+, OH-"]))
        assert (model.state[1].Liq_alpha["C6H12", "H+"].expr ==
                (model.state[1].Liq_Y["Cl-"] *
                 model.params.Liq.alpha["C6H12", "H+, Cl-"] +
                 model.state[1].Liq_Y["OH-"] *
                 model.params.Liq.alpha["C6H12", "H+, OH-"]))
        assert (model.state[1].Liq_alpha["Na+", "C6H12"].expr ==
                (model.state[1].Liq_Y["Cl-"] *
                 model.params.Liq.alpha["C6H12", "Na+, Cl-"] +
                 model.state[1].Liq_Y["OH-"] *
                 model.params.Liq.alpha["C6H12", "Na+, OH-"]))
        assert (model.state[1].Liq_alpha["H+", "C6H12"].expr ==
                (model.state[1].Liq_Y["Cl-"] *
                 model.params.Liq.alpha["C6H12", "H+, Cl-"] +
                 model.state[1].Liq_Y["OH-"] *
                 model.params.Liq.alpha["C6H12", "H+, OH-"]))
        assert (model.state[1].Liq_alpha["C6H12", "Cl-"].expr ==
                (model.state[1].Liq_Y["Na+"] *
                 model.params.Liq.alpha["C6H12", "Na+, Cl-"] +
                 model.state[1].Liq_Y["H+"] *
                 model.params.Liq.alpha["C6H12", "H+, Cl-"]))
        assert (model.state[1].Liq_alpha["C6H12", "OH-"].expr ==
                (model.state[1].Liq_Y["Na+"] *
                 model.params.Liq.alpha["C6H12", "Na+, OH-"] +
                 model.state[1].Liq_Y["H+"] *
                 model.params.Liq.alpha["C6H12", "H+, OH-"]))
        assert (model.state[1].Liq_alpha["Cl-", "C6H12"].expr ==
                (model.state[1].Liq_Y["Na+"] *
                 model.params.Liq.alpha["C6H12", "Na+, Cl-"] +
                 model.state[1].Liq_Y["H+"] *
                 model.params.Liq.alpha["C6H12", "H+, Cl-"]))
        assert (model.state[1].Liq_alpha["OH-", "C6H12"].expr ==
                (model.state[1].Liq_Y["Na+"] *
                 model.params.Liq.alpha["C6H12", "Na+, OH-"] +
                 model.state[1].Liq_Y["H+"] *
                 model.params.Liq.alpha["C6H12", "H+, OH-"]))

        # Ion-ion interactions
        assert (model.state[1].Liq_alpha["Na+", "Cl-"].expr ==
                (model.state[1].Liq_Y["H+"] *
                 model.params.Liq.alpha["Na+, Cl-", "H+, Cl-"]))
        assert (model.state[1].Liq_alpha["Na+", "OH-"].expr ==
                (model.state[1].Liq_Y["H+"] *
                 model.params.Liq.alpha["Na+, OH-", "H+, OH-"]))
        assert (model.state[1].Liq_alpha["H+", "Cl-"].expr ==
                (model.state[1].Liq_Y["Na+"] *
                 model.params.Liq.alpha["Na+, Cl-", "H+, Cl-"]))
        assert (model.state[1].Liq_alpha["H+", "OH-"].expr ==
                (model.state[1].Liq_Y["Na+"] *
                 model.params.Liq.alpha["Na+, OH-", "H+, OH-"]))
        assert (model.state[1].Liq_alpha["Cl-", "Na+"].expr ==
                (model.state[1].Liq_Y["OH-"] *
                 model.params.Liq.alpha["Na+, Cl-", "Na+, OH-"]))
        assert (model.state[1].Liq_alpha["Cl-", "H+"].expr ==
                (model.state[1].Liq_Y["OH-"] *
                 model.params.Liq.alpha["H+, Cl-", "H+, OH-"]))
        assert (model.state[1].Liq_alpha["OH-", "Na+"].expr ==
                (model.state[1].Liq_Y["Cl-"] *
                 model.params.Liq.alpha["Na+, Cl-", "Na+, OH-"]))
        assert (model.state[1].Liq_alpha["OH-", "H+"].expr ==
                (model.state[1].Liq_Y["Cl-"] *
                 model.params.Liq.alpha["H+, Cl-", "H+, OH-"]))

        # Like species interactions
        assert ("H2O", "H2O") not in model.state[1].Liq_alpha
        assert ("C6H12", "C6H12") not in model.state[1].Liq_alpha
        assert ("Na+", "Na+") not in model.state[1].Liq_alpha
        assert ("Na+", "H+") not in model.state[1].Liq_alpha
        assert ("H+", "Na+") not in model.state[1].Liq_alpha
        assert ("H+", "H+") not in model.state[1].Liq_alpha
        assert ("Cl-", "Cl-") not in model.state[1].Liq_alpha
        assert ("Cl-", "OH-") not in model.state[1].Liq_alpha
        assert ("OH-", "Cl-") not in model.state[1].Liq_alpha
        assert ("OH-", "OH-") not in model.state[1].Liq_alpha

    @pytest.mark.unit
    def test_G(self, model):
        assert isinstance(model.state[1].Liq_G, Expression)
        assert len(model.state[1].Liq_G) == 26

        # Molecule-molecule interactions
        assert (model.state[1].Liq_G["H2O", "C6H12"].expr ==
                exp(-model.params.Liq.alpha["H2O", "C6H12"] *
                    model.params.Liq.tau["H2O", "C6H12"]))
        assert (model.state[1].Liq_G["C6H12", "H2O"].expr ==
                exp(-model.params.Liq.alpha["H2O", "C6H12"] *
                    model.params.Liq.tau["H2O", "C6H12"]))

        # Molecule-ion interactions
        assert (model.state[1].Liq_G["H2O", "Na+"].expr ==
                (model.state[1].Liq_Y["Cl-"] *
                 exp(-model.params.Liq.alpha["H2O", "Na+, Cl-"] *
                     model.params.Liq.tau["H2O", "Na+, Cl-"]) +
                 model.state[1].Liq_Y["OH-"] *
                 exp(-model.params.Liq.alpha["H2O", "Na+, OH-"] *
                     model.params.Liq.tau["H2O", "Na+, OH-"])))
        assert (model.state[1].Liq_G["H2O", "H+"].expr ==
                (model.state[1].Liq_Y["Cl-"] *
                 exp(-model.params.Liq.alpha["H2O", "H+, Cl-"] *
                     model.params.Liq.tau["H2O", "H+, Cl-"]) +
                 model.state[1].Liq_Y["OH-"] *
                 exp(-model.params.Liq.alpha["H2O", "H+, OH-"] *
                     model.params.Liq.tau["H2O", "H+, OH-"])))
        assert (model.state[1].Liq_G["Na+", "H2O"].expr ==
                (model.state[1].Liq_Y["Cl-"] *
                 exp(-model.params.Liq.alpha["H2O", "Na+, Cl-"] *
                     model.params.Liq.tau["H2O", "Na+, Cl-"]) +
                 model.state[1].Liq_Y["OH-"] *
                 exp(-model.params.Liq.alpha["H2O", "Na+, OH-"] *
                     model.params.Liq.tau["H2O", "Na+, OH-"])))
        assert (model.state[1].Liq_G["H+", "H2O"].expr ==
                (model.state[1].Liq_Y["Cl-"] *
                 exp(-model.params.Liq.alpha["H2O", "H+, Cl-"] *
                     model.params.Liq.tau["H2O", "H+, Cl-"]) +
                 model.state[1].Liq_Y["OH-"] *
                 exp(-model.params.Liq.alpha["H2O", "H+, OH-"] *
                     model.params.Liq.tau["H2O", "H+, OH-"])))
        assert (model.state[1].Liq_G["H2O", "Cl-"].expr ==
                (model.state[1].Liq_Y["Na+"] *
                 exp(-model.params.Liq.alpha["H2O", "Na+, Cl-"] *
                     model.params.Liq.tau["H2O", "Na+, Cl-"]) +
                 model.state[1].Liq_Y["H+"] *
                 exp(-model.params.Liq.alpha["H2O", "H+, Cl-"] *
                     model.params.Liq.tau["H2O", "H+, Cl-"])))
        assert (model.state[1].Liq_G["H2O", "OH-"].expr ==
                (model.state[1].Liq_Y["Na+"] *
                 exp(-model.params.Liq.alpha["H2O", "Na+, OH-"] *
                     model.params.Liq.tau["H2O", "Na+, OH-"]) +
                 model.state[1].Liq_Y["H+"] *
                 exp(-model.params.Liq.alpha["H2O", "H+, OH-"] *
                     model.params.Liq.tau["H2O", "H+, OH-"])))
        assert (model.state[1].Liq_G["Cl-", "H2O"].expr ==
                (model.state[1].Liq_Y["Na+"] *
                 exp(-model.params.Liq.alpha["H2O", "Na+, Cl-"] *
                     model.params.Liq.tau["H2O", "Na+, Cl-"]) +
                 model.state[1].Liq_Y["H+"] *
                 exp(-model.params.Liq.alpha["H2O", "H+, Cl-"] *
                     model.params.Liq.tau["H2O", "H+, Cl-"])))
        assert (model.state[1].Liq_G["OH-", "H2O"].expr ==
                (model.state[1].Liq_Y["Na+"] *
                 exp(-model.params.Liq.alpha["H2O", "Na+, OH-"] *
                     model.params.Liq.tau["H2O", "Na+, OH-"]) +
                 model.state[1].Liq_Y["H+"] *
                 exp(-model.params.Liq.alpha["H2O", "H+, OH-"] *
                     model.params.Liq.tau["H2O", "H+, OH-"])))

        assert (model.state[1].Liq_G["C6H12", "Na+"].expr ==
                (model.state[1].Liq_Y["Cl-"] *
                 exp(-model.params.Liq.alpha["C6H12", "Na+, Cl-"] *
                     model.params.Liq.tau["C6H12", "Na+, Cl-"]) +
                 model.state[1].Liq_Y["OH-"] *
                 exp(-model.params.Liq.alpha["C6H12", "Na+, OH-"] *
                     model.params.Liq.tau["C6H12", "Na+, OH-"])))
        assert (model.state[1].Liq_G["C6H12", "H+"].expr ==
                (model.state[1].Liq_Y["Cl-"] *
                 exp(-model.params.Liq.alpha["C6H12", "H+, Cl-"] *
                     model.params.Liq.tau["C6H12", "H+, Cl-"]) +
                 model.state[1].Liq_Y["OH-"] *
                 exp(-model.params.Liq.alpha["H2O", "C6H12"] *
                     model.params.Liq.tau["H2O", "C6H12"])))
        assert (model.state[1].Liq_G["Na+", "C6H12"].expr ==
                (model.state[1].Liq_Y["Cl-"] *
                 exp(-model.params.Liq.alpha["C6H12", "Na+, Cl-"] *
                     model.params.Liq.tau["C6H12", "Na+, Cl-"]) +
                 model.state[1].Liq_Y["OH-"] *
                 exp(-model.params.Liq.alpha["C6H12", "Na+, OH-"] *
                     model.params.Liq.tau["C6H12", "Na+, OH-"])))
        assert (model.state[1].Liq_G["H+", "C6H12"].expr ==
                (model.state[1].Liq_Y["Cl-"] *
                 exp(-model.params.Liq.alpha["C6H12", "H+, Cl-"] *
                     model.params.Liq.tau["C6H12", "H+, Cl-"]) +
                 model.state[1].Liq_Y["OH-"] *
                 exp(-model.params.Liq.alpha["H2O", "C6H12"] *
                     model.params.Liq.tau["H2O", "C6H12"])))
        assert (model.state[1].Liq_G["C6H12", "Cl-"].expr ==
                (model.state[1].Liq_Y["Na+"] *
                 exp(-model.params.Liq.alpha["C6H12", "Na+, Cl-"] *
                     model.params.Liq.tau["C6H12", "Na+, Cl-"]) +
                 model.state[1].Liq_Y["H+"] *
                 exp(-model.params.Liq.alpha["C6H12", "H+, Cl-"] *
                     model.params.Liq.tau["C6H12", "H+, Cl-"])))
        assert (model.state[1].Liq_G["C6H12", "OH-"].expr ==
                (model.state[1].Liq_Y["Na+"] *
                 exp(-model.params.Liq.alpha["C6H12", "Na+, OH-"] *
                     model.params.Liq.tau["C6H12", "Na+, OH-"]) +
                 model.state[1].Liq_Y["H+"] *
                 exp(-model.params.Liq.alpha["H2O", "C6H12"] *
                     model.params.Liq.tau["H2O", "C6H12"])))
        assert (model.state[1].Liq_G["Cl-", "C6H12"].expr ==
                (model.state[1].Liq_Y["Na+"] *
                 exp(-model.params.Liq.alpha["C6H12", "Na+, Cl-"] *
                     model.params.Liq.tau["C6H12", "Na+, Cl-"]) +
                 model.state[1].Liq_Y["H+"] *
                 exp(-model.params.Liq.alpha["C6H12", "H+, Cl-"] *
                     model.params.Liq.tau["C6H12", "H+, Cl-"])))
        assert (model.state[1].Liq_G["OH-", "C6H12"].expr ==
                (model.state[1].Liq_Y["Na+"] *
                 exp(-model.params.Liq.alpha["C6H12", "Na+, OH-"] *
                     model.params.Liq.tau["C6H12", "Na+, OH-"]) +
                 model.state[1].Liq_Y["H+"] *
                 exp(-model.params.Liq.alpha["H2O", "C6H12"] *
                     model.params.Liq.tau["H2O", "C6H12"])))

        # Ion-ion interactions
        assert (model.state[1].Liq_G["Na+", "Cl-"].expr ==
                (model.state[1].Liq_Y["H+"] *
                 exp(-model.params.Liq.alpha["Na+, Cl-", "H+, Cl-"] *
                     model.params.Liq.tau["Na+, Cl-", "H+, Cl-"])))
        assert (model.state[1].Liq_G["Na+", "OH-"].expr ==
                (model.state[1].Liq_Y["H+"] *
                 exp(-model.params.Liq.alpha["Na+, OH-", "H+, OH-"] *
                     model.params.Liq.tau["Na+, OH-", "H+, OH-"])))
        assert (model.state[1].Liq_G["H+", "Cl-"].expr ==
                (model.state[1].Liq_Y["Na+"] *
                 exp(-model.params.Liq.alpha["Na+, Cl-", "H+, Cl-"] *
                     model.params.Liq.tau["Na+, Cl-", "H+, Cl-"])))
        assert (model.state[1].Liq_G["H+", "OH-"].expr ==
                (model.state[1].Liq_Y["Na+"] *
                 exp(-model.params.Liq.alpha["Na+, OH-", "H+, OH-"] *
                     model.params.Liq.tau["Na+, OH-", "H+, OH-"])))
        assert (model.state[1].Liq_G["Cl-", "Na+"].expr ==
                (model.state[1].Liq_Y["OH-"] *
                 exp(-model.params.Liq.alpha["Na+, Cl-", "Na+, OH-"] *
                     model.params.Liq.tau["Na+, Cl-", "Na+, OH-"])))
        assert (model.state[1].Liq_G["Cl-", "H+"].expr ==
                (model.state[1].Liq_Y["OH-"] *
                 exp(-model.params.Liq.alpha["H+, Cl-", "H+, OH-"] *
                     model.params.Liq.tau["H+, Cl-", "H+, OH-"])))
        assert (model.state[1].Liq_G["OH-", "Na+"].expr ==
                (model.state[1].Liq_Y["Cl-"] *
                 exp(-model.params.Liq.alpha["Na+, Cl-", "Na+, OH-"] *
                     model.params.Liq.tau["Na+, Cl-", "Na+, OH-"])))
        assert (model.state[1].Liq_G["OH-", "H+"].expr ==
                (model.state[1].Liq_Y["Cl-"] *
                 exp(-model.params.Liq.alpha["H+, Cl-", "H+, OH-"] *
                     model.params.Liq.tau["H+, Cl-", "H+, OH-"])))

        # Like species interactions
        assert ("H2O", "H2O") not in model.state[1].Liq_G
        assert ("C6H12", "C6H12") not in model.state[1].Liq_G
        assert ("Na+", "Na+") not in model.state[1].Liq_G
        assert ("Na+", "H+") not in model.state[1].Liq_G
        assert ("H+", "Na+") not in model.state[1].Liq_G
        assert ("H+", "H+") not in model.state[1].Liq_G
        assert ("Cl-", "Cl-") not in model.state[1].Liq_G
        assert ("Cl-", "OH-") not in model.state[1].Liq_G
        assert ("OH-", "Cl-") not in model.state[1].Liq_G
        assert ("OH-", "OH-") not in model.state[1].Liq_G

    @pytest.mark.unit
    def test_tau(self, model):
        assert isinstance(model.state[1].Liq_tau, Expression)
        assert len(model.state[1].Liq_tau) == 26

        # Molecule-molecule interactions
        assert (model.state[1].Liq_tau["H2O", "C6H12"].expr ==
                model.params.Liq.tau["H2O", "C6H12"])
        assert (model.state[1].Liq_tau["C6H12", "H2O"].expr ==
                model.params.Liq.tau["H2O", "C6H12"])

        for i, j in model.state[1].Liq_tau:
            if (i, j) not in [("H2O", "H2O"), ("H2O", "C6H12"),
                              ("C6H12", "H2O"), ("C6H12", "C6H12")]:
                assert (model.state[1].Liq_tau[i, j].expr ==
                        -log(model.state[1].Liq_G[i, j]) /
                        model.state[1].Liq_alpha[i, j])

        # Like species interactions
        assert ("H2O", "H2O") not in model.state[1].Liq_tau
        assert ("C6H12", "C6H12") not in model.state[1].Liq_tau
        assert ("Na+", "Na+") not in model.state[1].Liq_tau
        assert ("Na+", "H+") not in model.state[1].Liq_tau
        assert ("H+", "Na+") not in model.state[1].Liq_tau
        assert ("H+", "H+") not in model.state[1].Liq_tau
        assert ("Cl-", "Cl-") not in model.state[1].Liq_tau
        assert ("Cl-", "OH-") not in model.state[1].Liq_tau
        assert ("OH-", "Cl-") not in model.state[1].Liq_tau
        assert ("OH-", "OH-") not in model.state[1].Liq_tau
