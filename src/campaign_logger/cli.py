"""Module that contains the command line app."""

import json
import os

import click

from .api import GeneratorClient
from .api import LoggerClient
from .models import FullGeneratorModel


@click.group()
@click.pass_context
def main(ctx):
    """Campaign Logger command line interface."""
    ctx.ensure_object(dict)


@main.group()
@click.option("--url", default="https://generator.campaign-logger.com", help="API Base URL")
@click.option("--token", envvar="CL_GENERATOR_TOKEN", help="Bearer Token")
@click.option("--client-id", envvar="CL_GENERATOR_CLIENT_ID", help="Client ID for API Key auth")
@click.option("--client-secret", envvar="CL_GENERATOR_CLIENT_SECRET", help="Client Secret for API Key auth")
@click.pass_context
def generator(ctx, url, token, client_id, client_secret):
    """Generator API commands."""
    ctx.obj["client"] = GeneratorClient(base_url=url, token=token, client_id=client_id, client_secret=client_secret)


@generator.command(name="list")
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


@generator.command(name="get")
@click.argument("generator_id")
@click.pass_context
def get_generator(ctx, generator_id):
    """Get a generator by ID."""
    client = ctx.obj["client"]
    try:
        generator_obj = client.get_generator(generator_id)
        click.echo(generator_obj.model_dump_json(indent=2))
    except Exception as e:
        click.echo(f"Error: {e}", err=True)


@generator.command(name="create")
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


@generator.command(name="update")
@click.argument("generator_id")
@click.argument("json_file", type=click.File("r"))
@click.pass_context
def update_generator(ctx, generator_id, json_file):
    """Update an existing generator from a JSON file."""
    client = ctx.obj["client"]
    try:
        data = json.load(json_file)
        model = FullGeneratorModel(**data)
        updated = client.update_generator(generator_id, model)
        click.echo(updated.model_dump_json(indent=2))
    except Exception as e:
        click.echo(f"Error: {e}", err=True)


@generator.command(name="delete")
@click.argument("generator_id")
@click.pass_context
def delete_generator(ctx, generator_id):
    """Delete a generator."""
    client = ctx.obj["client"]
    try:
        client.delete_generator(generator_id)
        click.echo(f"Generator {generator_id} deleted.")
    except Exception as e:
        click.echo(f"Error: {e}", err=True)


@generator.command(name="generate")
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


@generator.command(name="validate")
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


@main.group()
@click.option("--url", default="https://logger.campaign-logger.com", help="API Base URL")
@click.option("--token", envvar="CL_LOGGER_TOKEN", help="Bearer Token")
@click.pass_context
def logger(ctx, url, token):
    """Main Campaign Logger API commands."""
    ctx.obj["client"] = LoggerClient(base_url=url, token=token)


# --- Campaign Commands ---
@logger.group()
def campaign():
    """Manage campaigns."""


@campaign.command(name="list")
@click.pass_context
def list_campaigns(ctx):
    """List all campaigns."""
    client = ctx.obj["client"]
    try:
        res = client.get_campaigns()
        click.echo(json.dumps([c.to_dict() for c in res], indent=2))
    except Exception as e:
        click.echo(f"Error: {e}", err=True)


@campaign.command(name="get")
@click.argument("campaign_id")
@click.pass_context
def get_campaign(ctx, campaign_id):
    """Get a campaign by ID."""
    client = ctx.obj["client"]
    try:
        click.echo(json.dumps(client.get_campaign(campaign_id).to_dict(), indent=2))
    except Exception as e:
        click.echo(f"Error: {e}", err=True)


@campaign.command(name="create")
@click.argument("title")
@click.option("--description", default="", help="Description of the campaign")
@click.pass_context
def create_campaign(ctx, title, description):
    """Create a new campaign."""
    client = ctx.obj["client"]
    try:
        click.echo(json.dumps(client.create_campaign(title, description).to_dict(), indent=2))
    except Exception as e:
        click.echo(f"Error: {e}", err=True)


@campaign.command(name="update")
@click.argument("campaign_id")
@click.option("--title", help="New title")
@click.option("--description", help="New description")
@click.pass_context
def update_campaign(ctx, campaign_id, title, description):
    """Update an existing campaign."""
    client = ctx.obj["client"]
    try:
        click.echo(json.dumps(client.update_campaign(campaign_id, title, description).to_dict(), indent=2))
    except Exception as e:
        click.echo(f"Error: {e}", err=True)


@campaign.command(name="delete")
@click.argument("campaign_id")
@click.pass_context
def delete_campaign(ctx, campaign_id):
    """Delete a campaign."""
    client = ctx.obj["client"]
    try:
        client.delete_campaign(campaign_id)
        click.echo(f"Campaign {campaign_id} deleted.")
    except Exception as e:
        click.echo(f"Error: {e}", err=True)


# --- Log Commands ---
@logger.group()
def log():
    """Manage logs."""


@log.command(name="list")
@click.pass_context
def list_logs(ctx):
    """List all logs."""
    client = ctx.obj["client"]
    try:
        res = client.get_logs()
        click.echo(json.dumps([log_obj.to_dict() for log_obj in res], indent=2))
    except Exception as e:
        click.echo(f"Error: {e}", err=True)


@log.command(name="get")
@click.argument("log_id")
@click.pass_context
def get_log(ctx, log_id):
    """Get a log by ID."""
    client = ctx.obj["client"]
    try:
        click.echo(json.dumps(client.get_log(log_id).to_dict(), indent=2))
    except Exception as e:
        click.echo(f"Error: {e}", err=True)


@log.command(name="create")
@click.argument("campaign_id")
@click.argument("title")
@click.option("--description", default="", help="Description of the log")
@click.pass_context
def create_log(ctx, campaign_id, title, description):
    """Create a new log."""
    client = ctx.obj["client"]
    try:
        click.echo(json.dumps(client.create_log(campaign_id, title, description).to_dict(), indent=2))
    except Exception as e:
        click.echo(f"Error: {e}", err=True)


@log.command(name="update")
@click.argument("log_id")
@click.option("--title", help="New title")
@click.option("--description", help="New description")
@click.pass_context
def update_log(ctx, log_id, title, description):
    """Update an existing log."""
    client = ctx.obj["client"]
    try:
        click.echo(json.dumps(client.update_log(log_id, title, description).to_dict(), indent=2))
    except Exception as e:
        click.echo(f"Error: {e}", err=True)


@log.command(name="delete")
@click.argument("log_id")
@click.pass_context
def delete_log(ctx, log_id):
    """Delete a log."""
    client = ctx.obj["client"]
    try:
        client.delete_log(log_id)
        click.echo(f"Log {log_id} deleted.")
    except Exception as e:
        click.echo(f"Error: {e}", err=True)


# --- Entry Commands ---
@logger.group()
def entry():
    """Manage log entries."""


@entry.command(name="list")
@click.pass_context
def list_entries(ctx):
    """List all log entries."""
    client = ctx.obj["client"]
    try:
        res = client.get_log_entries()
        click.echo(json.dumps([e.to_dict() for e in res], indent=2))
    except Exception as e:
        click.echo(f"Error: {e}", err=True)


@entry.command(name="get")
@click.argument("entry_id")
@click.pass_context
def get_entry(ctx, entry_id):
    """Get a log entry by ID."""
    client = ctx.obj["client"]
    try:
        click.echo(json.dumps(client.get_log_entry(entry_id).to_dict(), indent=2))
    except Exception as e:
        click.echo(f"Error: {e}", err=True)


@entry.command(name="create")
@click.argument("log_id")
@click.argument("text")
@click.pass_context
def create_entry(ctx, log_id, text):
    """Create a new log entry."""
    client = ctx.obj["client"]
    try:
        click.echo(json.dumps(client.create_log_entry(log_id, text).to_dict(), indent=2))
    except Exception as e:
        click.echo(f"Error: {e}", err=True)


@entry.command(name="update")
@click.argument("entry_id")
@click.argument("text")
@click.pass_context
def update_entry(ctx, entry_id, text):
    """Update an existing log entry."""
    client = ctx.obj["client"]
    try:
        click.echo(json.dumps(client.update_log_entry(entry_id, text).to_dict(), indent=2))
    except Exception as e:
        click.echo(f"Error: {e}", err=True)


@entry.command(name="delete")
@click.argument("entry_id")
@click.pass_context
def delete_entry(ctx, entry_id):
    """Delete a log entry."""
    client = ctx.obj["client"]
    try:
        client.delete_log_entry(entry_id)
        click.echo(f"Entry {entry_id} deleted.")
    except Exception as e:
        click.echo(f"Error: {e}", err=True)


# --- Page Commands ---
@logger.group()
def page():
    """Manage pages (campaign entries)."""


@page.command(name="list")
@click.pass_context
def list_pages(ctx):
    """List all pages."""
    client = ctx.obj["client"]
    try:
        res = client.get_campaign_entries()
        click.echo(json.dumps([p.to_dict() for p in res], indent=2))
    except Exception as e:
        click.echo(f"Error: {e}", err=True)


@page.command(name="get")
@click.argument("page_id")
@click.pass_context
def get_page(ctx, page_id):
    """Get a page by ID."""
    client = ctx.obj["client"]
    try:
        click.echo(json.dumps(client.get_campaign_entry(page_id).to_dict(), indent=2))
    except Exception as e:
        click.echo(f"Error: {e}", err=True)


@page.command(name="create")
@click.argument("campaign_id")
@click.argument("text")
@click.pass_context
def create_page(ctx, campaign_id, text):
    """Create a new page."""
    client = ctx.obj["client"]
    try:
        click.echo(json.dumps(client.create_campaign_entry(campaign_id, text).to_dict(), indent=2))
    except Exception as e:
        click.echo(f"Error: {e}", err=True)


@page.command(name="update")
@click.argument("page_id")
@click.argument("text")
@click.pass_context
def update_page(ctx, page_id, text):
    """Update an existing page."""
    client = ctx.obj["client"]
    try:
        click.echo(json.dumps(client.update_campaign_entry(page_id, text).to_dict(), indent=2))
    except Exception as e:
        click.echo(f"Error: {e}", err=True)


@page.command(name="delete")
@click.argument("page_id")
@click.pass_context
def delete_page(ctx, page_id):
    """Delete a page."""
    client = ctx.obj["client"]
    try:
        client.delete_campaign_entry(page_id)
        click.echo(f"Page {page_id} deleted.")
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
