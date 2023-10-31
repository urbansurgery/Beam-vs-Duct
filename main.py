"""This module contains the business logic of the function.

use the automation_context module to wrap your function in an Automate context helper
"""
from typing import List

from pydantic import Field
import multiprocessing
from speckle_automate import (
    AutomateBase,
    AutomationContext,
    execute_automate_function,
)
from specklepy.objects import Base
from specklepy.objects.units import Units
from specklepy.api.models import Branch
from specklepy.api import operations
from specklepy.transports.server import ServerTransport

class FunctionInputs(AutomateBase):
    """These are function author defined values.

    Automate will make sure to supply them matching the types specified here.
    Please use the pydantic model schema to define your inputs:
    https://docs.pydantic.dev/latest/usage/models/
    """

    tolerance: float = Field(
        default=25.0,
        title="Tolerance",
        description="Specify the tolerance value for the analysis.",
        ge=0.0,  # Greater than or equal to 0.0
    )
    tolerance_unit: Units = Field(  # Using the SpecklePy Units enum here
        default=Units.mm,
        title="Tolerance Unit",
        description="Unit of the tolerance value.",
    )
    static_model_name: str = Field(
        ...,
        title="Static Model Name",
        description="Name of the static structural model.",
    )


def clash_objects(left:List[Base], right:List[Base], tolerance:float, tolerance_unit:Units = "mm"):
    pass


def automate_function(
    automate_context: AutomationContext,
    function_inputs: FunctionInputs,
) -> None:
    """This is an example Speckle Automate function.

    Args:
        automate_context: A context helper object, that carries relevant information
            about the runtime context of this function.
            It gives access to the Speckle project data, that triggered this run.
            It also has convenience methods attach result data to the Speckle model.
        function_inputs: An instance object matching the defined schema.
    """
    # the context provides a convenient way, to receive the triggering version
    changed_model_version = automate_context.receive_version()

    # the static reference model will be retrieved from the project using model name stored in the inputs
    speckle_client = automate_context.speckle_client
    project_id = automate_context.automation_run_data.project_id
    static_model_name = function_inputs.static_model_name
    remote_transport = ServerTransport(
        automate_context.automation_run_data.project_id, speckle_client
    )

    model: Branch = speckle_client.branch.get(
        project_id, static_model_name, commits_limit=1
    )  # get the latest commit of the static model

    if not model:
        automate_context.mark_run_failed(
            status_message="The static model does not exist, skipping the function."
        )

    latest_reference_model_id = model.commits[0].referencedObject

    if latest_reference_model_id == automate_context.automation_run_data.model_id:
        automate_context.mark_run_failed(
            status_message="The static model is the same as the changed model, skipping the function."
        )
        return

    latest_reference_model_version = operations.receive(
        latest_reference_model_id,
        remote_transport,
    )  # receive the static model

    # Create a Pool of processes
    with multiprocessing.Pool(processes=2) as pool:
        # Use `pool.map()` to distribute the models to the processes
        results = pool.map(
            get_displayable_objects,
            [latest_reference_model_version, changed_model_version],
        )

    # Results will be a list of displayable objects for each model
    static_displayable_objects, latest_displayable_objects = results

    clash_objects(
        left=static_displayable_objects,
        right=latest_displayable_objects,
        tolerance=function_inputs.tolerance,
        tolerance_unit=function_inputs.tolerance_unit,
    )

    automate_context.mark_run_success(status_message="Clash detection completed.")


def get_displayable_objects() -> List[Base]:
    return []


# make sure to call the function with the executor
if __name__ == "__main__":
    # NOTE: always pass in the automate function by its reference, do not invoke it!

    # pass in the function reference with the inputs schema to the executor
    execute_automate_function(automate_function, FunctionInputs)

    # if the function has no arguments, the executor can handle it like so
    # execute_automate_function(automate_function_without_inputs)
