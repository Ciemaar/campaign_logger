"""Module that contains the command line app."""

import json
import os

import click

from .api import GeneratorClient
from .api import LoggerClient
from .models import GeneratorModel


@click.group()
@click.pass_context
def main(ctx):
    """Campaign Logger command line interface."""
    ctx.ensure_object(dict)


@main.group()
@click.option("--url", default="https://generator.campaign-logger.com", help="API Base URL")
@click.option("--token", envvar="CL_GENERATOR_TOKEN", help="Bearer Token")
@click.pass_context
def generator(ctx, url, token):
    """Generator API commands."""
    ctx.obj["client"] = GeneratorClient(base_url=url, token=token)


@generator.command(name="list")
@click.pass_context
def list_generators(ctx):
    """Retrieve and display a list of all user generators."""
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
    """Fetch the configuration of a specific generator by its ID."""
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
    """Create and save a new generator using a provided JSON file."""
    client = ctx.obj["client"]
    try:
        data = json.load(json_file)
        model = GeneratorModel(**data)
        created = client.create_generator(model)
        click.echo(created.model_dump_json(indent=2))
    except Exception as e:
        click.echo(f"Error: {e}", err=True)


@generator.command(name="update")
@click.argument("generator_id")
@click.argument("json_file", type=click.File("r"))
@click.pass_context
def update_generator(ctx, generator_id, json_file):
    """Overwrite an existing generator's configuration with a JSON file."""
    client = ctx.obj["client"]
    try:
        data = json.load(json_file)
        model = GeneratorModel(**data)
        updated = client.update_generator(generator_id, model)
        click.echo(updated.model_dump_json(indent=2))
    except Exception as e:
        click.echo(f"Error: {e}", err=True)


@generator.command(name="delete")
@click.argument("generator_id")
@click.pass_context
def delete_generator(ctx, generator_id):
    """Permanently delete a generator by its ID."""
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
    """Generate a random outcome from a generator ID or local JSON file."""
    client = ctx.obj["client"]
    try:
        if os.path.isfile(target):
            with open(target, "r") as f:
                data = json.load(f)
            model = GeneratorModel(**data)
            result = client.generate(model)
        else:
            result = client.execute_operation(target, "generate")

        click.echo(json.dumps(result, indent=2))
    except Exception as e:
        click.echo(f"Error: {e}", err=True)


@generator.command(name="validate")
@click.argument("target")
@click.pass_context
def validate(ctx, target):
    """Validate the syntax of a generator ID or local JSON file."""
    client = ctx.obj["client"]
    try:
        if os.path.isfile(target):
            with open(target, "r") as f:
                data = json.load(f)
            model = GeneratorModel(**data)
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
@click.option("--client-id", envvar="CL_LOGGER_CLIENT_ID", help="API Client ID")
@click.option("--client-secret", envvar="CL_LOGGER_CLIENT_SECRET", help="API Client Secret")
@click.pass_context
def logger(ctx, url, client_id, client_secret):
    """Main Campaign Logger API commands."""
    ctx.obj["client"] = LoggerClient(base_url=url, client_id=client_id, client_secret=client_secret)


# --- Campaign Commands ---
@logger.group()
def campaign():
    """Manage campaigns."""


@campaign.command(name="list")
@click.pass_context
def list_campaigns(ctx):
    """Retrieve and print all user campaigns in JSON format."""
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
    """Fetch and print a specific campaign by its ID."""
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
    """Create a new top-level campaign with an optional description."""
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
    """Modify the metadata attributes (title/description) of a campaign."""
    client = ctx.obj["client"]
    try:
        camp = client.get_campaign(campaign_id)
        if title is not None:
            camp.title = title
        if description is not None:
            camp.description = description
        click.echo(json.dumps(camp.save().to_dict(), indent=2))
    except Exception as e:
        click.echo(f"Error: {e}", err=True)


@campaign.command(name="delete")
@click.argument("campaign_id")
@click.pass_context
def delete_campaign(ctx, campaign_id):
    """Permanently delete a campaign by its ID."""
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
    """Retrieve and print all logs across all campaigns."""
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
    """Fetch and print a specific log by its ID."""
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
    """Create a new log attached to a specific campaign."""
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
    """Modify the metadata attributes (title/description) of a log."""
    client = ctx.obj["client"]
    try:
        log_obj = client.get_log(log_id)
        if title is not None:
            log_obj.title = title
        if description is not None:
            log_obj.description = description
        click.echo(json.dumps(log_obj.save().to_dict(), indent=2))
    except Exception as e:
        click.echo(f"Error: {e}", err=True)


@log.command(name="delete")
@click.argument("log_id")
@click.pass_context
def delete_log(ctx, log_id):
    """Permanently delete a log and its contents."""
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
    """Retrieve and print all log entries across all logs."""
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
    """Fetch and print a specific log entry by its ID."""
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
    """Append a new text entry to a specific log."""
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
    """Modify the text content of a specific log entry."""
    client = ctx.obj["client"]
    try:
        entry_obj = client.get_log_entry(entry_id)
        entry_obj.raw_text = text
        click.echo(json.dumps(entry_obj.save().to_dict(), indent=2))
    except Exception as e:
        click.echo(f"Error: {e}", err=True)


@entry.command(name="delete")
@click.argument("entry_id")
@click.pass_context
def delete_entry(ctx, entry_id):
    """Permanently delete a log entry."""
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
    """Retrieve and print all top-level campaign pages."""
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
    """Fetch and print a specific campaign page by its ID."""
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
    """Create a new top-level page attached to a specific campaign."""
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
    """Modify the text content of a specific campaign page."""
    client = ctx.obj["client"]
    try:
        page_obj = client.get_campaign_entry(page_id)
        page_obj.raw_text = text
        click.echo(json.dumps(page_obj.save().to_dict(), indent=2))
    except Exception as e:
        click.echo(f"Error: {e}", err=True)


@page.command(name="delete")
@click.argument("page_id")
@click.pass_context
def delete_page(ctx, page_id):
    """Permanently delete a campaign page."""
    client = ctx.obj["client"]
    try:
        client.delete_campaign_entry(page_id)
        click.echo(f"Page {page_id} deleted.")
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
