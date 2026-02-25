"""
Module that contains the command line app.
"""

import json
import os

import click

from .api import GeneratorClient
from .models import FullGeneratorModel


@click.group()
@click.option("--url", default="https://generator.campaign-logger.com", help="API Base URL")
@click.option("--token", envvar="CL_GENERATOR_TOKEN", help="Bearer Token")
@click.option("--client-id", envvar="CL_GENERATOR_CLIENT_ID", help="Client ID for API Key auth")
@click.option("--client-secret", envvar="CL_GENERATOR_CLIENT_SECRET", help="Client Secret for API Key auth")
@click.pass_context
def main(ctx, url, token, client_id, client_secret):
    ctx.ensure_object(dict)
    ctx.obj["client"] = GeneratorClient(base_url=url, token=token, client_id=client_id, client_secret=client_secret)


@main.command(name="list")
@click.pass_context
def list_generators(ctx):
    """List all generators."""
    client = ctx.obj["client"]
    try:
        generators = client.list_generators()
        for g in generators:
            click.echo(f"{g.id}: {g.name}")
    except Exception as e:
        click.echo(f"Error: {e}", err=True)


@main.command(name="get")
@click.argument("id")
@click.pass_context
def get_generator(ctx, id):
    """Get a generator by ID."""
    client = ctx.obj["client"]
    try:
        generator = client.get_generator(id)
        click.echo(generator.model_dump_json(indent=2))
    except Exception as e:
        click.echo(f"Error: {e}", err=True)


@main.command(name="create")
@click.argument("json_file", type=click.File("r"))
@click.pass_context
def create_generator(ctx, json_file):
    """Create a new generator from a JSON file."""
    client = ctx.obj["client"]
    try:
        data = json.load(json_file)
        model = FullGeneratorModel(**data)
        created = client.create_generator(model)
        click.echo(created.model_dump_json(indent=2))
    except Exception as e:
        click.echo(f"Error: {e}", err=True)


@main.command(name="update")
@click.argument("id")
@click.argument("json_file", type=click.File("r"))
@click.pass_context
def update_generator(ctx, id, json_file):
    """Update an existing generator from a JSON file."""
    client = ctx.obj["client"]
    try:
        data = json.load(json_file)
        model = FullGeneratorModel(**data)
        updated = client.update_generator(id, model)
        click.echo(updated.model_dump_json(indent=2))
    except Exception as e:
        click.echo(f"Error: {e}", err=True)


@main.command(name="delete")
@click.argument("id")
@click.pass_context
def delete_generator(ctx, id):
    """Delete a generator."""
    client = ctx.obj["client"]
    try:
        client.delete_generator(id)
        click.echo(f"Generator {id} deleted.")
    except Exception as e:
        click.echo(f"Error: {e}", err=True)


@main.command(name="generate")
@click.argument("target")
@click.pass_context
def generate(ctx, target):
    """Generate result from a generator ID or JSON file."""
    client = ctx.obj["client"]
    try:
        if os.path.isfile(target):
            with open(target, "r") as f:
                data = json.load(f)
            model = FullGeneratorModel(**data)
            result = client.generate_random(model)
        else:
            result = client.execute_operation(target, "generate")

        click.echo(json.dumps(result, indent=2))
    except Exception as e:
        click.echo(f"Error: {e}", err=True)


@main.command(name="validate")
@click.argument("target")
@click.pass_context
def validate(ctx, target):
    """Validate a generator ID or JSON file."""
    client = ctx.obj["client"]
    try:
        if os.path.isfile(target):
            with open(target, "r") as f:
                data = json.load(f)
            model = FullGeneratorModel(**data)
            client.validate_generator(model)
            click.echo("Generator is valid.")
        else:
            # Assuming validating by ID uses the same execute_operation endpoint
            client.execute_operation(target, "validate")
            click.echo(f"Generator {target} is valid.")
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
