import importlib
from typing import List

import click
from colorama import init, Fore, Style
from tabulate import tabulate
from pyfused.core.network import WorkflowNotFoundException
from pyfused.core.parser import PyFusedConfig, get_pyfused_config


@click.group()
def cli():
    init(autoreset=True)


@cli.command(context_settings=dict(ignore_unknown_options=False, allow_extra_args=False))
@click.pass_context
def ls(ctx):
    """Show all workflows defined in a project."""
    pyfused_config: PyFusedConfig = get_pyfused_config()

    # Prepare data for tabulation
    headers = [Fore.GREEN + Style.BRIGHT + "Workflow Name" + Style.RESET_ALL, 
               Fore.GREEN + Style.BRIGHT + "Input Shape" + Style.RESET_ALL,
               Fore.GREEN + Style.BRIGHT + "Outputs" + Style.RESET_ALL]
    
    table_data: List[List[str]] = []
    
    for workflow in pyfused_config.workflows:
        workflow = workflow.build()
        workflow_name = Fore.CYAN + workflow.name + Style.RESET_ALL
        input_shape = "\n".join([ 
            f"{input_name}[{input_type}]"
            for input_name, input_type in workflow.input_shape.items()
        ])

        outputs = "\n".join([
            f"{output.name}[{output.annotation}]"
            for output in workflow.outputs
        ])
        #outputs = Fore.YELLOW + outputs + Style.RESET_ALL
        table_data.append([workflow_name, input_shape, outputs])
    
    # Create and print the table
    table = tabulate(table_data, headers=headers, tablefmt="grid")
    
    #click.echo("\n" + Fore.MAGENTA + Style.BRIGHT + "Workflows defined in the project:" + Style.RESET_ALL)
    click.echo(table)
    
    # Print additional config info if needed
    click.echo(f"\n{Fore.BLUE}Engine: {Fore.WHITE}{pyfused_config.config.engine}{Style.RESET_ALL}")



@cli.command(context_settings=dict(ignore_unknown_options=True, allow_extra_args=True))
@click.argument('workflow_name')
@click.pass_context
def run(ctx, workflow_name: str):
    """Run a specified workflow with given parameters."""
    pyfused_config: PyFusedConfig = get_pyfused_config()
    try:
        workflow = pyfused_config[workflow_name]
    except WorkflowNotFoundException:
        color = Fore.RED
        status = f"{color}ERROR!{Style.RESET_ALL}"

        click.echo(f"{status} Workflow `{workflow_name}` not found.")
        return

    # Parse arguments
    params = {}
    for i in range(0, len(ctx.args), 2):
        key = ctx.args[i].lstrip('--')
        value = ctx.args[i+1] if i+1 < len(ctx.args) else None
        if value is not None:
            try:
                # Try to convert to int or float if possible
                params[key] = int(value)
            except ValueError:
                try:
                    params[key] = float(value)
                except ValueError:
                    params[key] = value

    try:
        result_net = workflow.run(**params)
        click.echo(result_net.print_outputs())
    except Exception as e:
        color = Fore.RED
        status = f"{color}ERROR!{Style.RESET_ALL}"

        click.echo(f"{status} {workflow_name}: {e!s}")

if __name__ == '__main__':
    cli()
